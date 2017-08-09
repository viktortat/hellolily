from microsoft_mail_client.constants import (
    SUPPORTED_API_VERSIONS, WRITABLE_MESSAGE_PROPERTIES, INFERENCE_CLASSIFICATION_OPTIONS, SETTING_OPTIONS,
    SETTING_AUTOMATIC_REPLIES, WRITABLE_FILE_PROPERTIES, WRITABLE_ITEM_PROPERTIES, WRITABLE_REFERENCE_PROPERTIES
)
from microsoft_mail_client.http import HttpRequest
from microsoft_mail_client.errors import (
    UnknownApiVersion, NoFolderId, NoMessageId, NoComment, NoRecipients, NoMessage, InvalidClassification,
    InvalidSettingsOption, NoFileName, NoFile, InvalidWritableFileProperty, InvalidWritableItemProperty, NoItem,
    InvalidWritableMessageProperty, NoUrl, InvalidWritableReferenceProperty, NoItemName, NoReferenceName,
    NoAttachmentId, NoName, NoDestinationFolderId
)

# TODO: On email threading / conversation:
# stackoverflow.com/questions/41161515/best-way-to-achieve-conversation-view-for-mail-folder-using-outlook-rest-api
# TODO: On push notifications: https://docs.microsoft.com/en-us/outlook/rest/webhooks
# TODO: On archiving mail: https://stackoverflow.com/questions/41065083/outlook-rest-api-and-mail-archive-action


def build(version, user_email, credentials=None):
    # Returns a Resource object with methods for interacting with the Microsoft 365 email API.
    if version not in SUPPORTED_API_VERSIONS:
        raise UnknownApiVersion("Version: {0}".format(version))

    return Resource(version, user_email, credentials)


