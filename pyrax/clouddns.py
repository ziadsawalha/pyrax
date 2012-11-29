#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2012 Rackspace

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

from functools import wraps
import time

from pyrax.client import BaseClient
import pyrax.exceptions as exc
from pyrax.manager import BaseManager
from pyrax.resource import BaseResource
import pyrax.utils as utils

# How long (in seconds) to wait for a response from async operations
WAIT_LIMIT = 5


def assure_domain(fnc):
    @wraps(fnc)
    def _wrapped(self, domain, *args, **kwargs):
        if not isinstance(domain, CloudDNSDomain):
            # Must be the ID
            domain = self._manager.get(domain)
        return fnc(self, domain, *args, **kwargs)
    return _wrapped


class CloudDNSDomain(BaseResource):
    """
    This class represents the available instance configurations, or 'flavors',
    which you use to define the memory and CPU size of your instance. These
    objects are read-only.
    """
    def export(self):
        """
        Provides the BIND (Berkeley Internet Name Domain) 9 formatted contents
        of the requested domain. This call is for a single domain only, and as such,
        does not provide subdomain information.

        Sample export:
            {u'accountId': 000000,
             u'contentType': u'BIND_9',
             u'contents': u'example.com.\t3600\tIN\tSOA\tns.rackspace.com. foo@example.com. 1354202974 21600 3600 1814400 500'
                'example.com.\t3600\tIN\tNS\tdns1.stabletransit.com.'
                'example.com.\t3600\tIN\tNS\tdns2.stabletransit.com.',
             u'id': 1111111}
        """
        resp, body = self.manager.export_domain(self)
        return body


    def update(self, emailAddress=None, ttl=None, comment=None):
        """
        Provides a way to modify the following attributes of a domain
        record:
            - email address
            - ttl setting
            - comment
        """
        resp, body = self.manager.update_domain(self, emailAddress=emailAddress,
                ttl=ttl, comment=comment)
        return body


class CloudDNSManager(BaseManager):
    def _get(self, url):
        """
        Handles the communication with the API when getting
        a specific resource managed by this class.

        Because DNS returns a different format for the body,
        the BaseManager method must be overridden here.
        """
        url = "%s?showRecords=true&showSubdomains=true" % url
        _resp, body = self.api.method_get(url)
        body["records"] = body.pop("recordsList").get("records", [])
        return self.resource_class(self, body, loaded=True)


    def _async_call(self, url, body=None, method="GET", error_class=None,
            has_response=True, *args, **kwargs):
        """
        Handles asynchronous call/responses for the DNS API.

        Returns the response headers and body if the call was successful.
        If an error status is returned, and the 'error_class' parameter is
        specified, that class of error will be raised with the details from
        the response. If no error class is specified, the response headers
        and body will be returned to the calling method, which will have
        to handle the result.
        """
        api_methods = {
                "GET": self.api.method_get,
                "POST": self.api.method_post,
                "PUT": self.api.method_put,
                "DELETE": self.api.method_delete,
                }
        api_method = api_methods[method]
        if body is None:
            _resp, ret_body = api_method(url, *args, **kwargs)
        else:
            _resp, ret_body = api_method(url, body=body, *args, **kwargs)
        callbackURL = ret_body["callbackUrl"].split("/status/")[-1]
        massagedURL = "/status/%s?showDetails=true" % callbackURL
        start = time.time()
        while (ret_body["status"] == "RUNNING") and (time.time() - start < WAIT_LIMIT):
            _resp, ret_body= self.api.method_get(massagedURL)
        if error_class and (ret_body["status"] == "ERROR"):
            err = ret_body["error"]
            msg = "%s (%s)" % (err["details"], err["code"])
            raise error_class(msg)
        if has_response:
            ret = _resp, ret_body["response"]
        else:
            ret = _resp, ret_body
        return ret


    def _create(self, url, body, records=None, subdomains=None,
            return_none=False, return_raw=False, **kwargs):
        """
        Handles the communication with the API when creating a new
        resource managed by this class.

        Since DNS works completely differently for create() than the other
        APIs, this method overrides the default BaseManager behavior.

        If 'records' are supplied, they should be a list of dicts. Each
        record dict should have the following format:

            {"name" : "example.com",
            "type" : "A",
            "data" : "192.0.2.17",
            "ttl" : 86400}

        If 'subdomains' are supplied, they should be a list of dicts. Each
        subdomain dict should have the following format:

            {"name" : "sub1.example.com",
             "comment" : "1st sample subdomain",
             "emailAddress" : "sample@rackspace.com"}
        """
        self.run_hooks("modify_body_for_create", body, **kwargs)
        _resp, ret_body = self._async_call(url, body=body, method="POST",
                error_class=exc.DomainCreationFailed)
        response_body = ret_body[self.response_key][0]
        return self.resource_class(self, response_body)


    def findall(self, **kwargs):
        """
        Finds all items with attributes matching ``**kwargs``.

        Normally this isn't very efficient, since the default action is to
        load the entire list and then filter on the Python side, but the DNS
        API provides a more efficient search option when filtering on name.
        So if the filter is on name, use that; otherwise, use the default.
        """
        if (len(kwargs) == 1) and ("name" in kwargs):
            # Filtering on name; use the more efficient method.
            uri = "/%s?name=%s" % (self.uri_base, kwargs["name"])
            return self._list(uri)
        else:
            return super(CloudDNSManager, self).findall(**kwargs)


    def export_domain(self, domain):
        """
        Provides the BIND (Berkeley Internet Name Domain) 9 formatted contents
        of the requested domain. This call is for a single domain only, and as such,
        does not provide subdomain information.

        Sample export:
            {u'accountId': 000000,
             u'contentType': u'BIND_9',
             u'contents': u'example.com.\t3600\tIN\tSOA\tns.rackspace.com. foo@example.com. 1354202974 21600 3600 1814400 500'
                'example.com.\t3600\tIN\tNS\tdns1.stabletransit.com.'
                'example.com.\t3600\tIN\tNS\tdns2.stabletransit.com.',
             u'id': 1111111}
        """
        url = "/domains/%s/export" % utils.get_id(domain)
        resp, ret_body = self._async_call(url, method="GET", error_class=exc.NotFound)
        return resp, ret_body


    def import_domain(self, domain_data):
        """
        Takes a string in the BIND 9 format and creates a new domain. See the
        'export_domain()' method for a description of the format.
        """
        url = "/domains/import"
        body = {"domains" : [{
                "contentType" : "BIND_9",
                "contents" : domain_data,
                }]}
        resp, ret_body = self._async_call(url, method="POST", body=body,
                error_class=exc.DomainCreationFailed)
        return resp, ret_body


    def update_domain(self, domain, emailAddress=None, ttl=None, comment=None):
        """
        Provides a way to modify the following attributes of a domain
        record:
            - email address
            - ttl setting
            - comment
        """
        if not any((emailAddress, ttl, comment)):
            raise exc.MissingDNSSettings("No settings provided to update_domain().")
        url = "/domains/%s" % utils.get_id(domain)
        body = {"comment" : comment,
                "ttl" : ttl,
                "emailAddress" : emailAddress,
                }
        none_keys = [key for key, val in body.items()
                if val is None]
        for none_key in none_keys:
            body.pop(none_key)
        resp, ret_body = self._async_call(url, method="PUT", body=body,
                error_class=exc.DomainUpdateFailed, has_response=False)
        return resp, ret_body



