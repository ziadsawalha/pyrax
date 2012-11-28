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


class CloudDNSDomain(BaseResource):
    """
    This class represents the available instance configurations, or 'flavors',
    which you use to define the memory and CPU size of your instance. These
    objects are read-only.
    """
    pass


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


    def _create(self, url, body, return_none=False, return_raw=False, **kwargs):
        """
        Handles the communication with the API when creating a new
        resource managed by this class.

        Since DNS works completely differently for create(), this method
        overrides the default BaseManager behavior.
        """
        self.run_hooks("modify_body_for_create", body, **kwargs)
        _resp, body = self.api.method_post(url, body=body)
        if return_none:
            # No response body
            return
        callbackURL = body["callbackUrl"].split("/status/")[-1]
        massagedURL = "/status/%s?showDetails=true" % callbackURL
        start = time.time()
        while (body["status"] == "RUNNING") and (time.time() - start < WAIT_LIMIT):
            _resp, body= self.api.method_get(massagedURL)
        if body["status"] == "ERROR":
            err = body["error"]
            msg = "%s (%s)" % (err["details"], err["code"])
            raise exc.DomainCreationFailed(msg)
        response_body = body["response"][self.response_key][0]
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


    def get_absolute_limits(self):
        resp, body = self.method_get("/limits")
        absolute_limits = body.get("limits", {}).get("absolute")
        return absolute_limits


    def get_rate_limits(self):
        resp, body = self.method_get("/limits")
        rate_limits = body.get("limits", {}).get("rate")
        ret = []
        for rate_limit in rate_limits:
            limits = rate_limit["limit"]
            uri_limits = {"uri": rate_limit["uri"],
                    "limits": limits}
            ret.append(uri_limits)
        return ret
