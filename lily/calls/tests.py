import json
from channels import Group
from channels.tests import ChannelTestCase, WSClient
from channels.signals import consumer_finished
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from lily.tenant.factories import TenantFactory
from lily.users.factories import TeamFactory
from lily.accounts.factories import AccountFactory
from lily.contacts.factories import ContactFactory, ContactWithAccountFactory, FunctionFactory
from lily.utils.models.factories import PhoneNumberFactory
from lily.users.models import LilyUser
from lily.users.factories import LilyUserFactory
from django.test import Client, override_settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from lily.tests.utils import UserBasedTest, get_dummy_credentials
from django.conf import settings

class SocketTests(UserBasedTest, ChannelTestCase):
    @classmethod
    @override_settings(CHANNEL_SESSION_ENGINE="user_sessions.backends.db")
    def setUpTestData(cls):
        print settings.CHANNEL_SESSION_ENGINE

        super(SocketTests, cls).setUpTestData()

        cls.account = AccountFactory(tenant=cls.user_obj.tenant) # Already has 1 phonenumber

        phonenumbers = PhoneNumberFactory.create_batch(2, tenant=cls.user_obj.tenant)
        cls.contact = ContactFactory(tenant=cls.user_obj.tenant)
        cls.contact.phone_numbers.add(*phonenumbers)

        # Client for websocket messages
        cls.wsclient = WSClient()
        cls.wsclient.login(email=cls.user_obj.email, password='password')

        # Client for HTTP Calls
        cls.client = Client()
        cls.client.login(email=cls.user_obj.email, password='password')

    # In deze test zelf maakt het niet meer uit welke session backend je gebruikt, zolang
    # die bij het inloggen maar "user_sessions.backends.db" is
    @override_settings(CHANNEL_SESSION_ENGINE="django.contrib.sessions.backends.db")
    def test_1(self):
        print settings.CHANNEL_SESSION_ENGINE
        # Deze gaat kapot wanneer je de CHANNELS_SESSION_ENGINE niet override in setUpTestData
        self.wsclient.send_and_consume(u'websocket.connect')
        self.assertIsNone(self.wsclient.receive())

    def test_2(self):
        pass
