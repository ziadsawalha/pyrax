#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2013 Rackspace

# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
import requests
from paste.util.multidict import MultiDict

import pyrax
from pyrax.client import BaseClient
from pyrax import exceptions
from pyrax.manager import BaseManager
from pyrax.resource import BaseResource

MAILGUN_API = 'https://api.mailgun.net/v2'
MAILGUN_ACCOUNTS_API = 'https://mailgun.com/'
HEADERS = {'Accept': 'application/json'}


class MailgunDomain(BaseResource):
    """
    This class represents a Mailgun domain.
    """
    def __init__(self, *args, **kwargs):
        super(MailgunDomain, self).__init__(*args, **kwargs)
        self.id = self.name

    def delete(self):
        """Delete named domain from account."""
        return self.manager.delete(self)

    def send_simple_message(self, sender, recipients, subject, text):
        """Send simple plain text message."""
        return self.manager.send_simple_message(self.name, sender, recipients,
            subject, text)

    def send_complex_message(self, sender, recipients, subject, text,
        ccopy=None, bcc=None, html=None, files=None):
        """Send message that could include cc, bcc, files and html."""
        return self.manager.send_complex_message(self.name, sender, recipients,
            subject, text, ccopy, bcc, html, files)

    def send_mime_message(self, recipient, mime_file):
        """Send message as included mime file."""
        return self.manager.send_mime_message(self.name, recipient, mime_file)

    def send_message_no_tracking(self, sender, recipients, subject, text):
        """Send message with o:tracking tag set to False."""
        return self.manager.send_message_no_tracking(self.name, sender,
            recipients, subject, text)

    def send_scheduled_message(self, sender, recipient, subject, text, delivery_time):
        """Send message at scheduled epoch time."""
        return self.manager.send_scheduled_message(self.name, sender, recipient,
            subject, text, delivery_time)

    def send_tagged_message(self, sender, recipients, subject, text, tags=[]):
        """Send message with custom tags."""
        return self.manager.send_tagged_message(self.name, sender, recipients,
            subject, text, tags)

    def send_inline_image(self, sender, recipient, subject, text, html, files):
        """Send message with inline images."""
        return self.manager.send_inline_image(self.name, sender, recipient,
            subject, text, html, files)

    def send_template_message(self, sender, recipients, subject, text, recipient_vars):
        """Send template message supporting variables."""
        return self.manager.send_template_message(self.name, sender, recipients,
            subject, text, recipient_vars)

    def get_logs(self, start_time, limit=100, ascending='yes', pretty='yes',
        sender=None, receiver=None):
        """Return event logs for domain."""
        return self.manager.get_logs(self.name, start_time, limit, ascending, pretty,
            sender, receiver)

    def get_stats(self, events=[], skip=0, limit=100):
        """Return event stats for domain.
        params: 
            events: ["sent", "opened"] etc.
        """
        return self.manager.get_stats(self.name, events, skip, limit)

    def create_campaign(self, name, campaign_id):
        """Creates an email campaign."""
        return self.manager.create_campaign(self.name, campaign_id)

    def send_campaign_message(self, sender, recipients, subject, text, campaign_id):
        """Send a message to an existing campaign."""
        return self.manager.send_campaign_message(self.name, sender, recipients,
            subject, text, campaign_id)

    def get_campaign_stats(self, campaign_id, limit=20, group_by='daily_hour'):
        """Get statistics on campaign messages."""
        return self.manager.get_campaign_stats(self.name, campaign_id, limit, group_by)

    def get_mailboxes(self):
        """Returns list of mailboxes on current domain."""
        return self.manager.get_mailboxes(self.name)

    def create_mailbox(self, mailbox_address, password):
        """Creates mailbox on current domain."""
        return self.manager.create_mailbox(self.name, mailbox_address, password)

    def change_mailbox_password(self, mailbox_name, password):
        """Changes mailbox account password."""
        return self.manager.change_mailbox_password(self.name, mailbox_name, password)

    def delete_mailbox(self, mailbox_name):
        """Deletes specified mailbox from current domain."""
        return self.manager.delete_mailbox(self.name, mailbox_name)

    def list_webhooks(self):
        """Lists current webhooks on current domain."""
        return self.manager.list_webhooks(self.name)

    def get_webhook(self, webhook):
        """Returns data on specified webhook for current domain."""
        return self.manager.get_webhook(self.name, webhook)

    def create_webhook(self, webhook, url):
        """Creates specified webhook on current domain."""
        return self.manager.create_webhook(self.name, webhook, url)

    def update_webhook(self, webhook, url):
        """Updates the specified webhook with the provided url on current dom."""
        return self.manager.update_webhook(self.name, webhook, url)

    def delete_webhook(self, webhook):
        """Deletes specified webhook from current domain."""
        return self.manager.delete_webhook(self.name, webhook)


