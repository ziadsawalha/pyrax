#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import random
import unittest

from mock import patch
from mock import MagicMock as Mock

import pyrax.cloudnetworks
from pyrax.cloudmonitoring import CloudMonitorCheck
from pyrax.cloudmonitoring import CloudMonitorNotificationType
from pyrax.cloudmonitoring import _params_to_dict

import pyrax.exceptions as exc
import pyrax.utils as utils

from tests.unit import fakes



class CloudMonitoringTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(CloudMonitoringTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.client = fakes.FakeCloudMonitorClient()
        self.entity = fakes.FakeCloudMonitorEntity()

    def tearDown(self):
        self.client = None

    def test_params_to_dict(self):
        val = utils.random_name()
        local = {"foo": val, "bar": None, "baz": True}
        params = ("foo", "bar")
        expected = {"foo": val}
        ret = _params_to_dict(params, {}, local)
        self.assertEqual(ret, expected)

    def test_entity_update(self):
        ent = self.entity
        ent.manager.update_entity = Mock()
        agent = utils.random_name()
        metadata = {"fake": utils.random_name()}
        ent.update(agent=agent, metadata=metadata)
        ent.manager.update_entity.assert_called_once_with(ent, agent=agent,
                metadata=metadata)

    def test_entity_list_checks(self):
        ent = self.entity
        ent.manager.list_checks = Mock()
        ent.list_checks()
        ent.manager.list_checks.assert_called_once_with(ent)

    def test_entity_delete_check(self):
        ent = self.entity
        ent.manager.delete_check = Mock()
        check = utils.random_name()
        ent.delete_check(check)
        ent.manager.delete_check.assert_called_once_with(ent, check)

    def test_entity_list_metrics(self):
        ent = self.entity
        ent.manager.list_metrics = Mock()
        check = utils.random_name()
        ent.list_metrics(check)
        ent.manager.list_metrics.assert_called_once_with(ent, check)

    def test_entity_get_metric_data_points(self):
        ent = self.entity
        ent.manager.get_metric_data_points = Mock()
        check = utils.random_name()
        metric = utils.random_name()
        start = utils.random_name()
        end = utils.random_name()
        points = utils.random_name()
        resolution = utils.random_name()
        stats = utils.random_name()
        ent.get_metric_data_points(check, metric, start, end, points=points,
                resolution=resolution, stats=stats)
        ent.manager.get_metric_data_points.assert_called_once_with(ent, check,
                metric, start, end, points=points, resolution=resolution,
                stats=stats)

    def test_entity_create_alarm(self):
        ent = self.entity
        ent.manager.create_alarm = Mock()
        check = utils.random_name()
        np = utils.random_name()
        criteria = utils.random_name()
        disabled = random.choice((True, False))
        label = utils.random_name()
        name = utils.random_name()
        metadata = utils.random_name()
        ent.create_alarm(check, np, criteria=criteria, disabled=disabled,
                label=label, name=name, metadata=metadata)
        ent.manager.create_alarm.assert_called_once_with(ent, check, np,
                criteria=criteria, disabled=disabled, label=label, name=name,
                metadata=metadata)

    def test_entity_update_alarm(self):
        ent = self.entity
        ent.manager.update_alarm = Mock()
        alarm = utils.random_name()
        criteria = utils.random_name()
        disabled = random.choice((True, False))
        label = utils.random_name()
        name = utils.random_name()
        metadata = utils.random_name()
        ent.update_alarm(alarm, criteria=criteria, disabled=disabled,
                label=label, name=name, metadata=metadata)
        ent.manager.update_alarm.assert_called_once_with(ent, alarm,
                criteria=criteria, disabled=disabled, label=label, name=name,
                metadata=metadata)

    def test_entity_list_alarms(self):
        ent = self.entity
        ent.manager.list_alarms = Mock()
        ent.list_alarms()
        ent.manager.list_alarms.assert_called_once_with(ent)

    def test_entity_get_alarm(self):
        ent = self.entity
        ent.manager.get_alarm = Mock()
        alarm = utils.random_name()
        ent.get_alarm(alarm)
        ent.manager.get_alarm.assert_called_once_with(ent, alarm)

    def test_entity_delete_alarm(self):
        ent = self.entity
        ent.manager.delete_alarm = Mock()
        alarm = utils.random_name()
        ent.delete_alarm(alarm)
        ent.manager.delete_alarm.assert_called_once_with(ent, alarm)

    def test_entity_name(self):
        ent = self.entity
        ent.label = utils.random_name()
        self.assertEqual(ent.label, ent.name)

    def test_notif_manager_create(self):
        clt = self.client
        mgr = clt._notification_manager
        clt.method_post = Mock(return_value=(None, None))
        ntyp = utils.random_name()
        label = utils.random_name()
        name = utils.random_name()
        details = utils.random_name()
        exp_uri = "/%s" % mgr.uri_base
        exp_body = {"label": label or name, "type": ntyp, "details": details}
        mgr.create(ntyp, label=label, name=name, details=details)
        clt.method_post.assert_called_once_with(exp_uri, body=exp_body)

    def test_notif_manager_test_notification_existing(self):
        clt = self.client
        mgr = clt._notification_manager
        clt.method_post = Mock(return_value=(None, None))
        ntf = utils.random_name()
        details = utils.random_name()
        exp_uri = "/%s/%s/test" % (mgr.uri_base, ntf)
        exp_body = None
        mgr.test_notification(notification=ntf, details=details)
        clt.method_post.assert_called_once_with(exp_uri, body=exp_body)

    def test_notif_manager_test_notification(self):
        clt = self.client
        mgr = clt._notification_manager
        clt.method_post = Mock(return_value=(None, None))
        ntyp = utils.random_name()
        details = utils.random_name()
        exp_uri = "/test-notification"
        exp_body = {"type": ntyp, "details": details}
        mgr.test_notification(notification_type=ntyp, details=details)
        clt.method_post.assert_called_once_with(exp_uri, body=exp_body)

    def test_notif_manager_update_notification(self):
        clt = self.client
        mgr = clt._notification_manager
        clt.method_put = Mock(return_value=(None, None))
        ntf = fakes.FakeCloudMonitorNotification()
        ntf.type = utils.random_name()
        details = utils.random_name()
        exp_uri = "/%s/%s" % (mgr.uri_base, ntf.id)
        exp_body = {"type": ntf.type, "details": details}
        mgr.update_notification(ntf, details)
        clt.method_put.assert_called_once_with(exp_uri, body=exp_body)

    def test_notif_manager_update_notification_id(self):
        clt = self.client
        mgr = clt._notification_manager
        clt.method_put = Mock(return_value=(None, None))
        ntf = fakes.FakeCloudMonitorNotification()
        ntf.type = utils.random_name()
        details = utils.random_name()
        mgr.get = Mock(return_value=ntf)
        exp_uri = "/%s/%s" % (mgr.uri_base, ntf.id)
        exp_body = {"type": ntf.type, "details": details}
        mgr.update_notification(ntf.id, details)
        clt.method_put.assert_called_once_with(exp_uri, body=exp_body)

    def test_notif_manager_list_types(self):
        clt = self.client
        mgr = clt._notification_manager
        id_ = utils.random_name()
        ret_body = {"values": [{"id": id_}]}
        clt.method_get = Mock(return_value=(None, ret_body))
        ret = mgr.list_types()
        clt.method_get.assert_called_once_with("/notification_types")
        self.assertEqual(len(ret), 1)
        inst = ret[0]
        self.assertTrue(isinstance(inst, CloudMonitorNotificationType))
        self.assertEqual(inst.id, id_) 

    def test_notif_manager_get_type(self):
        clt = self.client
        mgr = clt._notification_manager
        id_ = utils.random_name()
        ret_body = {"id": id_}
        clt.method_get = Mock(return_value=(None, ret_body))
        ret = mgr.get_type(id_)
        exp_uri = "/notification_types/%s" % id_
        clt.method_get.assert_called_once_with(exp_uri)
        self.assertTrue(isinstance(ret, CloudMonitorNotificationType))
        self.assertEqual(ret.id, id_) 

    def test_notif_plan_manager_create(self):
        clt = self.client
        mgr = clt._notification_plan_manager
        clt.method_post = Mock(return_value=(None, None))
        label = utils.random_name()
        name = utils.random_name()
        crit = utils.random_name()
        # Make the OK an object rather than a straight ID.
        ok = fakes.FakeEntity()
        ok_id = ok.id = utils.random_name()
        warn = utils.random_name()
        exp_uri = "/%s" % mgr.uri_base
        exp_body = {"label": label or name, "critical_state": [crit],
                "ok_state": [ok.id], "warning_state": [warn]}
        mgr.create(label=label, name=name, critical_state=crit, ok_state=ok,
                warning_state=warn)
        clt.method_post.assert_called_once_with(exp_uri, body=exp_body)

    def test_entity_mgr_update_entity(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        clt.method_put = Mock(return_value=(None, None))
        agent = utils.random_name()
        metadata = utils.random_name()
        exp_uri = "/%s/%s" % (mgr.uri_base, ent.id)
        exp_body = {"agent_id": agent, "metadata": metadata}
        mgr.update_entity(ent, agent, metadata)
        clt.method_put.assert_called_once_with(exp_uri, body=exp_body)

    def test_entity_mgr_list_checks(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_name()
        ret_body = {"values": [{"id": id_}]}
        clt.method_get = Mock(return_value=(None, ret_body))
        ret = mgr.list_checks(ent)
        exp_uri = "/%s/%s/checks" % (mgr.uri_base, ent.id)
        clt.method_get.assert_called_once_with(exp_uri)
        self.assertEqual(len(ret), 1)
        inst = ret[0]
        self.assertTrue(isinstance(inst, CloudMonitorCheck))
        self.assertEqual(inst.id, id_) 

    def test_entity_mgr_create_check_test_debug(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        label = utils.random_name()
        name = utils.random_name()
        check_type = utils.random_name()
        details = utils.random_name()
        disabled = utils.random_name()
        metadata = utils.random_name()
        monitoring_zones_poll = utils.random_name()
        timeout = utils.random_name()
        period = utils.random_name()
        target_alias = utils.random_name()
        target_hostname = utils.random_name()
        target_receiver = utils.random_name()
        test_only = True
        include_debug = True
        clt.method_post = Mock(return_value=(None, None))
        exp_uri = "/%s/%s/test-check?debug=true" % (mgr.uri_base, ent.id)
        exp_body = {"label": label or name, "details": details,
                "disabled": disabled, "type": check_type,
                "monitoring_zones_poll": [monitoring_zones_poll], "timeout":
                timeout, "period": period, "target_alias": target_alias,
                "target_hostname": target_hostname, "target_receiver":
                target_receiver}
        mgr.create_check(ent, label=label, name=name, check_type=check_type,
                details=details, disabled=disabled, metadata=metadata,
                monitoring_zones_poll=monitoring_zones_poll, timeout=timeout,
                period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver, test_only=test_only,
                include_debug=include_debug)
        clt.method_post.assert_called_once_with(exp_uri, body=exp_body)

    def test_entity_mgr_create_check_test_no_debug(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        label = utils.random_name()
        name = utils.random_name()
        check_type = utils.random_name()
        details = utils.random_name()
        disabled = utils.random_name()
        metadata = utils.random_name()
        monitoring_zones_poll = utils.random_name()
        timeout = utils.random_name()
        period = utils.random_name()
        target_alias = utils.random_name()
        target_hostname = utils.random_name()
        target_receiver = utils.random_name()
        test_only = True
        include_debug = False
        clt.method_post = Mock(return_value=(None, None))
        exp_uri = "/%s/%s/test-check" % (mgr.uri_base, ent.id)
        exp_body = {"label": label or name, "details": details,
                "disabled": disabled, "type": check_type,
                "monitoring_zones_poll": [monitoring_zones_poll], "timeout":
                timeout, "period": period, "target_alias": target_alias,
                "target_hostname": target_hostname, "target_receiver":
                target_receiver}
        mgr.create_check(ent, label=label, name=name, check_type=check_type,
                details=details, disabled=disabled, metadata=metadata,
                monitoring_zones_poll=monitoring_zones_poll, timeout=timeout,
                period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver, test_only=test_only,
                include_debug=include_debug)
        clt.method_post.assert_called_once_with(exp_uri, body=exp_body)

    def test_entity_mgr_create_check(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        label = utils.random_name()
        name = utils.random_name()
        check_type = utils.random_name()
        details = utils.random_name()
        disabled = utils.random_name()
        metadata = utils.random_name()
        monitoring_zones_poll = utils.random_name()
        timeout = utils.random_name()
        period = utils.random_name()
        target_alias = utils.random_name()
        target_hostname = utils.random_name()
        target_receiver = utils.random_name()
        test_only = False
        include_debug = False
        clt.method_post = Mock(return_value=(None, None))
        exp_uri = "/%s/%s/checks" % (mgr.uri_base, ent.id)
        exp_body = {"label": label or name, "details": details,
                "disabled": disabled, "type": check_type,
                "monitoring_zones_poll": [monitoring_zones_poll], "timeout":
                timeout, "period": period, "target_alias": target_alias,
                "target_hostname": target_hostname, "target_receiver":
                target_receiver}
        mgr.create_check(ent, label=label, name=name, check_type=check_type,
                details=details, disabled=disabled, metadata=metadata,
                monitoring_zones_poll=monitoring_zones_poll, timeout=timeout,
                period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver, test_only=test_only,
                include_debug=include_debug)
        clt.method_post.assert_called_once_with(exp_uri, body=exp_body)

    def test_entity_mgr_create_check_no_details(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        self.assertRaises(exc.MissingMonitoringCheckDetails, mgr.create_check,
                ent)

    def test_entity_mgr_create_check_no_target(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        self.assertRaises(exc.MonitoringCheckTargetNotSpecified,
                mgr.create_check, ent, details="fake")

    def test_entity_mgr_create_check_no_mz_poll(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        self.assertRaises(exc.MonitoringZonesPollMissing, mgr.create_check,
                ent, details="fake", target_alias="fake",
                check_type="remote.fake")

    def test_entity_mgr_create_check_invalid_details(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        err = exc.BadRequest(400)
        err.message = "Validation error for key 'fake'"
        err.details = "Validation failed for 'fake'"
        clt.method_post = Mock(side_effect=err)
        self.assertRaises(exc.InvalidMonitoringCheckDetails, mgr.create_check,
                ent, details="fake", target_alias="fake",
                check_type="remote.fake", monitoring_zones_poll="fake")

    def test_entity_mgr_find_all_checks(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        c1 = fakes.FakeCloudMonitorCheck(ent, info={"foo": "fake"})
        c2 = fakes.FakeCloudMonitorCheck(ent, info={"foo": "real"})
        c3 = fakes.FakeCloudMonitorCheck(ent, info={"foo": "fake"})
        mgr.list_checks = Mock(return_value=[c1, c2, c3])
        found = mgr.find_all_checks(ent, foo="fake")
        self.assertEqual(len(found), 2)
        self.assertTrue(c1 in found)
        self.assertTrue(c2 not in found)
        self.assertTrue(c3 in found)

    def test_entity_mgr_update_check(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        chk = fakes.FakeCloudMonitorCheck(ent)
        label = utils.random_name()
        name = utils.random_name()
        check_type = utils.random_name()
        details = utils.random_name()
        disabled = utils.random_name()
        metadata = utils.random_name()
        monitoring_zones_poll = utils.random_name()
        timeout = utils.random_name()
        period = utils.random_name()
        target_alias = utils.random_name()
        target_hostname = utils.random_name()
        target_receiver = utils.random_name()
        test_only = False
        include_debug = False
        clt.method_put = Mock(return_value=(None, None))
        exp_uri = "/%s/%s/checks/%s" % (mgr.uri_base, ent.id, chk.id)
        exp_body = {"label": label or name, "metadata": metadata, "disabled":
            disabled, "monitoring_zones_poll": [monitoring_zones_poll],
            "timeout": timeout, "period": period, "target_alias": target_alias,
            "target_hostname": target_hostname, "target_receiver":
            target_receiver}
        mgr.update_check(chk, label=label, name=name, disabled=disabled,
                metadata=metadata, monitoring_zones_poll=monitoring_zones_poll,
                timeout=timeout, period=period, target_alias=target_alias,
                target_hostname=target_hostname,
                target_receiver=target_receiver)
        clt.method_put.assert_called_once_with(exp_uri, body=exp_body)

    def test_entity_mgr_get_check(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_name()
        ret_body = {"id": id_}
        clt.method_get = Mock(return_value=(None, ret_body))
        ret = mgr.get_check(ent, id_)
        exp_uri = "/%s/%s/checks/%s" % (mgr.uri_base, ent.id, id_)
        clt.method_get.assert_called_once_with(exp_uri)
        self.assertTrue(isinstance(ret, CloudMonitorCheck))
        self.assertEqual(ret.id, id_) 

    def test_entity_mgr_delete_check(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_name()
        clt.method_delete = Mock(return_value=(None, None))
        ret = mgr.delete_check(ent, id_)
        exp_uri = "/%s/%s/checks/%s" % (mgr.uri_base, ent.id, id_)
        clt.method_delete.assert_called_once_with(exp_uri)

    def test_entity_mgr_list_metrics(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        id_ = utils.random_name()
        met1 = utils.random_name()
        met2 = utils.random_name()
        ret_body = {"values": [{"name": met1}, {"name": met2}]}
        clt.method_get = Mock(return_value=(None, ret_body))
        ret = mgr.list_metrics(ent, id_)
        exp_uri = "/%s/%s/checks/%s/metrics" % (mgr.uri_base, ent.id, id_)
        clt.method_get.assert_called_once_with(exp_uri)
        self.assertEqual(len(ret), 2)
        self.assertTrue(met1 in ret)
        self.assertTrue(met2 in ret)

    def test_entity_mgr_get_metric_data_points_no_granularity(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        self.assertRaises(exc.MissingMonitoringCheckGranularity,
                mgr.get_metric_data_points, None, None, None, None, None)

    def test_entity_mgr_get_metric_data_points_invalid_resolution(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        self.assertRaises(exc.InvalidMonitoringMetricsResolution,
                mgr.get_metric_data_points, None, None, None, None, None,
                resolution="INVALID")

    def test_entity_mgr_get_metric_data_points(self):
        ent = self.entity
        clt = self.client
        mgr = clt._entity_manager
        chk_id = utils.random_name()
        metric = utils.random_name()
        resolution = "FULL"
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=7)
        start_stamp = int(utils.to_timestamp(start))
        end_stamp = int(utils.to_timestamp(end))
        stats = ["foo", "bar"]
        exp_qp = "from=%s&to=%s&resolution=%s&select=%s&select=%s" % (
                start_stamp, end_stamp, resolution, stats[0], stats[1])
        exp_uri = "/%s/%s/checks/%s/metrics/%s/plot?%s" % (mgr.uri_base, ent.id,
                chk_id, metric, exp_qp)
        vals = utils.random_name()
        ret_body = {"values": vals}
        clt.method_get = Mock(return_value=(None, ret_body))
        ret = mgr.get_metric_data_points(ent, chk_id, metric, start, end,
                resolution=resolution, stats=stats)
        clt.method_get.assert_called_once_with(exp_uri)
        self.assertEqual(ret, vals)




if __name__ == "__main__":
    unittest.main()
