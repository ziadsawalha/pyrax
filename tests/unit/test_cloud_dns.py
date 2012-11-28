#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import unittest

from mock import patch
from mock import MagicMock as Mock

from pyrax.manager import BaseManager
from pyrax.clouddns import CloudDNSClient
from pyrax.clouddns import CloudDNSManager
from pyrax.clouddns import CloudDNSDomain
import pyrax.exceptions as exc
import pyrax.utils as utils

from tests.unit import fakes

example_uri = "http://example.com"


class CloudDNSTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(CloudDNSTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.client = fakes.FakeDNSClient()

    def tearDown(self):
        self.client = None

    def test_manager_get(self):
        ret_body = {"recordsList": {
                "records": [{
                "accountId": "728829",
                "created": "2012-09-21T21:32:27.000+0000",
                "emailAddress": "me@example.com",
                "id": "3448214",
                "name": "example.com",
                "updated": "2012-09-21T21:35:45.000+0000"
                }]}}
        mgr = self.client._manager
        mgr.api.method_get = Mock(return_value=(None, ret_body))
        dom = mgr._get("fake")
        self.assertTrue(isinstance(dom, CloudDNSDomain))


    def test_manager_create(self):
        clt = self.client
        mgr = clt._manager
        ret_body = {"callbackUrl": example_uri,
                "status": "RUNNING"}
        mgr.api.method_post = Mock(return_value=(None, ret_body))
        stat_body = {"status": "complete",
                "response": {mgr.response_key: [{
                "accountId": "728829",
                "created": "2012-09-21T21:32:27.000+0000",
                "emailAddress": "me@example.com",
                "id": "3448214",
                "name": "example.com",
                "updated": "2012-09-21T21:35:45.000+0000"
                }]}}
        mgr.api.method_get = Mock(return_value=(None, stat_body))
        dom = mgr._create("fake", {})
        self.assertTrue(isinstance(dom, CloudDNSDomain))


    def test_manager_create_error(self):
        clt = self.client
        mgr = clt._manager
        ret_body = {"callbackUrl": example_uri,
                "status": "RUNNING"}
        mgr.api.method_post = Mock(return_value=(None, ret_body))
        stat_body = {"status": "ERROR",
                "error": {
                    "details": "fail",
                    "code": 666}}
        mgr.api.method_get = Mock(return_value=(None, stat_body))
        self.assertRaises(exc.DomainCreationFailed, mgr._create, "fake", {}) 

    def test_manager_findall(self):
        clt = self.client
        mgr = clt._manager
        mgr._list = Mock()
        mgr.findall(name="fake")
        mgr._list.assert_called_once_with("/domains?name=fake")

    def test_manager_findall_default(self):
        clt = self.client
        mgr = clt._manager
        BaseManager.findall = Mock()
        mgr.findall(foo="bar")
        BaseManager.findall.assert_called_once_with(foo="bar")

    def test_create_body(self):
        clt = self.client
        fake_name = utils.random_name()
        body = clt._create_body(fake_name, "fake@fake.com")
        self.assertEqual(body["domains"][0]["name"], fake_name)



if __name__ == "__main__":
    unittest.main()
