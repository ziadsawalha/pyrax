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

import os
import sys

import pyrax

creds_file = os.path.expanduser("~/.rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file)
cm = pyrax.cloud_monitoring

# We need the IP address of the entity for this check
ents = cm.list_entities()
if not ents:
    print "You must create an entity before you can create a check."
    sys.exit()
print "Select the entity on which you wish to create the check:"
for num, ent in enumerate(ents):
    print "%s: %s" % (num, ent.name)
# Add an escape option
escape_opt = num + 1
print "%s: HELP! I don't want to create a check after all!!" % escape_opt
choice = raw_input("Selection: ")
try:
    ichoice = int(choice)
    if ichoice > escape_opt:
        raise ValueError
except ValueError:
    print "Valid entries are the numbers 0-%s. Received '%s'." % (escape_opt,
            choice)
    sys.exit()

if ichoice == escape_opt:
    print "Bye!"
    sys.exit()

print ents[ichoice]

# Get a list of Check Types
chk_types = cm.list_check_types()
print "Check Types:"
for chk_type in chk_types:
    print "  ", chk_type.type, chk_type.id
print

# List the available Monitoring Zones
mzs = cm.list_monitoring_zones()
print "Monitoring Zones:"
for mz in mzs:
    print "  ", mz.id, mz.label
print

exit()
servers = cs.servers.list()
if not servers:
    print "You must have at least one server to run this sample code."
    exit()
server = servers[0]
ip = server.accessIPv4
print "Using server:", server.name, "with IP =", ip

# Create a check for HTTP
chk = cm.create_check(label="sample_check", check_type="remote.http",
        details={"url": "http://%s" % ip}, monitoring_zones_poll=mzs,
        period=900, timeout=20, target_hostname=ip)

print "Name:", chk.name
print "ID:", chk.id
print dir(chk)


chk.delete()
