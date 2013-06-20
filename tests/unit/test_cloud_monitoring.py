#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import unittest

from mock import patch
from mock import MagicMock as Mock

import pyrax.cloudnetworks
from pyrax.cloudmonitoring import CloudMonitorClient
from pyrax.cloudmonitoring import _params_to_dict

import pyrax.exceptions as exc
import pyrax.utils as utils

from tests.unit import fakes



class CloudMonitoringTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(CloudMonitoringTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.client = fakes.FakeCloudMonitorClient()

    def tearDown(self):
        self.client = None

    def test_params_to_dict(self):
        val = utils.random_name()
        local = {"foo": val, "bar": None, "baz": True}
        params = ("foo", "bar")
        expected = {"foo": val}
        ret = _params_to_dict(params, {}, local)
        self.assertEqual(ret, expected)



if __name__ == "__main__":
    unittest.main()