class MailgunManager(BaseManager):

    def fetch_apikey(self):
        """Returns Mailguin api key from valid token/tenant."""
        url = "%srackspace/accounts" % MAILGUN_ACCOUNTS_API
        ident = pyrax.identity
        data = {"account_id": ident.tenant_id, "auth_token": ident.token}

        try:
            req = requests.get(url, params=data, headers=HEADERS)                              
            response = req.json()['api_key']
        except KeyError:
            return req.text
        except requests.exceptions.RequestException:
            raise
        return response

    def create(self, dom_name, smtp_pass):
        """Creates Mailgun domain with supplied password."""
        data = {'name': dom_name, 'smtp_password': smtp_pass}
        return self._create('/domains', data=data)

    def _create(self, uri, data):
        resp, resp_body = self.api.method_post(uri, data=data)
        return self.resource_class(self, resp_body.get(self.response_key))

    def get(self, dom_name):
        """Returns details of specified domain."""
        return self._get('/domains/' + dom_name)

    def _get(self, uri):
        resp, resp_body = self.api.method_get(uri)
        resp_body[self.response_key]['receiving_dns_records'] = resp_body['receiving_dns_records']
        resp_body[self.response_key]['sending_dns_records'] = resp_body['sending_dns_records']
        return self.resource_class(self, resp_body.get(self.response_key))

    def send_simple_message(self, dom_name, sender, recipients, subject, text):
        """Send simple plain text message."""
        uri = "/%s/messages" % dom_name
        data={
            "from": sender, # "Excited User <me@samples.mailgun.org>"
            "to": recipients, # ["bar@example.com", "baz@example.com"]
            "subject": subject,
            "text": text
        }
        return self.api.method_post(uri, data=data)

    def send_complex_message(self, dom_name, sender, recipients, ccopy, bcc, subject, text, html=None, files=None):
        """Send message that could include cc, bcc, files and html."""
        uri = "/%s/messages" % dom_name
        files=files # MultiDict([("attachment", open("files/test.jpg")),
                     # ("attachment", open("files/test.txt"))])
        data={
            "from": sender,
            "to": recipients,
            "cc": ccopy,
            "bcc": bcc,
            "subject": subject,
            "text": text,
            "html": html # "<html>HTML version of the body</html>"
        } 
        return self.api.method_post(uri, data=data, files=files)

    def send_mime_message(self, dom_name, recipient, mime_file):
        """Send message as included mime file."""
        uri = "/%s/messages.mime" % dom_name
        data={"to": recipient}, # "bar@example.com"
        files={"message": mime_file} # open("files/message.mime")
        return self.api.method_post(uri, data=data, files=files)

    def send_message_no_tracking(self, dom_name, sender, recipients, subject, text):
        """Send message with o:tracking tag set to False."""
        uri = "/%s/messages" % dom_name
        data={
            "from": sender,
            "to": recipients, # ["bar@example.com", "baz@example.com"]
            "subject": subject,
            "text": text,
            "o:tracking": False
        }
        return self.api.method_post(uri, data=data)

    def send_scheduled_message(self, dom_name, sender, recipient, subject, text,
        delivery_time):
        """Send message at scheduled epoch time."""
        uri = "/%s/messages" % dom_name
        data={
            "from": sender,
            "to": recipient, # "bar@example.com"
            "subject": subject,
            "text": text,
            "o:deliverytime": delivery_time  # "Fri, 25 Oct 2011 23:10:10 -0000"
        }
        return self.api.method_post(uri, data=data)

    def send_tagged_message(self, dom_name, sender, recipients, subject, text, tags=[]):
        """Send message with custom tags."""
        uri = "/%s/messages" % dom_name
        data = MultiDict([("from", sender),
                        ("subject", subject),
                        ("text", text)])
                        #("o:tag", "September newsletter"),
                        #("o:tag", "newsletters")]))
        if isinstance(recipients, basestring):
            data.add('to', recipients)
        elif isinstance(recipients, list) or isinstance(recipients, tuple):
            for item in recipients:
                data.add('to', item)
        else:
            raise Exception('Invalid recipients type.')

        for tag in tags:
            for k, v in tag.items():
                data.add(k, v)
        return self.api.method_post(uri, data=data)

    def send_inline_image(self, dom_name, sender, recipient, subject, text, html, files):
        """Send message with inline images."""
        uri = "/%s/messages" % dom_name
        files=MultiDict(), # [("inline", open("files/test.jpg"))]
        data={"from": sender,
              "to": recipient,
              "subject": subject,
              "text": text,
              "html": html} # '<html>Inline image here: <img src="cid:test.jpg"></html>'
        for item in files:
            for k, v in item.items():
                files.add(k, v)
        return self.api.method_post(uri, data=data, files=files)

    def send_template_message(self, dom_name, sender, recipients, subject, text, recipient_vars):
        """Send template message supporting variables."""
        uri = "/%s/messages" % dom_name,
        data={"from": sender,
              "to": recipients, # ["alice@example.com, bob@example.com"]
              "subject": subject, # "Hey, %recipient.first%"
              "text": text, # "If you wish to unsubscribe, click http://mailgun/unsubscribe/%recipient.id%'"
              "recipient-variables": recipient_vars} # ('{"bob@example.com": {"first":"Bob", "id":1}, '
                                                      # '"alice@example.com": {"first":"Alice", "id": 2}}')
        return self.api.method_post(uri, data=data)

    def create_mailing_list(self, address, description):
        uri= "/lists"
        data={'address': address,
              'description': description}
        return self.api.method_post(uri, data=data)

    def add_list_member(self, list, name, address, description, vars):
        uri = 'lists/%s/members' % list # ex dev@samples.mailgun.org
        data={
            'subscribed': True,
            'address': address,
            'name': name,
            'description': description,
            'vars': vars # vars ex. '{"age": 26}'
        }
        return self.api.method_post(uri, data=data)

    def update_list_member(self, list, name, address, description, vars, subscribed=True):
        uri = 'lists/%s/members' % list # ex dev@samples.mailgun.org
        data={
            'subscribed': subscribed,
            'address': address,
            'name': name,
            'description': description,
            'vars': vars # vars ex. '{"age": 26}'
        }
        return self.api.method_put(uri, data=data)

    def get_logs(self, dom_name, start_time, limit=100, ascending='yes', pretty='yes', sender=None, receiver=None):
        uri = "/%s/events" % dom_name
        
        params={"begin"       : start_time, # "Fri, 3 May 2013 09:00:00 -0000"
                "ascending"   : ascending,
                "limit"       : limit,
                "pretty"      : pretty,
                "f:recipient" : "joe@example.com"}
        if sender:
            params['f:recipient'] = sender
        if receiver:
            params['t:recipient'] = receiver

        return self.api.method_get(uri, params=params)

    def get_stats(self, dom_name, events, skip, limit):
        uri = "/%s/stats" % dom_name,
        params={"event": events, # ex ["sent", "opened"]
                "skip": skip,
                "limit": limit}
        return self.api.method_get(uri, params=params)

    def create_campaign(self, dom_name, name, campaign_id):
        uri = "/%s/campaigns" % dom_name
        data={
            'name': name,
            'id': campaign_id
        }
        return self.api.method_post(uri, data=data)

    def send_campaign_message(self, dom_name, sender, recipients, subject, text, campaign_id):
        uri = "/%s/messages" % dom_name
        data={
            "from": sender, # ex "Excited User <me@samples.mailgun.org>"
            "to": recipients, # ex ["baz@example.com"]
            "subject": subject,
            "text": text,
            "o:campaign": campaign_id
        }
        return self.api.method_post(uri, data=data)

    def get_campaign_stats(self, dom_name, campaign_id, limit=20, group_by='daily_hour'):
        uri = "/%s/campaigns/%s/stats?groupby=%s&limit=%s" % (dom_name, campaign_id,
            group_by, limit)
        return self.api.method_get(uri)

    def get_mailboxes(self, dom_name):
        uri = "/%s/mailboxes", dom_name
        return self.api.method_get(uri)

    def create_mailbox(self, dom_name, mailbox_address, password):
        uri = "/%s/mailboxes" % dom_name
        data={
            "mailbox": mailbox_address, # ex "alice@samples.mailgun.org"
            "password": password
        }
        return self.api.method_post(uri, data=data)

    def change_mailbox_password(self, dom_name, mailbox_name, password):
        uri = "/%s/mailboxes/%s" % (dom_name, mailbox_name)
        data={"password": password}
        return self.api.method_put(uri, data=data)

    def delete_mailbox(self, dom_name, mailbox_name):
        uri = "/%s/mailboxes/%s" % (dom_name, mailbox_name)
        return self.api.method_delete(uri)

    def list_webhooks(self, dom_name):
        uri = "/domains/%s/webhooks" % dom_name
        return self.api.method_get(uri)

    def get_webhook(self, dom_name, webhook):
        uri = "/domains/%s/webhooks/%s"
        return self.api.method_get(uri)

    def create_webhook(self, dom_name, webhook, url):
        uri = "/domains/%s/webhooks"
        data = {'id': webhook, 'url': url}
        return self.api.method_post(uri, data=data)

    def update_webhook(self, dom_name, webhook, url):
        uri = "/domains/%s/webhooks/%s" % webhook
        data = {'url': url}
        return self.api.method_put(uri, data=data)

    def delete_webhook(self, dom_name, webhook):
        uri = "/domains/%s/webhooks/%s" % webhook
        return self.api.method_delete(uri)


class MailgunClient(BaseClient):
    """
    This is the base client for creating and managing Mailgun.
    """

    def __init__(self, *args, **kwargs):
        super(MailgunClient, self).__init__(*args, **kwargs)
        self.name = "Mailgun"
        self.management_url = MAILGUN_API
        self.auth = ('api', self._manager.fetch_apikey())

    def _configure_manager(self):
        """
        Creates the Manager instance to handle networks.
        """
        self._manager = MailgunManager(self, resource_class=MailgunDomain,
                response_key="domain", plural_response_key="items", 
                uri_base="domains")


    def _create_body(self, name, label=None, cidr=None):
        """
        Update with body creation bits.
        """
        pass
        

    def _api_request(self, uri, method, **kwargs):
        """
        Uses requests to perform api request.
        """
        try:
            print "REQ", self.management_url + uri
            print "METHOD", method
            req = getattr(requests, method.lower())(self.management_url + uri,
                headers=HEADERS, auth=self.auth, **kwargs)
            
            print
            print req.text
            print
            response = req.json()
            code = req.status_code
        except requests.exceptions.RequestException as exc:
            # do something
            raise
        return code, response
