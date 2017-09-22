#!/usr/bin/python
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from charms.reactive import Endpoint
from charms.reactive import when
from charms.reactive import when_not
from charms.reactive import set_flag
from charms.reactive import clear_flag
from charms.reactive import toggle_flag

from charmhelpers.core import hookenv


# TODO: update charms and remove legacy flags
class KubeControlProvider(Endpoint):
    """Implements the kubernetes-master side of the kube-control interface.

    """
    @when('endpoint.{relation_name}.joined')
    def legacy_flag_connected(self):
        set_flag(self.flag('{relation_name}.connected'))

    @when('endpoint.{relation_name}.departed')
    def legacy_flag_departed(self):
        set_flag(self.flag('{relation_name}.departed'))

    @when('endpoint.{relation_name}.changed.gpu')
    def check_gpu(self):
        """Set ``{relation_name}.gpu.available`` if any remote worker
        is gpu-enabled.

        """
        clear_flag(self.flag('endpoint.{relation_name}.changed.gpu'))
        hookenv.log('Checking for gpu-enabled workers')

        # json_receive automatically decodes bool values, but existing
        # relations may have the older string form
        gpu_enabled = self.all_units.json_receive['gpu'] in (True, 'True')
        toggle_flag(self.flag('endpoint.{relation_name}.gpu.available'),
                    should_set=gpu_enabled)
        toggle_flag(self.flag('{relation_name}.gpu.available'),  # legacy flag
                    should_set=gpu_enabled)

    @when('endpoint.{relation_name}.changed.kubelet_user')
    def check_auth_request(self):
        """Check if there's a kubelet user on the wire requesting auth. This
        action implies requested kube-proxy auth as well, as kube-proxy should
        be run everywhere there is a kubelet.
        """
        clear_flag(self.flag('endpoint.{relation_name}.changed.kubelet_user'))
        auth_requested = self.all_units.receive['kubelet_user']
        toggle_flag(self.flag('endpoint.{relation_name}.auth.requested'),
                    should_set=auth_requested)
        toggle_flag(self.flag('{relation_name}.auth.requested'),  # legacy flag
                    should_set=auth_requested)

    @when_not('endpoint.{relation_name}.joined')
    def broken(self):
        """Remove all flags.

        """
        clear_flag(self.flag('endpoint.{relation_name}.gpu.available'))
        clear_flag(self.flag('endpoint.{relation_name}.auth.requested'))
        clear_flag(self.flag('{relation_name}.connected'))  # legacy flag
        clear_flag(self.flag('{relation_name}.gpu.available'))  # legacy flag
        clear_flag(self.flag('{relation_name}.auth.requested'))  # legacy flag

    def flush_departed(self):
        """Remove the signal state that we have a unit departing the
        relationship. Additionally return the unit departing so the host can
        do any cleanup logic required. """
        clear_flag(self.flag('endpoint.{relation_name}.departed'))
        clear_flag(self.flag('{relation_name}.departed'))  # legacy flag

    def set_dns(self, port, domain, sdn_ip):
        """Send DNS info to the remote units.

        We'll need the port, domain, and sdn_ip of the dns service. If
        sdn_ip is not required in your deployment, the units private-ip
        is available implicitly.

        """
        for relation in self.relations:
            relation.send['port'] = port
            relation.send['domain'] = domain
            relation.send['sdn-ip'] = sdn_ip

    def auth_user(self):
        """ return the kubelet_user value on the wire from the requestors """
        requests = []
        for unit in self.all_units:
            # NB: These values aren't actually used by the master, and we
            # ought to just send the relations (or relation_ids).
            user = unit.receive['kubelet_user']
            group = unit.receive['auth_group']
            if not (user and group):
                continue
            requests.append((unit, {'user': user,
                                    'group': group}))
        return requests

    def sign_auth_request(self, unit, kubelet_token, proxy_token,
                          client_token):
        """Send authorization tokens to the requesting unit """
        # NB: You can actually only send data at the relation level, meaning
        # all units of that relation receive the same data.  So, all workers
        # are going to receive the same tokens, unless we send structrued
        # data keyed by unit name.
        unit.relation.send.update({'kubelet_token': kubelet_token,
                                   'proxy_token': proxy_token,
                                   'client_token': client_token})
        clear_flag(self.flag('endpoint.{relation_name}.auth.requested'))
        clear_flag(self.flag('{relation_name}.auth.requested'))  # legacy flag
