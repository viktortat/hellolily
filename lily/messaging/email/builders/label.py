import gc
from django.db import transaction

from ..models.models import EmailLabel


class LabelBuilder(object):
    """
    Builder to create and handle Labels
    """

    def __init__(self, manager):
        self.label = None
        self.manager = manager

    def get_or_create_label(self, label_dict):
        """
        Get or create EmailLabel.

        Arguments:
            label_dict (dict): with label information

        Returns:
            label (instance): unsaved label
        """
        # Check if it is a system label or not
        label_type = EmailLabel.LABEL_SYSTEM if label_dict['type'] == 'system' else EmailLabel.LABEL_USER
        created = False
        with transaction.atomic():
            try:
                self.label = EmailLabel.objects.get(
                    account=self.manager.email_account,
                    label_id=label_dict['id'],
                    label_type=label_type,
                )
            except EmailLabel.DoesNotExist:
                self.label = EmailLabel(
                    account=self.manager.email_account,
                    label_id=label_dict['id'],
                    label_type=label_type,
                )
                created = True

        # Name could have changed, always set the name
        self.label.name = label_dict['name']
        self.label.save()
        gc.collect()
        return self.label, created

    def cleanup(self):
        """
        Cleanup references, to prevent reference cycle
        """
        self.manager = None
        self.label = None