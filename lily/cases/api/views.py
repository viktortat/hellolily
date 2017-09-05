from django_filters import FilterSet, CharFilter
from django_filters.rest_framework import DjangoFilterBackend, BooleanFilter
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from lily.api.filters import ElasticSearchFilter
from lily.api.mixins import ModelChangesMixin

from .serializers import CaseSerializer, CaseStatusSerializer, CaseTypeSerializer
from ..models import Case, CaseStatus, CaseType


class CaseFilter(FilterSet):
    """
    Class to filter case queryset.
    """
    type = CharFilter(name='type__type')
    status = CharFilter(name='status__status')
    not_type = CharFilter(name='type__type', exclude=True)
    not_status = CharFilter(name='status__status', exclude=True)
    is_archived = BooleanFilter()

    class Meta:
        model = Case
        fields = ['type', 'status', 'not_type', 'not_status', ]


class CaseViewSet(ModelChangesMixin, viewsets.ModelViewSet):
    """
    Returns a list of all **active** cases in the system.

    #Search#
    Searching is enabled on this API.

    To search, provide a field name to search on followed by the value you want to search for to the search parameter.

    #Filtering#
    Filtering is enabled on this API.

    To filter, use the field name as parameter name followed by the value you want to filter on.

    #Ordering#
    Ordering is enabled on this API.

    To order, provide a comma seperated list to the ordering argument. Use `-` minus to inverse the ordering.

    #Examples#
    - plain: `/api/cases/`
    - search: `/api/cases/?search=subject:Doremi`
    - filter: `/api/cases/?type=1`
    - order: `/api/cases/?ordering=subject,-id`

    #Returns#
    * List of cases with related fields
    """
    # Set the queryset, without .all() this filters on the tenant and takes care of setting the `base_name`.
    queryset = Case.elastic_objects
    # Set the serializer class for this viewset.
    serializer_class = CaseSerializer
    # Set all filter backends that this viewset uses.
    filter_backends = (ElasticSearchFilter, OrderingFilter, DjangoFilterBackend)

    # OrderingFilter: set all possible fields to order by.
    ordering_fields = ('created', 'modified', 'priority', 'subject', 'expires')
    # SearchFilter: set the fields that can be searched on.
    search_fields = ('name', 'assigned_to')
    # DjangoFilter: set the filter class.
    filter_class = CaseFilter

    def get_queryset(self):
        """
        Set the queryset here so it filters on tenant and works with pagination.
        """
        return super(CaseViewSet, self).get_queryset().filter(is_deleted=False)


class TeamsCaseList(APIView):
    """
    List all cases assigned to the current users teams.
    """
    model = Case
    serializer_class = CaseSerializer
    filter_class = CaseFilter

    def get_queryset(self):
        return self.model.objects.filter(tenant_id=self.request.user.tenant_id)


class CaseStatusViewSet(viewsets.ModelViewSet):
    # Set the queryset, without .all() this filters on the tenant and takes care of setting the `base_name`.
    queryset = CaseStatus.objects
    # Set the serializer class for this viewset.
    serializer_class = CaseStatusSerializer

    def get_queryset(self):
        """
        Set the queryset here so it filters on tenant and works with pagination.
        """
        return super(CaseStatusViewSet, self).get_queryset().all()


class CaseTypeList(APIView):
    model = CaseType
    serializer_class = CaseTypeSerializer

    def get(self, request, format=None):
        queryset = self.model.objects.filter(tenant_id=self.request.user.tenant_id)
        serializer = CaseTypeSerializer(queryset, many=True)
        return Response(serializer.data)