class Resource(object):
    """
    A class for interacting with the resource.
    """

    def __init__(self, version, user_email, credentials):
        # TODO: Handle credentials=None or don't allow.
        self.version = version
        self.user_email = user_email
        self.credentials = credentials

        # TODO: use uritemplate.expand() like google api does.
        self._base_url = 'https://outlook.office.com/api/{0}/users/{1}'.format(version, user_email)
        # self._base_url = "https://outlook.office.com/api/{0}/users/'{1}'".format(version, user_email)
        # self._base_url = 'https://outlook.office365.com/api/{0}'.format(version)  # Larger attachment size limit.
        self._base_url += '{0}'

        self._batch_url = "https://outlook.office.com/api/{0}/users('{0}')/$batch".format(version, user_email)

        self._authorization_headers = {
            'Authorization': 'Bearer {0}'.format(self.credentials.access_token),
            'X-AnchorMailbox': self.user_email,
        }

    def get_messages(self, folder_id=None, allow_unsafe=False, body_content_type=None, query_parameters=None):
        """
        Get a message collection from the entire mailbox of the signed-in user (including the Deleted Items and Clutter
        folders).

        :param folder_id: optional.
        :param allow_unsafe: Don't strip message body from harmfull html. Optional.
        :param body_content_type: Allowed: None (falls back to html if available). html or text. Optional.
        :param query_parameters: use OData query parameters to control the results.
        :return: HttpRequest object.
        """
        headers = {}
        if allow_unsafe:
            headers = {
                'Prefer': 'outlook.allow-unsafe-html',
            }

        if body_content_type:
            if body_content_type in ['text', 'html']:
                additional_headers = {
                    'Prefer': 'outlook.body-content-type="{0}'.format(body_content_type),
                }
                headers = additional_headers

        url = self._base_url.format('/messages')
        if folder_id:
            url = self._base_url.format('/MailFolders/{0}/messages').format(folder_id)

        headers.update(self._authorization_headers)

        return HttpRequest(uri=url, method='GET', headers=headers, parameters=query_parameters)

    def get_message(self, message_id, allow_unsafe=False, body_content_type=None, query_parameters=None):
        """
        Get a message by ID.

        :param message_id:
        :param allow_unsafe: Don't strip message body from harmfull html. Optional.
        :param body_content_type: Allowed: None (falls back to html if available), 'html' or 'text'. Optional.
        :param query_parameters: use OData query parameters to control the results.
        :return: HttpRequest object.
        """
        if not message_id:
            raise NoMessageId()

        headers = {}
        if allow_unsafe:
            headers = {
                'Prefer': 'outlook.allow-unsafe-html',
            }

        if body_content_type:
            if body_content_type in ['text', 'html']:
                additional_headers = {
                    'Prefer': 'outlook.body-content-type="{0}'.format(body_content_type),
                }
                headers = additional_headers

        url = self._base_url.format('/messages/{0}').format(message_id)

        headers.update(self._authorization_headers)

        return HttpRequest(uri=url, method='GET', headers=headers, parameters=query_parameters)

    def synchronize_messages(self, folder_id, delta_token=None, skip_token=None, max_page_size=None,
                             query_parameters=None):
        """
        Return a collection containing the requested messages, use for a full or incremental synchronization.

        :param folder_id: required.
        :param delta_token: token that identifies the last sync request for that folder. Optional.
        :param skip_token: token that indicates that there are more messages to download. Optional.
        :param max_page_size: number of messages per response. Optional.
        :param query_parameters: use OData query parameters to control the results.  Optional.
               Full supported parameters: $select, $top, $expand.
               Limited supported parameters: $filter, $orderby.
               Not supoorted parameters: $search.
        :return: HttpRequest object.

        Usage:
            The initial response returns x messages, a deltaLink and deltaToken.
            The second request uses that deltaToken.
            The second response returns x messages, a nextLink and skipToken.
            To complete the sync, the follow up requests use the skipToken returned from the previous sync request,
                until the last sync response returns a deltaLink and deltaToken, this round of sync is complete.
            Save the deltaToken for the next round of sync.
        """
        if not folder_id:
            raise NoFolderId()

        headers = {}
        if not skip_token:
            headers = {
                'Prefer': 'odata.track-changes',
            }

        if max_page_size:
            additional_headers = {
                'Prefer': 'odata.maxpagesize={0}'.format(max_page_size),
            }
            headers = additional_headers

        if delta_token and delta_token not in query_parameters:
            query_parameters.update({'deltatoken': delta_token})

        if skip_token and skip_token not in query_parameters:
            query_parameters.update({'skiptoken': skip_token})

        url = self._base_url.format('/MailFolders/{0}/messages').format(folder_id)

        headers.update(self._authorization_headers)

        return HttpRequest(uri=url, method='GET', headers=headers, parameters=query_parameters)

        # TODO: Move to parse_history.
        # TODO: extract tokens from response, add the to the return.
        # next_skip_token = None
        # extract skip_token from result
        # next_delta_token = None
        # extract delta_token from result
        # TODO: also extract if 'Preference-Applied: odata.track-changes' is present, and return true/false.
        # return skip_token, delta_token, response

    def send_message(self, message, save_to_sent_items=True):
        """
        Send an email message.

        :param message: dict.
        :param save_to_sent_items: Indicates whether to save the message in Sent Items.
        :return: HttpRequest object.
        """
        if not message:
            raise NoMessage()

        if not save_to_sent_items:
            # Only add this field to the message if user don't want to save it to the sent items folder.
            message['SaveToSentItems'] = save_to_sent_items

        url = self._base_url.format('/sendmail')

        return HttpRequest(uri=url, method='POST', payload=message, headers=self._authorization_headers)

    def draft_message(self, message, folder_id):
        """
        Create a draft of a new message.

        :param message: dict.
        :param folder_id: save draft in this folder, Optinal, Default to Drafts.
        :return: HttpRequest object.
        """
        if not message and 'Comment' not in message:
            raise NoComment()

        url = self._base_url.format('/messages')
        if folder_id:
            url = self._base_url.format('/MailFolders/{0}/messages').format(folder_id)

        return HttpRequest(uri=url, method='POST', headers=self._authorization_headers, payload=message)

    def sent_draft_message(self, message_id):
        """
        Send a new message draft. The message is then saved in the Sent Items folder.

        :param message_id:
        :return: HttpRequest object.
        """
        if not message_id:
            raise NoMessageId()

        url = self._base_url.format('/messages/{0}/send').format(message_id)

        return HttpRequest(uri=url, method='POST', headers=self._authorization_headers)

    def sent_reply_message(self, message_id, message, reply_all=False):
        """
        Reply to a message.

        :param message_id: replying to this message.
        :param message: dict with key 'comment' with the actual comment as a value. So excluding the body of original
               message.
               stackoverflow.com/questions/41937948/how-to-properly-respond-to-an-email-using-the-outlook-rest-api
        :param reply_all: reply to all recipients or just to the sender. Optional.
        :return: HttpRequest object.
        """
        if not message_id:
            raise NoMessageId()

        if not message and 'Comment' not in message:
            raise NoComment()

        url = self._base_url.format('/messages/{0}/reply').format(message_id)
        if reply_all:
            url = self._base_url.format('/messages/{0}/replyall').format(message_id)

        return HttpRequest(uri=url, method='POST', headers=self._authorization_headers, payload=message)

    def sent_reply_all_message(self, message_id, message):
        """
        Reply to all recipients of a message.

        :param message_id: replying to this message.
        :param message: dict with key 'comment' with the actual comment as a value. So excluding the body of original
               message.
               stackoverflow.com/questions/41937948/how-to-properly-respond-to-an-email-using-the-outlook-rest-api
        :return: HttpRequest object.
        """
        return self.sent_reply_message(message_id, message, True)

    def draft_reply_message(self, message_id, message, reply_all=False):
        """
        Create a draft of a reply message.

        :param message_id: replying to this message.
        :param message: dict with key 'Comment' with the actual comment as a value. Falls back to empty comment.
               So excluding the body of original message.
               https://stackoverflow.com/questions/41937948/how-to-properly-respond-to-an-email-using-the-outlook-rest-api
        :param reply_all: reply to all recipients or just to the sender. Optional.
        :return: HttpRequest object.
        """
        if not message_id:
            raise NoMessageId()

        if not message and 'Comment' not in message:
            # No message provided, just draft an empty message.
            message = {'Comment': ''}

        url = self._base_url.format('/messages/{0}/createreply').format(message_id)
        if reply_all:
            url = self._base_url.format('/messages/{0}/createreplyall').format(message_id)

        return HttpRequest(uri=url, method='POST', headers=self._authorization_headers, payload=message)

    def draft_reply_all_message(self, message_id, message):
        """
        Create a draft of a reply-all message.

        :param message_id: replying to this message.
        :param message: dict with key 'Comment' with the actual comment as a value. Falls back to empty comment.
               So excluding the body of original message.
               stackoverflow.com/questions/41937948/how-to-properly-respond-to-an-email-using-the-outlook-rest-api
        :return: HttpRequest object.
        """
        return self.draft_reply_message(message_id, message, True)

    def sent_forward_message(self, message_id, message, recipients):
        """
        Forward a message. The message is saved in the Sent Items folder.

        :param message_id: message for forward.
        :param message: dict with key 'Comment' with the actual comment as a value. Falls back to empty comment.
               So excluding the body of original message.
               stackoverflow.com/questions/41937948/how-to-properly-respond-to-an-email-using-the-outlook-rest-api
        :param recipients: dict with key 'ToRecipients'.
        :return: HttpRequest object.
        """
        if not message_id:
            raise NoMessageId()

        if not recipients and 'ToRecipients' not in recipients:
            raise NoRecipients()

        if not message and 'Comment' not in message:
            # No message provided, just forward an empty message.
            message = {'Comment': ''}

        url = self._base_url.format('/messages/{0}/forward').format(message_id)

        payload = {
            'Comment': message['Comment'],
            'ToRecipients': recipients['ToRecipients'],
        }

        return HttpRequest(uri=url, method='POST', headers=self._authorization_headers, payload=payload)

    def draft_forward_message(self, message_id, message, recipients):
        """
        Create a draft of a forward message.

        :param message_id: message for forward.
        :param message: dict with key 'Comment' with the actual comment as a value. Falls back to empty comment.
               So excluding the body of original message.
               https://stackoverflow.com/questions/41937948/how-to-properly-respond-to-an-email-using-the-outlook-rest-api
        :param recipients: dict with key 'ToRecipients'. Optional.
        :return: HttpRequest object.
        """
        if not message_id:
            raise NoMessageId()

        if not message and 'Comment' not in message:
            # No message provided, just forward an empty message.
            message = {'Comment': ''}

        url = self._base_url.format('/messages/{0}/createforward').format(message_id)

        payload = {
            'Comment': message['Comment'],
            'ToRecipients': recipients['ToRecipients'],
        }

        return HttpRequest(uri=url, method='POST', headers=self._authorization_headers, payload=payload)

    def update_message(self, message_id, properties):
        """
        Change writable properties on a draft or existing message. Only the properties that you specify are changed.

        :param message_id: message to change.
        :param properties: dict with writable properties.
        :return: HttpRequest object.
        """
        if not message_id:
            raise NoMessageId()

        res = set(properties.keys()) - set(WRITABLE_MESSAGE_PROPERTIES)
        if len(res) != 0:
            raise InvalidWritableMessageProperty('Invalid properties: {0}'.format(', '.join(res)))

        url = self._base_url.format('/messages')

        return HttpRequest(uri=url, method='PATCH', headers=self._authorization_headers, payload=properties)

    def delete_message(self, message_id):
        """
        Delete a message.

        :param message_id: message to delete.
        :return: HttpRequest object.
        """
        if not message_id:
            raise NoMessageId()

        url = self._base_url.format('/messages/{0}').format(message_id)

        return HttpRequest(uri=url, method='DELETE', headers=self._authorization_headers)

    def move_message(self, message_id, destination_folder_id):
        """
        Move a message to a folder. This creates a new copy of the message in the destination folder.

        :param message_id: message to move.
        :param destination_folder_id: destination folder.
        :return: HttpRequest object.
        """
        if not message_id:
            raise NoMessageId()

        if not destination_folder_id:
            raise NoFolderId()

        url = self._base_url.format('/messages/{0}/move').format(message_id)

        payload = {
            'DestinationId': destination_folder_id
        }

        return HttpRequest(uri=url, method='POST', headers=self._authorization_headers, payload=payload)

    def copy_message(self, message_id, destination_folder_id):
        """
        Copy a message to a folder.

        :param message_id: message to copy.
        :param destination_folder_id: destination folder.
        :return: HttpRequest object.
        """
        if not message_id:
            raise NoMessageId()

        if not destination_folder_id:
            raise NoFolderId()

        url = self._base_url.format('/messages/{0}/copy').format(message_id)

        payload = {
            'DestinationId': destination_folder_id
        }

        return HttpRequest(uri=url, method='POST', headers=self._authorization_headers, payload=payload)

    def update_message_classification(self, message_id, classification, user_id=None):
        """
        Focused Inbox: change the InferenceClassification property of the specified message.
        This also trains the message classification.

        :param message_id: message to classify.
        :param classification: property to classify the message with.
        :param user_id: Optional.
        :return: HttpRequest object.
        """
        if not message_id:
            raise NoMessageId()

        if classification not in INFERENCE_CLASSIFICATION_OPTIONS:
            raise InvalidClassification()

        url = self._base_url.format('/messages/{0}').format(message_id)

        if user_id:
            url = self._base_url.format('/Users/{0}/messages/{1}').format(user_id, message_id)

        payload = {
            'InferenceClassification': classification
        }

        return HttpRequest(uri=url, method='PATCH', headers=self._authorization_headers, payload=payload)

    def override(self):
        """
        Focused Inbox: create an override for a sender identified by an SMTP address.
        """
        # TODO: implement.
        raise NotImplementedError()

    def get_overrides(self):
        """
        Focused Inbox: get the overrides that a user has set up.
        """
        # TODO: implement.
        raise NotImplementedError()

    def update_override(self):
        """
        Focused Inbox: change the ClassifyAs field of an override.
        """
        # TODO: implement.
        raise NotImplementedError()

    def delete_override(self):
        """
        Focused Inbox: delete an override.
        """
        # TODO: implement.
        raise NotImplementedError()

    def get_settings(self, option=None, outlook_time_zone=False):
        """
        Get the settings for the primary mailbox of the signed-in user.

        :param option: request a specific mailbox setting. Optional. Fallback to all settings.
        :param outlook_time_zone: use time zone. Optional.
        :return: HttpRequest object.
        """
        if option and option not in SETTING_OPTIONS:
            raise InvalidSettingsOption()

        url = self._base_url.format('/MailboxSettings')
        if option:
            url = self._base_url.format('/MailboxSettings/{0}').format(option)

        headers = {}
        if outlook_time_zone:
            headers = {
                'Prefer': 'outlook.timezone',
            }

        headers.update(self._authorization_headers)

        return HttpRequest(uri=url, method='GET', headers=headers)

    def get_auto_reply(self, outlook_time_zone=False):
        """
        Get the automatic reply settings of the signed-in user's mailbox.

        :param outlook_time_zone: use time zone. Optional.
        :return: HttpRequest object.
        """
        return self.get_settings(SETTING_AUTOMATIC_REPLIES, outlook_time_zone)

    def update_auto_reply(self):
        """
        Enable, configure, or disable automatic replies.
        """
        # TODO: implement.
        raise NotImplementedError()

    def get_attachments(self, message_id, attachment_id=None, query_parameters=None):
        """
        Get the specific attachment or attachment collection from a particular message.

        :param message_id: attachment(s) for message.
        :param attachment_id: specific attachement. Optional. Falls back to all attachment.
        :param query_parameters: use OData query parameters to control the results.
        :return: HttpRequest object.
        """
        if not message_id:
            raise NoMessageId()

        url = self._base_url.format('/messages/{0}/attachments').format(message_id)
        if attachment_id:
            url = self._base_url.format('/messages/{0}/attachments/{1}').format(message_id, attachment_id)

        return HttpRequest(uri=url, method='GET', headers=self._authorization_headers, parameters=query_parameters)

    def get_attachemnt(self, message_id, query_parameters=None):
        """
        Get an attachment from a particular message.

        :param message_id: attachment for message.
        :param query_parameters: use OData query parameters to control the results
        :return: HttpRequest object.
        """
        self.get_attachments(message_id, query_parameters=query_parameters)

    def create_file_attachment(self, message_id, attachment, name, properties=None):
        """
        Add a file attachment to a message.

        :param message_id: attach file to this message.
        :param attachment: file to attach. base64-encoded.
        :param name: name of the attachement.
        :param properties: additional writable file properties. Optional.
        :return: HttpRequest object.
        """
        if not message_id:
            raise NoMessageId()

        if not name:
            raise NoFileName()

        if not file:
            raise NoFile()

        res = set(properties.keys()) - set(WRITABLE_FILE_PROPERTIES)
        if len(res) != 0:
            raise InvalidWritableFileProperty('Invalid properties: {0}'.format(', '.join(res)))

        payload = {
            '@odata.type': '#Microsoft.OutlookServices.FileAttachment',
            'ContentBytes': attachment,
        }

        if name not in properties:
            additional_payload = {
                'Name': name,
            }
            payload.update(additional_payload)

        if properties:
            payload.update(properties)

        url = self._base_url.format('/messages/{0}/attachments').format(message_id)

        return HttpRequest(uri=url, method='POST', headers=self._authorization_headers, payload=payload)

    def create_item_attachment(self, message_id, item, name, properties=None):
        """
        Add an item attachment to a message.

        An item could be another message, contact, or event.

        :param message_id: attach item to this message.
        :param item: item to attach.
        :param name: name of the attachement.
        :param properties: additional writable item properties. Optional.
        :return: HttpRequest object.
        """
        if not message_id:
            raise NoMessageId()

        if not name:
            raise NoItemName()

        if not item:
            raise NoItem()

        res = set(properties.keys()) - set(WRITABLE_ITEM_PROPERTIES)
        if len(res) != 0:
            raise InvalidWritableItemProperty('Invalid properties: {0}'.format(', '.join(res)))

        payload = {
            '@odata.type': '#Microsoft.OutlookServices.ItemAttachment',
            'Item': item,
        }

        if name not in properties:
            additional_payload = {
                'Name': name,
            }
            payload.update(additional_payload)

        if properties:
            payload.update(properties)

        url = self._base_url.format('/messages/{0}/attachments').format(message_id)

        return HttpRequest(uri=url, method='POST', headers=self._authorization_headers, payload=payload)

    def create_reference_attachment(self, message_id, url, name, properties=None):
        """
        Add a reference attachment to a message.

        Url is a link to a file or folder, attached to a message, event, or task. Possible locations for the file or
        folder includes OneDrive, OneDrive for Business, and DropBox.

        :param message_id: attach reference attachment to this message.
        :param url: reference to attach.
        :param name: name of the attachement.
        :param properties: additional writable reference properties. Optional. 'IsFolder' must be True if url points to
               a folder.
        :return: HttpRequest object.
        """
        if not message_id:
            raise NoMessageId()

        if not name:
            raise NoReferenceName()

        if not url:
            raise NoUrl()

        res = set(properties.keys()) - set(WRITABLE_REFERENCE_PROPERTIES)
        if len(res) != 0:
            raise InvalidWritableReferenceProperty('Invalid properties: {0}'.format(', '.join(res)))

        payload = {
            '@odata.type': '#Microsoft.OutlookServices.ReferenceAttachment',
            'SourceUrl': url,
        }

        if name not in properties:
            additional_payload = {
                'Name': name,
            }
            payload.update(additional_payload)

        if properties:
            payload.update(properties)

        url = self._base_url.format('/messages/{0}/attachments').format(message_id)

        return HttpRequest(uri=url, method='POST', headers=self._authorization_headers, payload=payload)

    def delete_attachment(self, message_id, attachment_id):
        """
        Delete the specified attachment of a message.

        :param message_id: message with attachments.
        :param attachment_id: attachement to delete.
        :return: HttpRequest object.
        """
        if not message_id:
            raise NoMessageId()

        if not attachment_id:
            raise NoAttachmentId()

        url = self._base_url.format('/messages/{0}/attachments/{1}').format(message_id, attachment_id)

        return HttpRequest(uri=url, method='DELETE', headers=self._authorization_headers)

    def get_folders(self, folder_id=None, query_parameters=None):
        """
        Get the folder collection under the root or the specified folder.

        :param folder_id: get folders under this folder. Optional. Falls back to root folder.
        :param query_parameters: use OData query parameters to control the results.
        :return: HttpRequest object.
        """
        url = self._base_url.format('/MailFolders')
        if not folder_id:
            url = self._base_url.format('/MailFolders/{0}/childfolders').format(folder_id)

        return HttpRequest(uri=url, method='GET', headers=self._authorization_headers, parameters=query_parameters)

    def get_folder(self, folder_id, query_parameters=None):
        """
        Get a folder.

        :param folder_id: get this folder.
        :param query_parameters: use OData query parameters to control the results.
        :return: HttpRequest object.
        """
        if not folder_id:
            raise NoFolderId

        url = self._base_url.format('/MailFolders/{0}').format(folder_id)

        return HttpRequest(uri=url, method='GET', headers=self._authorization_headers, parameters=query_parameters)

    def synchronize_folders(self, delta_token=None, query_parameters=None):
        # TOOD: unclear documenation: how to pass requested category?
        # TODO: unclear documentation: deltatoken or odata.deltaLink,
        # TODO: unclear documentation: deltaX as query_parameters or in the payload?
        # TODO: unclear documentation: implementation like synchronize_message()?
        """

        :param delta_token:
        :param query_parameters:
        :return: HttpRequest object.
        """
        headers = {}
        if delta_token:
            # Incremental synchronization.
            headers = {
                'Prefer': 'odata.track-changes',
            }

        if delta_token and delta_token not in query_parameters:
            query_parameters.update({'deltatoken': delta_token})

        url = self._base_url.format('/MailFolders')

        headers.update(self._authorization_headers)

        return HttpRequest(uri=url, method='GET', headers=headers, parameters=query_parameters)

    def create_folder(self, folder_id, name):
        """
        Create a child folder by the name specified.

        :param folder_id: parent of the new folder.
        :param name: name of the new folder.
        :return: HttpRequest object.
        """
        if not folder_id:
            raise NoFolderId()

        if not name:
            raise NoName()

        payload = {
            'DisplayName': name,
        }

        url = self._base_url.format('/MailFolders/{0}/childfolders').format(folder_id)

        return HttpRequest(uri=url, method='POST', headers=self._authorization_headers, payload=payload)

    def update_folder(self, folder_id, name):
        """
        Create a child folder by the name specified.

        :param folder_id: folder to update.
        :param name: updated name of the folder.
        :return: HttpRequest object.
        """
        if not folder_id:
            raise NoFolderId()

        if not name:
            raise NoName()

        payload = {
            'DisplayName': name,
        }

        url = self._base_url.format('/MailFolders/{0}').format(folder_id)

        return HttpRequest(uri=url, method='PATCH', headers=self._authorization_headers, payload=payload)

    def delete_folder(self, folder_id):
        """
        Delete a folder.

        :param folder_id: folder to be deleted.
        :return: HttpRequest object.
        """
        if not folder_id:
            raise NoFolderId()

        url = self._base_url.format('/MailFolders/{0}').format(folder_id)

        return HttpRequest(uri=url, method='DELETE', headers=self._authorization_headers)

    def move_folder(self, folder_id, destination_folder_id):
        """
        Move a folder and its contents to another folder.

        :param folder_id: folder to be moved.
        :param destination_folder_id: move to this folder.
        :return: HttpRequest object.
        """
        if not folder_id:
            raise NoFolderId()

        if not destination_folder_id:
            raise NoDestinationFolderId()

        payload = {
            'DestinationId': destination_folder_id,
        }

        url = self._base_url.format('/MailFolders/{0}/move').format(folder_id)

        return HttpRequest(uri=url, method='POST', headers=self._authorization_headers, payload=payload)

    def copy_folder(self, folder_id, destination_folder_id):
        """
        Copy a folder and its contents to another folder.

        :param folder_id: folder to be copied.
        :param destination_folder_id: copy to this folder.
        :return: HttpRequest object.
        """
        if not folder_id:
            raise NoFolderId()

        if not destination_folder_id:
            raise NoDestinationFolderId()

        payload = {
            'DestinationId': destination_folder_id,
        }

        url = self._base_url.format('/MailFolders/{0}/copy').format(folder_id)

        return HttpRequest(uri=url, method='POST', headers=self._authorization_headers, payload=payload)
