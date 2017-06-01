from lily.search.base_mapping import BaseMapping

from .models import TimeLog


class TimeLogMapping(BaseMapping):
    @classmethod
    def get_model(cls):
        return TimeLog

    @classmethod
    def get_mapping(cls):
        """
        Returns an Elasticsearch mapping for this MappingType.
        """

        mapping = super(TimeLogMapping, cls).get_mapping()
        mapping['properties'].update({
            'date': {
                'type': 'date',
            },
            'gfk_content_type': {
                'type': 'string',
                'index_analyzer': 'keyword',
            },
            'gfk_object_id': {
                'type': 'integer',
            },
            'hours_logged': {
                'type': 'float',
            },
            'user': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'integer'},
                    'full_name': {
                        'type': 'string',
                        'analyzer': 'normal_edge_analyzer',
                    },
                },
            },
        })
        return mapping

    @classmethod
    def get_related_models(cls):
        """
        Maps related models, how to get an instance list from a signal sender.
        """
        return {
        }

    @classmethod
    def prepare_batch(cls, queryset):
        """
        Optimize a queryset for batch indexing.
        """
        return queryset

    @classmethod
    def obj_to_doc(cls, obj):
        """
        Translate an object to an index document.
        """
        return {
            'date': obj.date,
            'gfk_content_type': obj.gfk_content_type.name,
            'gfk_object_id': obj.gfk_object_id,
            'hours_logged': obj.hours_logged,
            'user': {
                'full_name': obj.user.full_name,
                'id': obj.user.id,
            },
        }
