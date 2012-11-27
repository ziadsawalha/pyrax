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
from pyrax.client import BaseClient
import pyrax.exceptions as exc
from pyrax.manager import BaseManager
from pyrax.resource import BaseResource
import pyrax.utils as utils


def assure_instance(fnc):
    @wraps(fnc)
    def _wrapped(self, instance, *args, **kwargs):
        if not isinstance(instance, CloudDatabaseInstance):
            # Must be the ID
            instance = self._manager.get(instance)
        return fnc(self, instance, *args, **kwargs)
    return _wrapped


class CloudDNSDomain(BaseResource):
    """
    This class represents the available instance configurations, or 'flavors',
    which you use to define the memory and CPU size of your instance. These
    objects are read-only.
    """
    pass


class CloudDNSClient(BaseClient):
    """
    This is the primary class for interacting with Cloud Databases.
    """
    def _configure_manager(self):
        """
        Creates a manager to handle the instances, and another
        to handle flavors.
        """
        self._manager = BaseManager(self, resource_class=CloudDNSDomain,
               response_key="domain", uri_base="domains")


    def _create_body(self, name, emailAddress, ttl=3600, comment=None):
        """
        """
        body = {"domain": {
                "name": name,
                "emailAddress": emailAddress,
                "ttl": ttl,
                "comment": comment,
                }}
        return body
