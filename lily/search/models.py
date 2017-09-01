from django.db import models
from django.db.models.query_utils import Q
from elasticsearch_dsl import Search
import six

from lily.search.registries import registry
from lily.tenant.middleware import get_current_user


class ElasticQuerySet(models.QuerySet):

    def __init__(self, model=None, query=None, using=None, hints=None, search=None):
        super(ElasticQuerySet, self).__init__(model=model, query=query, using=using, hints=hints)
        if search is None:
            doc_types = registry.get_documents([model])

            if len(doc_types) == 0:
                raise AttributeError('Model %s does not have an Elasticsearch mapping.' % model.__class__)

            search = Search(
                index=[doc_type.meta.index for doc_type in doc_types],
                doc_type=list(doc_types)
            )[0:10000]
        self.search = search
        self._total = None

    def __getitem__(self, k):
        """
        Retrieves an item or slice from the set of results.
        """
        if not isinstance(k, (slice,) + six.integer_types):
            raise TypeError
        assert ((not isinstance(k, slice) and (k >= 0)) or
                (isinstance(k, slice) and (k.start is None or k.start >= 0) and
                 (k.stop is None or k.stop >= 0))), \
            "Negative indexing is not supported."

        if self._result_cache is not None:
            return self._result_cache[k]

        if isinstance(k, slice):
            qs = self._clone()
            if k.start is not None:
                start = int(k.start)
            else:
                start = 0
            if k.stop is not None:
                stop = int(k.stop)
            else:
                stop = start + 10000
            qs.search = qs.search[start, stop]
            return qs

        qs = self._clone()
        qs.search = qs.search[k, k + 1]
        return list(qs)[0]

    def _fetch_all(self):
        if self._result_cache is not None:
            super(ElasticQuerySet, self)._fetch_all()
        else:
            response = self.search.execute(ignore_cache=True)
            self._total = response.hits.total
            ids = [hit.meta.id for hit in response.hits]

            obj = self._clone()
            obj.query.add_q(Q(pk__in=ids))
            models = {obj._get_pk_val(): obj for obj in obj.iterator()}

            sorted_models = []
            for idx in ids:
                sorted_models.append(models[int(idx)])
            self._result_cache = sorted_models

            if self._prefetch_related_lookups and not self._prefetch_done:
                self._prefetch_related_objects()

    def aggregate(self, *args, **kwargs):
        raise NotImplementedError

    def count(self):
        if self._total is None:
            self._fetch_all()

        return self._total

    def get(self, *args, **kwargs):
        raise NotImplementedError

    def _earliest_or_latest(self, field_name=None, direction="-"):
        raise NotImplementedError

    def first(self):
        raise NotImplementedError

    def last(self):
        raise NotImplementedError

    def _filter_or_exclude(self, negate, *args, **kwargs):
        if args or kwargs:
            assert self.query.can_filter(), \
                "Cannot filter a query once a slice has been taken."

        clone = self._clone()

        if len(args) == 0 and len(kwargs) == 0:
            return clone

        clone = self._clone()

        if negate:
            clone.search = clone.search.exclude('term', *args, **kwargs)
        else:
            clone.search = clone.search.filter('term', *args, **kwargs)

        return clone

    def order_by(self, *field_names):
        assert self.query.can_filter(), \
            "Cannot reorder a query once a slice has been taken."
        obj = self._clone()
        obj.search = obj.search.sort()

        fields = list(field_names)
        if 'id' in fields:
            fields.remove('id')

        if len(fields) > 0:
            obj.search = obj.search.sort(*['%s.sortable' % field for field in fields])

        return obj

    def extra(self, select=None, where=None, params=None, tables=None,
              order_by=None, select_params=None):
        raise NotImplementedError()

    def _clone(self, klass=None, setup=False, **kwargs):
        obj = super(ElasticQuerySet, self)._clone(klass=klass, setup=setup, **kwargs)
        obj.search = self.search
        return obj

    def elasticsearch_query(self, *args, **kwargs):
        obj = self._clone()
        obj.search = obj.search.query(*args, **kwargs)
        return obj


class ElasticManager(models.Manager):
    def get_queryset(self):
        return ElasticQuerySet(self.model, using=self._db, hints=self._hints)


class ElasticTenantManager(ElasticManager):
    def get_queryset(self):
        """
        Manipulate the returned queryset by adding a filter for tenant using the tenant linked
        to the current logged in user (received via custom middleware).
        """
        user = get_current_user()
        if user and user.is_authenticated():
            return super(ElasticTenantManager, self).get_queryset().filter(tenant_id=user.tenant_id)
        else:
            return super(ElasticTenantManager, self).get_queryset()
