# Copyright 2012 Nebula, Inc.
# Copyright 2013 IBM Corp.
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

from nova.tests.functional.v3 import api_sample_base
from nova.tests.unit.image import fake


class ServersSampleBase(api_sample_base.ApiSampleTestBaseV3):
    def _post_server(self, use_common_server_api_samples=True):
        # param use_common_server_api_samples: Boolean to set whether tests use
        # common sample files for server post request and response.
        # Default is True which means _get_sample_path method will fetch the
        # common server sample files from 'servers' directory.
        # Set False if tests need to use extension specific sample files

        subs = {
            'image_id': fake.get_valid_image_id(),
            'host': self._get_host(),
            'glance_host': self._get_glance_host()
        }
        orig_value = self.__class__._use_common_server_api_samples
        try:
            self.__class__._use_common_server_api_samples = (
                                        use_common_server_api_samples)
            response = self._do_post('servers', 'server-post-req', subs)
            subs = self._get_regexes()
            status = self._verify_response('server-post-resp', subs,
                                           response, 202)
            return status
        finally:
            self.__class__._use_common_server_api_samples = orig_value


class ServersSampleJsonTest(ServersSampleBase):
    sample_dir = 'servers'

    def test_servers_post(self):
        return self._post_server()

    def test_servers_get(self):
        uuid = self.test_servers_post()
        response = self._do_get('servers/%s' % uuid)
        subs = self._get_regexes()
        subs['hostid'] = '[a-f0-9]+'
        subs['id'] = uuid
        subs['hypervisor_hostname'] = r'[\w\.\-]+'
        subs['mac_addr'] = '(?:[a-f0-9]{2}:){5}[a-f0-9]{2}'
        self._verify_response('server-get-resp', subs, response, 200)

    def test_servers_list(self):
        uuid = self._post_server()
        response = self._do_get('servers')
        subs = self._get_regexes()
        subs['id'] = uuid
        self._verify_response('servers-list-resp', subs, response, 200)

    def test_servers_details(self):
        uuid = self._post_server()
        response = self._do_get('servers/detail')
        subs = self._get_regexes()
        subs['hostid'] = '[a-f0-9]+'
        subs['id'] = uuid
        subs['hypervisor_hostname'] = r'[\w\.\-]+'
        subs['mac_addr'] = '(?:[a-f0-9]{2}:){5}[a-f0-9]{2}'
        self._verify_response('servers-details-resp', subs, response, 200)


class ServerSortKeysJsonTests(ServersSampleBase):
    sample_dir = 'servers-sort'

    def test_servers_list(self):
        self._post_server()
        response = self._do_get('servers?sort_key=display_name&sort_dir=asc')
        subs = self._get_regexes()
        self._verify_response('server-sort-keys-list-resp', subs, response,
                              200)


class ServersSampleAllExtensionJsonTest(ServersSampleJsonTest):
    all_extensions = True


class ServersActionsJsonTest(ServersSampleBase):
    sample_dir = 'servers'

    def _test_server_action(self, uuid, action, req_tpl,
                            subs=None, resp_tpl=None, code=202):
        subs = subs or {}
        subs.update({'action': action,
                     'glance_host': self._get_glance_host()})
        response = self._do_post('servers/%s/action' % uuid,
                                 req_tpl,
                                 subs)
        if resp_tpl:
            subs.update(self._get_regexes())
            self._verify_response(resp_tpl, subs, response, code)
        else:
            self.assertEqual(response.status_code, code)
            self.assertEqual(response.content, "")

    def test_server_reboot_hard(self):
        uuid = self._post_server()
        self._test_server_action(uuid, "reboot",
                                 'server-action-reboot',
                                 {"type": "HARD"})

    def test_server_reboot_soft(self):
        uuid = self._post_server()
        self._test_server_action(uuid, "reboot",
                                 'server-action-reboot',
                                 {"type": "SOFT"})

    def test_server_rebuild(self):
        uuid = self._post_server()
        image = fake.get_valid_image_id()
        subs = {'host': self._get_host(),
                'uuid': image,
                'name': 'foobar',
                'pass': 'seekr3t',
                'hostid': '[a-f0-9]+',
                }
        self._test_server_action(uuid, 'rebuild',
                                 'server-action-rebuild',
                                  subs,
                                 'server-action-rebuild-resp')

    def test_server_resize(self):
        self.flags(allow_resize_to_same_host=True)
        uuid = self._post_server()
        self._test_server_action(uuid, "resize",
                                 'server-action-resize',
                                 {"id": 2,
                                  "host": self._get_host()})
        return uuid

    def test_server_revert_resize(self):
        uuid = self.test_server_resize()
        self._test_server_action(uuid, "revertResize",
                                 'server-action-revert-resize')

    def test_server_confirm_resize(self):
        uuid = self.test_server_resize()
        self._test_server_action(uuid, "confirmResize",
                                 'server-action-confirm-resize',
                                 code=204)

    def test_server_create_image(self):
        uuid = self._post_server()
        self._test_server_action(uuid, 'createImage',
                                 'server-action-create-image',
                                 {'name': 'foo-image'})


class ServerStartStopJsonTest(ServersSampleBase):
    sample_dir = 'servers'

    def _test_server_action(self, uuid, action, req_tpl):
        response = self._do_post('servers/%s/action' % uuid,
                                 req_tpl,
                                 {'action': action})
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.content, "")

    def test_server_start(self):
        uuid = self._post_server()
        self._test_server_action(uuid, 'os-stop', 'server-action-stop')
        self._test_server_action(uuid, 'os-start', 'server-action-start')

    def test_server_stop(self):
        uuid = self._post_server()
        self._test_server_action(uuid, 'os-stop', 'server-action-stop')
