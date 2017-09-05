from django.http.response import HttpResponse
from django.views.generic.base import View

import anyjson
from lily.messaging.email.models.models import EmailAccount
from lily.utils.functions import parse_phone_number
from lily.utils.views.mixins import LoginRequiredMixin
from lily.search.functions import search_number

from .lily_search import LilySearch


class SearchView(LoginRequiredMixin, View):
    """
    Generic search view suitable for all models that have search enabled.
    """
    def get(self, request):
        """
        Parses the GET parameters to create a search

        Returns:
            HttpResponse with JSON dict:
                hits (list): dicts with search results per item
                total (int): total number of results
                took (int): milliseconds Elastic search took to get the results
        """
        kwargs = {}
        user = self.request.user

        model_type = request.GET.get('type')
        if model_type:
            kwargs['model_type'] = model_type
        sort = request.GET.get('sort')
        if sort:
            kwargs['sort'] = sort
        page = request.GET.get('page')
        if page:
            kwargs['page'] = int(page)
        size = request.GET.get('size')
        if size:
            kwargs['size'] = int(size)

        facet_field = request.GET.get('facet_field', '')
        facet_filters = request.GET.get('facet_filter', '')

        filters = []

        if facet_filters:
            facet_filters = facet_filters.split(',')

            for facet_filter in facet_filters:
                if facet_filter.split(':')[1]:
                    filters.append(facet_filter)

        facet_size = request.GET.get('facet_size', 60)
        if facet_field:
            kwargs['facet'] = {
                'field': facet_field,
                'filters': filters,
                'size': facet_size,
            }

        # Passing arguments as **kwargs means we can use the defaults.
        search = LilySearch(
            tenant_id=request.user.tenant_id,
            **kwargs
        )

        id_arg = request.GET.get('id', '')
        if id_arg:
            search.get_by_id(id_arg)

        query = request.GET.get('q', '').lower()
        if query:
            search.query_common_fields(query)

        account_related = request.GET.get('account_related', '')
        if account_related:
            search.account_related(int(account_related))

        contact_related = request.GET.get('contact_related', '')
        if contact_related:
            search.contact_related(int(contact_related))

        user_email_related = request.GET.get('user_email_related', '')
        if user_email_related:
            search.user_email_related(user)

        filterquery = request.GET.get('filterquery', '')
        if filterquery:
            search.filter_query(filterquery)

        return_fields = filter(None, request.GET.get('fields', '').split(','))
        if '*' in return_fields:
            return_fields = None

        hits, facets, total, took = search.do_search(return_fields)

        if model_type == 'email_emailmessage':
            email_accounts = EmailAccount.objects.filter(tenant=user.tenant, is_deleted=False).distinct('id')

            filtered_hits = []

            for hit in hits:
                try:
                    email_account = email_accounts.get(pk=hit.get('account').get('id'))
                except EmailAccount.DoesNotExist:
                    pass
                else:
                    shared_config = email_account.sharedemailconfig_set.filter(user=user).first()

                    # If the email account or sharing is set to metadata only, just return these fields.
                    metadata_only_message = {
                        'id': hit.get('id'),
                        'sender_name': hit.get('sender_name'),
                        'sender_email': hit.get('sender_email'),
                        'received_by_email': hit.get('received_by_email'),
                        'received_by_name': hit.get('received_by_name'),
                        'received_by_cc_email': hit.get('received_by_cc_email'),
                        'received_by_cc_name': hit.get('received_by_cc_name'),
                        'sent_date': hit.get('sent_date'),
                        'privacy': hit.get('account').get('privacy'),
                    }

                    if email_account.owner == user:
                        filtered_hits.append(hit)
                    else:
                        if shared_config:
                            privacy = shared_config.privacy
                        else:
                            privacy = email_account.privacy

                        metadata_only_message.update({
                            'privacy': privacy,
                        })

                        if privacy == EmailAccount.METADATA:
                            filtered_hits.append(metadata_only_message)
                        elif privacy == EmailAccount.PRIVATE:
                            # Private email (account), so don't add to list.
                            continue
                        else:
                            filtered_hits.append(hit)

            hits = filtered_hits

        results = {'hits': hits, 'total': total, 'took': took}

        if facets:
            results['facets'] = facets

        return HttpResponse(anyjson.dumps(results), content_type='application/json; charset=utf-8')


class PhoneNumberSearchView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        number = kwargs.get('number', None)

        if number:
            # For now we'll always convert the phone number to a certain format.
            # In the future we might change how we handle phone numbers.
            number = parse_phone_number(number)

        response = {
            'data': {
                'accounts': [],
                'contacts': [],
            },
        }

        results = search_number(self.request.user.tenant_id, number)

        # Return only the primary keys of the accounts and contacts
        for account in results['data']['accounts']:
            response['data']['accounts'].append(account.id)

        for contact in results['data']['contacts']:
            response['data']['contacts'].append(contact.id)

        return HttpResponse(anyjson.dumps(response), content_type='application/json; charset=utf-8')
