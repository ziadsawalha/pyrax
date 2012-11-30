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


class CloudDNSRecord(BaseResource):
    """
    This class represents a domain record.
    """
    GET_DETAILS = False


class CloudDNSDomain(BaseResource):
    """
    This class represents a DNS domain.
    """
    def delete(self, delete_subdomains=False):
        """
        Deletes this domain and all of its resource records. If this domain
        has subdomains, each subdomain will now become a root domain.
        If you wish to also delete any subdomains, pass True to 'delete_subdomains'.
        """
        self.manager.delete(self, delete_subdomains=delete_subdomains)


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
        entry:
            - email address
            - ttl setting
            - comment
        """
        resp, body = self.manager.update_domain(self, emailAddress=emailAddress,
                ttl=ttl, comment=comment)
        return body


    def list_subdomains(self):
        """
        Returns a list of all subdomains for this domain.
        """
        resp, body = self.manager.list_subdomains(self)
        return body


    def list_records(self):
        """
        Returns a list of all records configured for this domain.
        """
        return self.manager.list_domain_records(self)


    def search_records(self, record_type, name=None, data=None):
        """
        Returns a list of all records configured for this domain that match
        the supplied search criteria.
        """
        return self.manager.search_records(self, record_type=record_type,
                name=name, data=data)


    def add_records(self, records):
        """
        Adds the records to this domain. Each record should be a dict with the
        following keys:
            type (required)
            name (required)
            data (required)
            ttl (optional)
            comment (optional)
            priority (required for MX and SRV records; forbidden otherwise)
        """
        self.manager.add_domain_records(self, records)



class CloudDNSManager(BaseManager):
    def __init__(self, api, resource_class=None, response_key=None,
            plural_response_key=None, uri_base=None):
        super(CloudDNSManager, self).__init__(api, resource_class=resource_class,
                response_key=response_key, plural_response_key=plural_response_key,
                uri_base=uri_base)


    def _get(self, uri):
        """
        Handles the communication with the API when getting
        a specific resource managed by this class.

        Because DNS returns a different format for the body,
        the BaseManager method must be overridden here.
        """
        # SLOW!!!!
#        uri = "%s?showRecords=true&showSubdomains=true" % uri
        uri = "%s?showRecords=true&showSubdomains=false" % uri
        _resp, body = self.api.method_get(uri)
        body["records"] = body.pop("recordsList").get("records", [])
        return self.resource_class(self, body, loaded=True)


    def _async_call(self, uri, body=None, method="GET", error_class=None,
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
            _resp, ret_body = api_method(uri, *args, **kwargs)
        else:
            _resp, ret_body = api_method(uri, body=body, *args, **kwargs)
        callbackURL = ret_body["callbackUrl"].split("/status/")[-1]
        massagedURL = "/status/%s?showDetails=true" % callbackURL
        start = time.time()
        while (ret_body["status"] == "RUNNING") and (time.time() - start < WAIT_LIMIT):
            _resp, ret_body= self.api.method_get(massagedURL)
        if error_class and (ret_body["status"] == "ERROR"):
            #This call will handle raising the error.
            self._process_async_error(ret_body, error_class)
        if has_response:
            ret = _resp, ret_body["response"]
        else:
            ret = _resp, ret_body
        return ret


    def _process_async_error(self, ret_body, error_class):
        """
        The DNS API does not return a consistent format for their error
        messages. This abstracts out the differences in order to present
        a single unified message in the exception to be raised.
        """
        def _fmt_error(err):
            # Remove the cumbersome Java-esque message
            details = err["details"].split(".")[-1].replace("\n", " ")
            if not details:
                details = err["message"]
            return "%s (%s)" % (details, err["code"])

        error = ret_body["error"]
        if "failedItems" in error:
            # Multi-error response
            faults = error["failedItems"]["faults"]
            msgs = [_fmt_error(fault) for fault in faults]
            msg = "\n".join(msgs)
        else:
            msg = _fmt_error(error)
        raise error_class(msg)


    def _create(self, uri, body, records=None, subdomains=None,
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
        _resp, ret_body = self._async_call(uri, body=body, method="POST",
                error_class=exc.DomainCreationFailed)
        response_body = ret_body[self.response_key][0]
        return self.resource_class(self, response_body)


    def delete(self, domain, delete_subdomains=False):
        """
        Deletes the specified domain and all of its resource records. If the
        domain has subdomains, each subdomain will now become a root domain.
        If you wish to also delete any subdomains, pass True to 'delete_subdomains'.
        """
        uri = "/%s/%s" % (self.uri_base, utils.get_id(domain))
        if delete_subdomains:
            uri = "%s?deleteSubdomains=true" % uri
        _resp, ret_body = self._async_call(uri, method="DELETE",
                error_class=exc.DomainDeletionFailed, has_response=False)


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
        uri = "/domains/%s/export" % utils.get_id(domain)
        resp, ret_body = self._async_call(uri, method="GET", error_class=exc.NotFound)
        return resp, ret_body


    def import_domain(self, domain_data):
        """
        Takes a string in the BIND 9 format and creates a new domain. See the
        'export_domain()' method for a description of the format.
        """
        uri = "/domains/import"
        body = {"domains" : [{
                "contentType" : "BIND_9",
                "contents" : domain_data,
                }]}
        resp, ret_body = self._async_call(uri, method="POST", body=body,
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
        uri = "/domains/%s" % utils.get_id(domain)
        body = {"comment" : comment,
                "ttl" : ttl,
                "emailAddress" : emailAddress,
                }
        none_keys = [key for key, val in body.items()
                if val is None]
        for none_key in none_keys:
            body.pop(none_key)
        resp, ret_body = self._async_call(uri, method="PUT", body=body,
                error_class=exc.DomainUpdateFailed, has_response=False)
        return resp, ret_body


    def list_subdomains(self, domain):
        """
        Returns a list of all subdomains of the specified domain.
        """
        uri = "/domains/%s/subdomains" % utils.get_id(domain)
        resp, body = self.api.method_get(uri)
        domains = body.get("domains", [])
        return [CloudDNSDomain(self, domain, loaded=False)
                for domain in domains if domain]


    def list_domain_records(self, domain):
        """
        Returns a list of all records configured for the specified domain.
        """
        uri = "/domains/%s/records" % utils.get_id(domain)
        resp, body = self.api.method_get(uri)
        records = body.get("records", [])
        return [CloudDNSRecord(self, record, loaded=False)
                for record in records if record]


    def search_domain_records(self, domain, record_type, name=None, data=None):
        """
        Returns a list of all records configured for the specified domain that match
        the supplied search criteria.
        """
        search_params = []
        if name:
            search_params.append("name=%s" % name)
        if data:
            search_params.append("data=%s" % data)
        query_string = "&".join(search_params)
        uri = "/domains/%s/records?type=%s" % (utils.get_id(domain), record_type)
        if query_string:
            uri = "%s&%s" % (uri, query_string)
        resp, body = self.api.method_get(uri)
        records = body.get("records", [])
        return [CloudDNSRecord(self, record, loaded=False)
                for record in records if record]


    def add_domain_records(self, domain, records):
        """
        Adds the records to this domain. Each record should be a dict with the
        following keys:
            type (required)
            name (required)
            data (required)
            ttl (optional)
            comment (optional)
            priority (required for MX and SRV records; forbidden otherwise)
        """
        if isinstance(records, dict):
            # Single record passed
            records = [records]
        uri = "/domains/%s/records" % utils.get_id(domain)
        body = {"records": records}
        resp, ret_body = self._async_call(uri, method="POST", body=body,
                error_class=exc.DomainRecordAdditionFailed, has_response=False)
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


    def delete_domain(self, domain, delete_subdomains=False):
        """
        Deletes the specified domain and all of its resource records. If the
        domain has subdomains, each subdomain will now become a root domain.
        If you wish to also delete any subdomains, pass True to 'delete_subdomains'.
        """
        self._manager.delete(domain, delete_subdomains=delete_subdomains)


    def list_subdomains(self, domain):
        """
        Returns a list of all subdomains for the specified domain.
        """
        return self._manager.list_subdomains(domain)


    def list_domain_records(self, domain):
        """
        Returns a list of all records configured for the specified domain.
        """
        return self._manager.list_domain_records(domain)


    def search_domain_records(self, domain, record_type, name=None, data=None):
        """
        Returns a list of all records configured for the specified domain that match
        the supplied search criteria.
        """
        return self._manager.search_domain_records(domain, record_type=record_type,
                name=name, data=data)


    def add_domain_records(self, domain, records):
        """
        Adds the records to this domain. Each record should be a dict with the
        following keys:
            type (required)
            name (required)
            data (required)
            ttl (optional)
            comment (optional)
            priority (required for MX and SRV records; forbidden otherwise)
        """
        return self._manager.add_domain_records(domain, records)


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
