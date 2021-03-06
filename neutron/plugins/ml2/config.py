# Copyright (c) 2013 OpenStack Foundation
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

from oslo_config import cfg

from neutron._i18n import _

ml2_opts = [
    cfg.ListOpt('type_drivers',
                default=['local', 'flat', 'vlan', 'gre', 'vxlan', 'geneve'],
                help=_("List of network type driver entrypoints to be loaded "
                       "from the neutron.ml2.type_drivers namespace.")),
    cfg.ListOpt('tenant_network_types',
                default=['local'],
                help=_("Ordered list of network_types to allocate as tenant "
                       "networks. The default value 'local' is useful for "
                       "single-box testing but provides no connectivity "
                       "between hosts.")),
    cfg.ListOpt('mechanism_drivers',
                default=[],
                help=_("An ordered list of networking mechanism driver "
                       "entrypoints to be loaded from the "
                       "neutron.ml2.mechanism_drivers namespace.")),
    cfg.ListOpt('extension_drivers',
                default=[],
                help=_("An ordered list of extension driver "
                       "entrypoints to be loaded from the "
                       "neutron.ml2.extension_drivers namespace. "
                       "For example: extension_drivers = port_security,qos")),
    cfg.IntOpt('path_mtu', default=1500,
               help=_('Maximum size of an IP packet (MTU) that can traverse '
                      'the underlying physical network infrastructure without '
                      'fragmentation. For instances using a '
                      'self-service/private network, neutron subtracts the '
                      'overlay protocol overhead from this value and '
                      'provides it to instances via DHCP option 26. For '
                      'example, using a value of 9000, DHCP provides 8950 '
                      'to instances using a VXLAN network that contains '
                      '50 bytes of overhead. Using a value of 0 disables '
                      'this feature and instances typically default to a '
                      '1500 MTU. Only impacts instances, not neutron network '
                      'components such as bridges and routers.')),
    cfg.IntOpt('segment_mtu', default=1500,
               help=_('The maximum permissible size of an unfragmented '
                      'packet travelling a L2 network segment. The default '
                      'value of 1500 is used as the segment MTU, to reflect '
                      'standard Ethernet.')),
    cfg.ListOpt('physical_network_mtus',
                default=[],
                help=_("A list of mappings of physical networks to MTU "
                       "values. The format of the mapping is "
                       "<physnet>:<mtu val>. This mapping allows "
                       "specifying a physical network MTU value that "
                       "differs from the default segment_mtu value.")),
    cfg.StrOpt('external_network_type',
               help=_("Default network type for external networks when no "
                      "provider attributes are specified. By default it is "
                      "None, which means that if provider attributes are not "
                      "specified while creating external networks then they "
                      "will have the same type as tenant networks. Allowed "
                      "values for external_network_type config option depend "
                      "on the network type values configured in type_drivers "
                      "config option."))
]


cfg.CONF.register_opts(ml2_opts, "ml2")
