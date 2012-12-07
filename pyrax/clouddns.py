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
import json
import time

import pyrax
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


    def changes_since(self, date_or_datetime):
        """
        Get the changes for this domain since the specified date/datetime.
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
        return self.manager.changes_since(self, date_or_datetime)


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
        return self.manager.export_domain(self)


    def update(self, emailAddress=None, ttl=None, comment=None):
        """
        Provides a way to modify the following attributes of a domain
        entry:
            - email address
            - ttl setting
            - comment
        """
        return self.manager.update_domain(self, emailAddress=emailAddress,
                ttl=ttl, comment=comment)


    def list_subdomains(self):
        """
        Returns a list of all subdomains for this domain.
        """
        return self.manager.list_subdomains(self)


    def list_records(self):
        """
        Returns a list of all records configured for this domain.
        """
        return self.manager.list_records(self)


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
        self.manager.add_records(self, records)

    #Create an alias, so that adding a single record is more intuitive
    add_record = add_records


    def update_record(self, record, name, data=None, priority=None,
            ttl=None, comment=None):
        """
        Modifie an existing record for this domain.
        """
        return self.manager.update_record(self, record, name, data=data,
                priority=priority, ttl=ttl, comment=comment)


    def delete_record(self, record):
        """
        Deletes an existing record for this domain.
        """
        return self.manager.delete_record(self, record)



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
        try:
            body = json.loads(body)
        except Exception:
            pass
        return ret


    def _process_async_error(self, ret_body, error_class):
        """
        The DNS API does not return a consistent format for their error
        messages. This abstracts out the differences in order to present
        a single unified message in the exception to be raised.
        """
        def _fmt_error(err):
            # Remove the cumbersome Java-esque message
#            details = err["details"].split(".")[-1].replace("\n", " ")
            details = err["details"].replace("\n", " ")
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
            nm = kwargs["name"]
            uri = "/%s?name=%s" % (self.uri_base, nm)
            matches = self._list(uri)
            return [match for match in matches
                if match.name == nm] 
        else:
            return super(CloudDNSManager, self).findall(**kwargs)


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
        resp, body = self.api.method_get(uri)
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
        uri = "/domains/%s/export" % utils.get_id(domain)
        resp, ret_body = self._async_call(uri, method="GET", error_class=exc.NotFound)
        return ret_body.get("contents", "")


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
        return ret_body


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
        return ret_body


    def list_subdomains(self, domain):
        """
        Returns a list of all subdomains of the specified domain.
        """
        # The commented-out uri is the official API, but it is
        # horribly slow.
#        uri = "/domains/%s/subdomains" % utils.get_id(domain)
        uri = "/domains?name=%s" % domain.name
        resp, body = self.api.method_get(uri)
        subdomains = body.get("domains", [])
        return [CloudDNSDomain(self, subdomain, loaded=False)
                for subdomain in subdomains
                if subdomain["id"] != domain.id]


    def list_records(self, domain):
        """
        Returns a list of all records configured for the specified domain.
        """
        uri = "/domains/%s/records" % utils.get_id(domain)
        resp, body = self.api.method_get(uri)
        records = body.get("records", [])
        return [CloudDNSRecord(self, record, loaded=False)
                for record in records if record]


    def search_records(self, domain, record_type, name=None, data=None):
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


    def add_records(self, domain, records):
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
        return ret_body
        

    def update_record(self, domain, record, name, data=None, priority=None,
            ttl=None, comment=None):
        """
        Modifies an existing record for a domain.
        """
        rec_id = utils.get_id(record)
        uri = "/domains/%s/records/%s" % (utils.get_id(domain), rec_id)
        body = {"name": name}
        all_opts = (("data", data), ("priority", priority), ("ttl", ttl), ("comment", comment))
        opts = [(k, v) for k, v in all_opts if v is not None]
        body.update(dict(opts))
        resp, ret_body = self._async_call(uri, method="PUT", body=body,
                error_class=exc.DomainRecordUpdateFailed, has_response=False)
        return ret_body


    def delete_record(self, domain, record):
        """
        Deletes an existing record for a domain.
        """
        uri = "/domains/%s/records/%s" % (utils.get_id(domain), utils.get_id(record))
        resp, ret_body = self._async_call(uri, method="DELETE",
                error_class=exc.DomainRecordDeletionFailed, has_response=False)
        return ret_body


    def _get_ptr_details(self, device, device_type):
        """
        Takes a device and device type and returns the corresponding HREF link
        and service name for use with PTR record management.
        """
        if device_type.lower().startswith("load"):
            ep = pyrax._get_service_endpoint("load_balancer")
            svc = "loadbalancers"
            svc_name = "cloudLoadBalancers"
        else:
            ep = pyrax._get_service_endpoint("compute")
            svc = "servers"
            svc_name = "cloudServersOpenStack"
        href = "%s/%s/%s" % (ep, svc, utils.get_id(device))
        return (href, svc_name)


    def list_ptr_records(self, device, device_type="server"):
        href, svc_name = self._get_ptr_details(device, device_type)
        uri = "/rdns/%s?href=%s" % (svc_name, href)
        try:
            resp, ret_body = self.api.method_get(uri)
        except exc.NotFound:
            return []
        return ret_body["records"]


    def add_ptr_records(self, records, device, device_type="server"):
        """
        Adds one or more PTR records to the specified device.
        """
        href, svc_name = self._get_ptr_details(device, device_type)
        if not isinstance(records, (list, tuple)):
            records = [records]
        body = {"recordsList": {
                   "records": records},
                "link": {
                    "content": "",
                    "href": href,
                    "rel": svc_name,
                }}
        uri = "/rdns"
        resp, ret_body = self.api.method_post(uri, body=body)


    def update_ptr_record(self, record, device, device_type="server",
            domain_name=None, data=None, ttl=None, comment=None):
        """
        Updates a PTR record with the supplied values.
        """
        href, svc_name = self._get_ptr_details(device, device_type)
        rec = {"name": domain_name,
              "id": utils.get_id(record),
              "type": "PTR",
              "data": data,
            }
        if ttl is not None:
            # Minimum TTL is 300 seconds
            rec["ttl"] = max(300, ttl)
        if comment is not None:
            # Maximum comment length is 160 chars
            rec["comment"] = comment[:160]
        body = {"recordsList": {
                   "records": [rec]},
                "link": {
                    "content": "",
                    "href": href,
                    "rel": svc_name,
                }}
        uri = "/rdns"
        resp, ret_body = self.api.method_put(uri, body=body)
        return ret_body


    def delete_ptr_records(self, device, device_type="server", ip_address=None):
        """
        Deletes the PTR records for the specified device. If 'ip_address' is supplied,
        only the PTR records with that IP address will be deleted.
        """
        href, svc_name = self._get_ptr_details(device, device_type)
        uri = "/rdns/%s?href=%s" % (svc_name, href)
        if ip_address:
            uri = "%s&ip=%s" % (uri, ip_address)
        resp, ret_body = self.api.method_delete(uri)
        return ret_body



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


    @assure_domain
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
        return domain.changes_since(date_or_datetime)


    @assure_domain
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
        return domain.export()


    def import_domain(self, domain_data):
        """
        Takes a string in the BIND 9 format and creates a new domain. See the
        'export_domain()' method for a description of the format.
        """
        return self._manager.import_domain(domain_data)


    @assure_domain
    def update_domain(self, domain, emailAddress=None, ttl=None, comment=None):
        """
        Provides a way to modify the following attributes of a domain
        record:
            - email address
            - ttl setting
            - comment
        """
        return domain.update(emailAddress=emailAddress,
                ttl=ttl, comment=comment)


    @assure_domain
    def delete(self, domain, delete_subdomains=False):
        """
        Deletes the specified domain and all of its resource records. If the
        domain has subdomains, each subdomain will now become a root domain.
        If you wish to also delete any subdomains, pass True to 'delete_subdomains'.
        """
        domain.delete(delete_subdomains=delete_subdomains)


    @assure_domain
    def list_subdomains(self, domain):
        """
        Returns a list of all subdomains for the specified domain.
        """
        return domain.list_subdomains()


    @assure_domain
    def list_records(self, domain):
        """
        Returns a list of all records configured for the specified domain.
        """
        return domain.list_records()


    @assure_domain
    def search_records(self, domain, record_type, name=None, data=None):
        """
        Returns a list of all records configured for the specified domain that match
        the supplied search criteria.
        """
        return domain.search_records(record_type=record_type,
                name=name, data=data)


    @assure_domain
    def add_records(self, domain, records):
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
        return domain.add_records(records)

    #Create an alias, so that adding a single record is more intuitive
    add_record = add_records


    @assure_domain
    def update_record(self, domain, record, name, data=None, priority=None,
            ttl=None, comment=None):
        """
        Modifies an existing record for a domain.
        """
        return domain.update_record(record, name, data=data,
                priority=priority, ttl=ttl, comment=comment)


    @assure_domain
    def delete_record(self, domain, record):
        return domain.delete_record(record)


    def list_ptr_records(self, device, device_type="server"):
        return self._manager.list_ptr_records(device, device_type=device_type)


    def add_ptr_records(self, records, device, device_type="server"):
        """
        Adds one or more PTR records to the specified device.
        """
        return self._manager.add_ptr_records(records, device, device_type=device_type)


    def update_ptr_record(self, record, device, device_type="server", domain_name=None,
            data=None, ttl=None, comment=None):
        """
        Updates a PTR record with the supplied values.
        """
        return self._manager.update_ptr_record(record, device, device_type=device_type,
                domain_name=domain_name, data=data, ttl=ttl, comment=comment)


    def delete_ptr_records(self, device, device_type="server", ip_address=None):
        """
        Deletes the PTR records for the specified device. If 'ip_address' is supplied,
        only the PTR records with that IP address will be deleted.
        """
        return self._manager.delete_ptr_records(device, device_type=device_type,
                ip_address=ip_address)


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
