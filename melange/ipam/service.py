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
import json
import routes
from webob.exc import (HTTPUnprocessableEntity, HTTPBadRequest,
                       HTTPNotFound)

from melange.common import service
from melange.common import wsgi
from melange.ipam import models
from melange.ipam.models import (IpBlock, IpAddress, Policy, IpRange,
                                 IpOctet)
from melange.common.utils import exclude


class BaseController(service.Controller):

    def __init__(self):
        exception_map = {HTTPUnprocessableEntity:
                         [models.NoMoreAddressesError,
                          models.DuplicateAddressError,
                          models.AddressDoesNotBelongError,
                          models.AddressLockedError],
                         HTTPBadRequest: [models.InvalidModelError],
                         HTTPNotFound: [models.ModelNotFoundError]}

        super(BaseController, self).__init__(exception_map)

    def _extract_limits(self, params):
        return dict([(key, params[key]) for key in params.keys()
                     if key in ["limit", "marker"]])

    def _get_optionals(self, params, *args):
        return [params.get(key, None) for key in args]

    def _parse_ips(self, addresses):
        return [IpBlock.find_or_allocate_ip(address["ip_block_id"],
                                                 address["ip_address"])
                     for address in json.loads(addresses)]

    def _get_addresses(self, ips):
        return dict(ip_addresses=[ip_address.data() for ip_address in ips])


class IpBlockController(BaseController):

    def __init__(self, type):
        self.type = type
        super(IpBlockController, self).__init__()

    def index(self, request, tenant_id=None):
        all_ips = IpBlock.find_all(tenant_id=tenant_id,
                                                 type=self.type)
        blocks = IpBlock.with_limits(all_ips,
                                     **self._extract_limits(request.params))
        return dict(ip_blocks=[ip_block.data() for ip_block in blocks])

    def create(self, request, tenant_id=None):
        block = IpBlock.create(tenant_id=tenant_id,
                               type=self.type, **request.params)
        return dict(ip_block=block.data()), 201

    def show(self, request, id, tenant_id=None):
        return dict(ip_block=IpBlock.find_by(id=id, type=self.type,
                                          tenant_id=tenant_id).data())

    def delete(self, request, id, tenant_id=None):
        IpBlock.find_by(id=id, type=self.type, tenant_id=tenant_id).delete()


class IpAddressController(BaseController):

    def index(self, request, ip_block_id, tenant_id=None):
        find_all_query = IpAddress.find_all_by_ip_block(ip_block_id)
        addresses = IpAddress.with_limits(find_all_query,
                                       **self._extract_limits(request.params))

        return dict(ip_addresses=[ip_address.data()
                                   for ip_address in addresses])

    def show(self, request, address, ip_block_id, tenant_id=None):
        ip_block = IpBlock.find(ip_block_id)
        return dict(ip_address=ip_block.find_allocated_ip(address).data())

    def delete(self, request, address, ip_block_id, tenant_id=None):
        IpBlock.find(ip_block_id).deallocate_ip(address)

    def create(self, request, ip_block_id, tenant_id=None):
        ip_block = IpBlock.find(ip_block_id)
        address, port_id = self._get_optionals(request.params,
                                               *['address', 'port_id'])
        ip_address = ip_block.allocate_ip(address=address,
                                          port_id=port_id)
        return dict(ip_address=ip_address.data()), 201

    def restore(self, request, ip_block_id, address, tenant_id=None):
        ip_address = IpBlock.find(ip_block_id).find_allocated_ip(address)
        ip_address.restore()


class InsideGlobalsController(BaseController):

    def create(self, request, ip_block_id, address):
        local_ip = IpBlock.find_or_allocate_ip(ip_block_id, address)
        global_ips = self._parse_ips(request.params["ip_addresses"])
        local_ip.add_inside_globals(global_ips)

    def index(self, request, ip_block_id, address):
        ip = IpBlock.find(ip_block_id).find_allocated_ip(address)
        return self._get_addresses(ip.inside_globals(
                                      **self._extract_limits(request.params)))

    def delete(self, request, ip_block_id, address,
               inside_globals_address=None):
        local_ip = IpBlock.find(ip_block_id).find_allocated_ip(address)
        local_ip.remove_inside_globals(inside_globals_address)


class InsideLocalsController(BaseController):

    def create(self, request, ip_block_id, address):
        global_ip = IpBlock.find_or_allocate_ip(ip_block_id, address)
        local_ips = self._parse_ips(request.params["ip_addresses"])
        global_ip.add_inside_locals(local_ips)

    def index(self, request, ip_block_id, address):
        ip = IpBlock.find(ip_block_id).find_allocated_ip(address)
        return self._get_addresses(ip.inside_locals(
                                    **self._extract_limits(request.params)))

    def delete(self, request, ip_block_id, address,
               inside_locals_address=None):
        global_ip = IpBlock.find(ip_block_id).find_allocated_ip(address)
        global_ip.remove_inside_locals(inside_locals_address)


class UnusableIpRangesController(BaseController):

    def create(self, request, policy_id):
        policy = Policy.find(policy_id)
        ip_range = policy.create_unusable_range(**request.params.copy())
        return dict(ip_range=ip_range.data()), 201

    def show(self, request, policy_id, id):
        ip_range = Policy.find(policy_id).find_ip_range(id)
        return dict(ip_range=ip_range.data())

    def index(self, request, policy_id):
        ip_range_all = Policy.find(policy_id).unusable_ip_ranges()
        ip_ranges = IpRange.with_limits(ip_range_all,
                                        **self._extract_limits(request.params))
        return dict(ip_ranges=[ip_range.data() for ip_range in ip_ranges])

    def update(self, request, policy_id, id):
        ip_range = Policy.find(policy_id).find_ip_range(id)
        ip_range.update(request.params)
        return dict(ip_range=ip_range.data())

    def delete(self, request, policy_id, id):
        ip_range = Policy.find(policy_id).find_ip_range(id)
        ip_range.delete()


