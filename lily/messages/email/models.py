import copy
import email

from BeautifulSoup import BeautifulSoup, Comment, Declaration
from django.db import models
from django.template.defaultfilters import truncatechars
from django_extensions.db.models import TimeStampedModel
from django.utils.translation import ugettext as _
from django_fields.fields import EncryptedCharField, EncryptedEmailField

from lily.messages.email.emailclient import DRAFTS, TRASH
from lily.messages.models import Message, MessagesAccount
from lily.settings import EMAIL_ATTACHMENT_UPLOAD_TO
from lily.utils.functions import get_tenant_mixin as TenantMixin


class EmailProvider(TenantMixin):
    """
    A provider contains the connection information for an account.
    """
    name = models.CharField(max_length=30, blank=True, null=True)  # named providers are defaults.
    retrieve_host = models.CharField(max_length=32)
    retrieve_port = models.IntegerField()

    send_host = models.CharField(max_length=32)
    send_port = models.IntegerField()
    send_use_tls = models.BooleanField()

    def __unicode__(self):
        return self.retrieve_host if len(self.name.strip()) == 0 else self.name

    class Meta:
        verbose_name = _('e-mail provider')
        verbose_name_plural = _('e-mail providers')


class EmailAccount(MessagesAccount):
    """
    An e-mail account.
    """
    name = models.CharField(max_length=255)
    email = EncryptedEmailField(max_length=255)
    username = EncryptedCharField(max_length=255)
    password = EncryptedCharField(max_length=255)
    provider = models.ForeignKey(EmailProvider, related_name='email_accounts')
    last_sync_date = models.DateTimeField()

    def __unicode__(self):
        return self.name if self.name else self.email

    class Meta:
        verbose_name = _('e-mail account')
        verbose_name_plural = _('e-mail accounts')


class EmailMessage(Message):
    """
    A single e-mail message.
    """
    uid = models.IntegerField()  # unique id on the server
    flags = models.TextField(blank=True, null=True)
    body = models.TextField(blank=True, null=True)
    size = models.IntegerField(default=0, null=True)  # size in bytes
    folder_name = models.CharField(max_length=255)
    is_private = models.BooleanField(default=False)

    def has_attachments(self):
        return self.attachments.count() > 0

    # def get_conversation(self):
    #     """
    #     Return the entire conversation this message is a part of.
    #     """
    #     messages = []
    #     message = self.headers.filter(name='In-Reply-To')
    #     while message != None:
    #         messages.append(message)
    #         try:
    #             message_id = message.headers.filter(name='In-Reply-To')
    #             message = EmailMessage.objects.get(header__name='MSG-ID', header_value=message_id)
    #         except EmailMessage.DoesNotExist:
    #             message = None

    #     return messages

    @property
    def flat_body(self):
        if self.body:
            soup = BeautifulSoup(self.body)

            # Remove html comments
            comments = soup.findAll(text=lambda text: isinstance(text, Comment))
            for comment in comments:
                comment.extract()

            flat_soup = copy.deepcopy(soup)

            # Remove doctype tag from flat_soup
            for child in flat_soup.contents:
                if isinstance(child, Declaration):
                    declaration_type = child.string.split()[0]
                    if declaration_type.upper() == 'DOCTYPE':
                        del flat_soup.contents[flat_soup.contents.index(child)]

            # Remove several tags from flat_soup
            extract_tags = ['style', 'script', 'img', 'object', 'audio', 'video', 'doctype']
            for elem in flat_soup.findAll(extract_tags):
                elem.extract()

            return ''.join(flat_soup.findAll(text=True)).strip('&nbsp;\n ').replace('\r\n', ' ').replace('\r', '').replace('\n', ' ').replace('&nbsp;', ' ')  # pass html white-space to strip() also
        return ''

    @property
    def subject(self):
        header = None
        if getattr(self, '_subject_header', False):
            header = self._subject_header
        else:
            header = self.headers.filter(name='Subject')
            self._subject_header = header
        if header:
            return header[0].value
        return None

    @property
    def to_name(self):
        header = None
        if getattr(self, '_to_header', False):
            header = self._to_header
        else:
            header = self.headers.filter(name='To')
            self._to_header = header
        if header:
            return email.utils.parseaddr(header[0].value)[0]
        return ''

    @property
    def to_email(self):
        header = None
        if getattr(self, '_to_header', False):
            header = self._to_header
        else:
            header = self.headers.filter(name='To')
            self._to_header = header
        if header:
            return email.utils.parseaddr(header[0].value)[1]
        return ''

    @property
    def from_name(self):
        header = None
        if getattr(self, '_from_header', False):
            header = self._from_header
        else:
            header = self.headers.filter(name='From')
            self._from_header = header
        if header:
            return email.utils.parseaddr(header[0].value)[0]
        return ''

    @property
    def from_email(self):
        header = None
        if getattr(self, '_from_header', False):
            header = self._from_header
        else:
            header = self.headers.filter(name='From')
            self._from_header = header
        if header:
            return email.utils.parseaddr(header[0].value)[1]
        return ''

    @property
    def is_plain(self):
        header = self.headers.filter(name='Content-Type')
        if header:
            return header[0].value.startswith('text/plain')
        return False

    @property
    def is_draft(self):
        return DRAFTS in self.flags

    @property
    def is_deleted(self):
        return TRASH in self.flags

    def __unicode__(self):
        return u'%s - %s'.strip() % (email.utils.parseaddr(self.from_email), truncatechars(self.subject, 130))

    class Meta:
        verbose_name = _('e-mail message')
        verbose_name_plural = _('e-mail messages')
        unique_together = ('uid', 'folder_name', 'account')


