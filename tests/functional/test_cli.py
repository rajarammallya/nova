#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack LLC.
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

# If ../melange/__init__.py exists, add ../ to Python search path, so that
# it will override what happens to be installed in /usr/(local/)lib/python...
from melange.ipam.models import IpBlock, Policy

from tests.functional import execute
from tests.functional import get_api_port
from tests.factories.models import (PublicIpBlockFactory,
                                    PrivateIpBlockFactory, PolicyFactory)
from tests import BaseTest


def run(command):
    return execute("../bin/melange-manage --port=%s %s"
                   % (get_api_port(), command))


class TestPublicIpBlockCLI(BaseTest):

    def test_create(self):
        policy = PolicyFactory()
        exitcode, out, err = run("public_ip_block create 10.1.1.0/29 net1 %s"
                                 % policy.id)

        self.assertEqual(exitcode, 0)
        ip_block = IpBlock.get_by(cidr="10.1.1.0/29", type='public')
        self.assertTrue(ip_block is not None)
        self.assertEqual(ip_block.network_id, "net1")
        self.assertEqual(ip_block.policy_id, policy.id)
        self.assertEqual(ip_block.tenant_id, None)

    def test_list(self):
        exitcode, out, err = run("public_ip_block list")

        self.assertEqual(exitcode, 0)
        self.assertIn("ip_blocks", out)

    def test_show(self):
        ip_block = PublicIpBlockFactory()

        exitcode, out, err = run("public_ip_block show %s" % ip_block.id)

        self.assertEqual(exitcode, 0)
        self.assertIn(ip_block.cidr, out)

    def test_delete(self):
        ip_block = PublicIpBlockFactory()

        exitcode, out, err = run("public_ip_block delete %s" % ip_block.id)

        self.assertEqual(exitcode, 0)
        self.assertTrue(IpBlock.get(ip_block.id) is None)


class TestPrivateIpBlockCLI(BaseTest):

    def test_create(self):
        policy = PolicyFactory()
        exitcode, out, err = run("private_ip_block create 10.1.1.0/29 net1 %s"
                                 % policy.id)

        self.assertEqual(exitcode, 0)
        ip_block = IpBlock.get_by(cidr="10.1.1.0/29", type='private')
        self.assertTrue(ip_block is not None)
        self.assertEqual(ip_block.network_id, "net1")
        self.assertEqual(ip_block.policy_id, policy.id)
        self.assertEqual(ip_block.tenant_id, None)

    def test_list(self):
        exitcode, out, err = run("private_ip_block list")

        self.assertEqual(exitcode, 0)
        self.assertIn("ip_blocks", out)

    def test_show(self):
        ip_block = PrivateIpBlockFactory(tenant_id=None)

        exitcode, out, err = run("private_ip_block show %s" % ip_block.id)

        self.assertEqual(exitcode, 0)
        self.assertIn(ip_block.cidr, out)

    def test_delete(self):
        ip_block = PrivateIpBlockFactory(tenant_id=None)

        exitcode, out, err = run("private_ip_block delete %s" % ip_block.id)

        self.assertEqual(exitcode, 0)
        self.assertTrue(IpBlock.get(ip_block.id) is None)


class TestTenantIpBlockCLI(BaseTest):

    def test_create(self):
        policy = PolicyFactory()
        exitcode, out, err = run("tenant_ip_block create 123 10.1.1.0/29 net1"
                                 " %s" % policy.id)

        self.assertEqual(exitcode, 0)
        ip_block = IpBlock.get_by(cidr="10.1.1.0/29",
                                  type="private", tenant_id="123")
        self.assertTrue(ip_block is not None)
        self.assertEqual(ip_block.network_id, "net1")
        self.assertEqual(ip_block.policy_id, policy.id)

    def test_list(self):
        exitcode, out, err = run("tenant_ip_block list 123")

        self.assertEqual(exitcode, 0)
        self.assertIn("ip_blocks", out)

    def test_show(self):
        ip_block = PrivateIpBlockFactory(tenant_id=123)

        exitcode, out, err = run("tenant_ip_block show 123 %s" % ip_block.id)

        self.assertEqual(exitcode, 0)
        self.assertIn(ip_block.cidr, out)

    def test_delete(self):
        ip_block = PrivateIpBlockFactory(tenant_id=123)

        exitcode, out, err = run("tenant_ip_block delete 123 %s" % ip_block.id)

        self.assertEqual(exitcode, 0)
        self.assertTrue(IpBlock.get(ip_block.id) is None)


class TestPolicyCLI(BaseTest):

    def test_create(self):
        exitcode, out, err = run("policy create policy_name policy_desc")

        self.assertEqual(exitcode, 0)
        policy = Policy.get_by(name="policy_name", description="policy_desc")
        self.assertTrue(policy is not None)
        self.assertEqual(policy.tenant_id, None)

    def test_update(self):
        policy = PolicyFactory(name='name', description='desc')
        exitcode, out, err = run("policy update %s new_name" % policy.id)

        self.assertEqual(exitcode, 0)
        updated_policy = Policy.get(policy.id)
        self.assertEqual(updated_policy.name, "new_name")
        self.assertEqual(updated_policy.description, "desc")

    def test_list(self):
        exitcode, out, err = run("policy list")

        self.assertEqual(exitcode, 0)
        self.assertIn("policies", out)

    def test_show(self):
        policy = PolicyFactory(name="blah", tenant_id=None)

        exitcode, out, err = run("policy show %s" % policy.id)

        self.assertEqual(exitcode, 0)
        self.assertIn(policy.name, out)

    def test_delete(self):
        policy = PolicyFactory(tenant_id=None)

        exitcode, out, err = run("policy delete %s" % policy.id)

        self.assertEqual(exitcode, 0)
        self.assertTrue(Policy.get(policy.id) is None)
