from elasticsearch_dsl.query import MultiMatch
from rest_framework.filters import SearchFilter
from rest_framework.settings import api_settings


class ElasticSearchFilter(SearchFilter):
    ordering_param = api_settings.ORDERING_PARAM

    def filter_queryset(self, request, queryset, view):
        if not hasattr(queryset, 'elasticsearch_query'):
            raise AttributeError('ElasticSearchFilter can only be used with an ElasticQuerySet.')

        search_fields = getattr(view, 'search_fields', None)
        search_term = request.query_params.get(self.search_param, '')

        if not search_fields or not search_term:
            return queryset

        if request.GET.get(self.ordering_param, None):
            raise AttributeError('ElasticSearchFilter orders on relevancy and cannot be used with custom ordering.')

        fields = [field.replace('__', '.') for field in search_fields]
        return queryset.elasticsearch_query(MultiMatch(query=search_term, fields=fields))