class UnusableIpOctetsController(BaseController):

    def index(self, request, policy_id):
        policy = Policy.find(policy_id)
        ip_octets = IpOctet.with_limits(policy.unusable_ip_octets(),
                                        **self._extract_limits(request.params))
        return dict(ip_octets=[ip_octet.data() for ip_octet in ip_octets])

    def create(self, request, policy_id):
        policy = Policy.find(policy_id)
        ip_octet = policy.create_unusable_ip_octet(**request.params.copy())
        return dict(ip_octet=ip_octet.data()), 201

    def show(self, request, policy_id, id):
        ip_octet = Policy.find(policy_id).find_ip_octet(id)
        return dict(ip_octet=ip_octet.data())

    def update(self, request, policy_id, id):
        ip_octet = Policy.find(policy_id).find_ip_octet(id)
        ip_octet.update(request.params)
        return dict(ip_octet=ip_octet.data())

    def delete(self, request, policy_id, id):
        ip_octet = Policy.find(policy_id).find_ip_octet(id)
        ip_octet.delete()


class PoliciesController(BaseController):

    def index(self, request, tenant_id=None):
        policies = Policy.with_limits(Policy.find_all(tenant_id=tenant_id),
                                      **self._extract_limits(request.params))
        return dict(policies=[policy.data() for policy in policies])

    def show(self, request, id, tenant_id=None):
        return dict(policy=Policy.find_by(id=id, tenant_id=tenant_id).data())

    def create(self, request, tenant_id=None):
        params = exclude(request.params, 'tenant_id')
        policy = Policy.create(tenant_id=tenant_id, **params)
        return dict(policy=policy.data()), 201

    def update(self, request, id, tenant_id=None):
        policy = Policy.find_by(id=id, tenant_id=tenant_id)
        policy.update(exclude(request.params, 'tenant_id'))
        return dict(policy=policy.data())

    def delete(self, request, id, tenant_id=None):
        policy = Policy.find_by(id=id, tenant_id=tenant_id)
        policy.delete()


class API(wsgi.Router):
    def __init__(self, options={}):
        self.options = options
        mapper = routes.Mapper()

        self._block_and_address_mapper(mapper, "public_ip_block",
                                "/ipam/public_ip_blocks",
                                IpBlockController('public'))
        self._block_and_address_mapper(mapper, "private_ip_block",
                                "/ipam/tenants/{tenant_id}/private_ip_blocks",
                                IpBlockController('private'))
        self._natting_mapper(mapper, "inside_globals",
                             InsideGlobalsController())
        self._natting_mapper(mapper, "inside_locals",
                             InsideLocalsController())
        mapper.resource("policy", "/ipam/policies",
                        controller=PoliciesController())
        mapper.resource("policy", "/ipam/tenants/{tenant_id}/policies",
                        controller=PoliciesController())
        mapper.resource("unusable_ip_range", "unusable_ip_ranges",
                        controller=UnusableIpRangesController(),
                        parent_resource=dict(member_name="policy",
                                           collection_name="/ipam/policies"))
        mapper.resource("unusable_ip_octet", "unusable_ip_octets",
                        controller=UnusableIpOctetsController(),
                        parent_resource=dict(member_name="policy",
                                           collection_name="/ipam/policies"))
        super(API, self).__init__(mapper)

    def _block_and_address_mapper(self, mapper, block_resource,
                                  block_resource_path, block_controller):
        mapper.resource(block_resource, block_resource_path,
                        controller=block_controller)
        block_as_parent = dict(member_name="ip_block",
                            collection_name=block_resource_path)
        self._ip_address_mapper(mapper, IpAddressController(),
                                block_as_parent)

    def _ip_address_mapper(self, mapper, ip_address_controller,
                           parent_resource):
        prefix_path = "%s/{%s_id}" % (parent_resource["collection_name"],
                                      parent_resource["member_name"])
        mapper.connect(prefix_path + "/ip_addresses/{address:.+?}",
                       controller=ip_address_controller, action="show",
                       conditions=dict(method=["GET"]))
        mapper.connect(prefix_path + "/ip_addresses/{address:.+?}",
                       controller=ip_address_controller, action="delete",
                       conditions=dict(method=["DELETE"]))
        mapper.connect(prefix_path + "/ip_addresses/{address:.+?}/restore",
                       controller=ip_address_controller, action="restore",
                       conditions=dict(method=["PUT"]))
        mapper.resource("ip_address", "ip_addresses",
                        controller=ip_address_controller,
                        parent_resource=parent_resource)

    def _natting_mapper(self, mapper, nat_type, nat_controller):
        with mapper.submapper(controller=nat_controller,
                              path_prefix="/ipam/ip_blocks/{ip_block_id}/"
                              "ip_addresses/{address:.+?}/") as submap:
            submap.connect(nat_type, action="create",
                           conditions=dict(method=["POST"]))
            submap.connect(nat_type, action="index",
                           conditions=dict(method=["GET"]))
            submap.connect(nat_type, action="delete",
                           conditions=dict(method=["DELETE"]))
            submap.connect(
                "%(nat_type)s/{%(nat_type)s_address:.+?}" % locals(),
                action="delete",
                conditions=dict(method=["DELETE"]))


def app_factory(global_conf, **local_conf):
    conf = global_conf.copy()
    conf.update(local_conf)
    return API(conf)