class EmailAttachment(TenantMixin):
    """
    A single attachment linked to an e-mail message.
    """
    attachment = models.FileField(upload_to=EMAIL_ATTACHMENT_UPLOAD_TO)  # also contains filename
    size = models.PositiveIntegerField(default=0)  # size in bytes
    message = models.ForeignKey(EmailMessage, related_name='attachments')

    class Meta:
        verbose_name = _('e-mail attachment')
        verbose_name_plural = _('e-mail attachments')


class EmailHeader(models.Model):
    """
    A single e-mail header linked to an e-mail message.
    Most common are: 'to', 'from' and 'content-type'.
    """
    name = models.CharField(max_length=255)
    value = models.TextField(null=True)
    message = models.ForeignKey(EmailMessage, related_name='headers')


class EmailLabel(models.Model):
    """
    A single label in which an e-mail message can be linked to.
    """
    name = models.CharField(max_length=50)
    message = models.ForeignKey(EmailMessage, related_name='labels')


class ActionStep(TenantMixin):
    """
    ActionStep helping decide the order in which to process e-mail messages.
    """
    LOW, NORMAL, HIGH = range(3)
    ACTION_STEP_PRIO = (
        (LOW, _('Low priority')),
        (NORMAL, _('Normal priority')),
        (HIGH, _('High priority'))
    )
    priority = models.IntegerField()
    done = models.BooleanField(default=False)
    message = models.ForeignKey(EmailMessage)


class EmailTemplate(TenantMixin, TimeStampedModel):
    """
    Emails can be composed using templates.
    A template is a predefined email in which parameters can be dynamically inserted.

    """
    name = models.CharField(verbose_name=_('template name'), max_length=255)
    body = models.TextField(verbose_name=_('message body'))

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        verbose_name = _('e-mail template')
        verbose_name_plural = _('e-mail templates')


class EmailTemplateParameters(TenantMixin, TimeStampedModel):
    """
    All template parameters are stored in the database, a parameter is a dynamically filled part of a template.
    This models contains those parameters and the default value of that parameter (can be overwritten during e-mail composing).

    Default values can be static or dynamic, which one it is is stored in the is_dynamic field:
        static  = 'value'
        dynamic = 'model/pk/field'

    The is_dynamic part should be in sync with the is_dynamic set in parameter choice.
    There is no foreign key to the choice since the values are copied to this model.

    """
    template = models.ForeignKey(EmailTemplate, verbose_name=_(''), related_name='parameters')
    name = models.CharField(verbose_name=_('parameter name'), max_length=255)
    value = models.CharField(verbose_name=_('parameter value'), max_length=255, blank=True)
    label = models.CharField(_('choice label'), max_length="255", blank=True)
    is_dynamic = models.BooleanField(_('parameter is dynamic'), default=False)


    @property
    def get_display_value(self):
        # TODO: check if dynamic and parse that shit up!
        return self.value

    def __unicode__(self):
        return u'%s - %s' % (self.name, self.value)

    class Meta:
        verbose_name = _('e-mail template parameter')
        verbose_name_plural = _('e-mail template parameters')


class EmailTemplateParameterChoice(TenantMixin, models.Model):
    """
    These are default value choices for parameters that are displayed in the choices dropdown.

    """
    label = models.CharField(_('choice label'), max_length="255")
    value = models.CharField(_('choice value'), max_length="255")
    is_dynamic = models.BooleanField(_('choice is dynamic'), default=False)


    def __unicode__(self):
        return u'%s - %s' % (self.label, self.value)


    class Meta:
        verbose_name = _('e-mail template parameter choice')
        verbose_name_plural = _('e-mail template parameter choices')