class CloudDNSClient(BaseClient):
    """
    This is the primary class for interacting with Cloud Databases.
    """
    def _configure_manager(self):
        """
        Creates a manager to handle the instances, and another
        to handle flavors.
        """
        self._manager = CloudDNSManager(self, resource_class=CloudDNSDomain,
               response_key="domains", plural_response_key="domains",
               uri_base="domains")


    def _create_body(self, name, emailAddress, ttl=3600, comment=None,
            subdomains=None, records=None):
        """
        Creates the appropriate dict for creating a new domain.
        """
        if subdomains is None:
            subdomains = []
        if records is None:
            records = []
        body = {"domains": [{
                "name": name,
                "emailAddress": emailAddress,
                "ttl": ttl,
                "comment": comment,
                "subdomains": {
                    "domains": subdomains
                    },
                "recordsList": {
                    "records": records
                    },
                }]}
        return body


    def changes_since(self, domain, date_or_datetime):
        """
        Get the changes for a domain since the specified date/datetime.
        The date can be one of:
            - a Python datetime object
            - a Python date object
            - a string in the format 'YYYY-MM-YY HH:MM:SS'
            - a string in the format 'YYYY-MM-YY'

        It returns a list of dicts, whose keys depend on the specific change
        that was made. A simple example of such a change dict:

            {u'accountId': 000000,
             u'action': u'update',
             u'changeDetails': [{u'field': u'serial_number',
               u'newValue': u'1354038941',
               u'originalValue': u'1354038940'},
              {u'field': u'updated_at',
               u'newValue': u'Tue Nov 27 17:55:41 UTC 2012',
               u'originalValue': u'Tue Nov 27 17:55:40 UTC 2012'}],
             u'domain': u'example.com',
             u'targetId': 00000000,
             u'targetType': u'Domain'}
        """
        domain_id = utils.get_id(domain)
        dt = utils.iso_time_string(date_or_datetime, show_tzinfo=True)
        uri = "/domains/%s/changes?since=%s" % (domain_id, dt)
        resp, body = self.method_get(uri)
        return body.get("changes", [])


    def export_domain(self, domain):
        """
        Provides the BIND (Berkeley Internet Name Domain) 9 formatted contents
        of the requested domain. This call is for a single domain only, and as such,
        does not provide subdomain information.

        Sample export:
            {u'accountId': 000000,
             u'contentType': u'BIND_9',
             u'contents': u'example.com.\t3600\tIN\tSOA\tns.rackspace.com. foo@example.com. 1354202974 21600 3600 1814400 500'
                'example.com.\t3600\tIN\tNS\tdns1.stabletransit.com.'
                'example.com.\t3600\tIN\tNS\tdns2.stabletransit.com.',
             u'id': 1111111}
        """
        resp, body = self._manager.export_domain(domain)
        return body


    def import_domain(self, domain_data):
        """
        Takes a string in the BIND 9 format and creates a new domain. See the
        'export_domain()' method for a description of the format.
        """
        resp, body = self._manager.import_domain(domain_data)
        return body


    def update_domain(self, domain, emailAddress=None, ttl=None, comment=None):
        """
        Provides a way to modify the following attributes of a domain
        record:
            - email address
            - ttl setting
            - comment
        """
        resp, body = self._manager.update_domain(domain, emailAddress=emailAddress,
                ttl=ttl, comment=comment)


    def get_absolute_limits(self):
        """
        Returns a dict with the absolute limits for the current account.
        """
        resp, body = self.method_get("/limits")
        absolute_limits = body.get("limits", {}).get("absolute")
        return absolute_limits


    def get_rate_limits(self):
        """
        Returns a dict with the current rate limit information for domain
        and status requests.
        """
        resp, body = self.method_get("/limits")
        rate_limits = body.get("limits", {}).get("rate")
        ret = []
        for rate_limit in rate_limits:
            limits = rate_limit["limit"]
            uri_limits = {"uri": rate_limit["uri"],
                    "limits": limits}
            ret.append(uri_limits)
        return ret
