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
class KubeControlRequireer(Endpoint):
    """Implements the kubernetes-worker side of the kube-control interface.

    """
    @when('endpoint.{relation_name}.joined')
    def legacy_flag_connected(self):
        set_flag(self.flag('{relation_name}.connected'))

    @when('endpoint.{relation_name}.changed')
    def changed(self):
        """Set states corresponding to the data we have.

        """
        toggle_flag(self.flag('endpoint.{relation_name}.dns.available'),
                    should_set=self.dns_ready())
        toggle_flag(self.flag('endpoint.{relation_name}.auth.available'),
                    should_set=self._has_auth_credentials())

        toggle_flag(self.flag('{relation_name}.dns.available'),  # legacy flag
                    should_set=self.dns_ready())
        toggle_flag(self.flag('{relation_name}.auth.available'),  # legacy flag
                    should_set=self._has_auth_credentials())

    @when_not('endpoint.{relation_name}.joined')
    def broken(self):
        """Remove all states.

        """
        clear_flag(self.flag('endpoint.{relation_name}.dns.available'))
        clear_flag(self.flag('endpoint.{relation_name}.auth.available'))
        clear_flag(self.flag('{relation_name}.connected'))  # legacy flag
        clear_flag(self.flag('{relation_name}.dns.available'))  # legacy flag
        clear_flag(self.flag('{relation_name}.auth.available'))  # legacy flag

    def get_auth_credentials(self):
        """ Return the authentication credentials.

        """
        return {
            'kubelet_token': self.all_units.receive['kubelet_token'],
            'proxy_token': self.all_units.receive['proxy_token'],
            'client_token': self.all_units.receive['client_token'],
        }

    def get_dns(self):
        """Return DNS info provided by the master.

        """
        return {
            'private-address': self.all_units.receive['private-address'],
            'port': self.all_units.receive['port'],
            'domain': self.all_units.receive['domain'],
            'sdn-ip': self.all_units.receive['sdn-ip'],
        }

    def dns_ready(self):
        """Return True if we have all DNS info from the master.

        """
        return all(self.get_dns().values())

    def set_auth_request(self, kubelet, group='system:nodes'):
        """ Tell the master that we are requesting auth, and to use this
        hostname for the kubelet system account.

        Param groups - Determines the level of eleveted privleges of the
        requested user. Can be overridden to request sudo level access on the
        cluster via changing to system:masters """
        for relation in self.relations:  # should only ever be one relation
            relation.send.update({'kubelet_user': kubelet,
                                  'auth_group': group})

    def set_gpu(self, enabled=True):
        """Tell the master that we're gpu-enabled (or not).

        """
        hookenv.log('Setting gpu={} on kube-control relation'.format(enabled))
        for relation in self.relations:  # should only ever be one relation
            relation.json_send['gpu'] = enabled

    def _has_auth_credentials(self):
        """Predicate method to signal we have authentication credentials """
        return all(self.get_auth_credentials().values())
