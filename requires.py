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

from charms.reactive import RelationBase
from charms.reactive import hook
from charms.reactive import scopes

from charmhelpers.core import hookenv


class KubeControlRequireer(RelationBase):
    """Implements the kubernetes-worker side of the kube-control interface.

    """
    scope = scopes.GLOBAL

    @hook('{requires:kube-control}-relation-{joined,changed}')
    def joined_or_changed(self):
        """Set states corresponding to the data we have.

        """
        conv = self.conversation()
        conv.set_state('{relation_name}.connected')

        if self.dns_ready():
            conv.set_state('{relation_name}.dns.available')
        else:
            conv.remove_state('{relation_name}.dns.available')

    @hook('{requires:kube-control}-relation-{broken,departed}')
    def departed(self):
        """Remove all states.

        """
        conv = self.conversation()
        conv.remove_state('{relation_name}.connected')
        conv.remove_state('{relation_name}.dns.available')

    def get_dns(self):
        """Return DNS info provided by the master.

        """
        conv = self.conversation()

        return {
            'private-address': conv.get_remote('private-address'),
            'port': conv.get_remote('port'),
            'domain': conv.get_remote('domain'),
            'sdn-ip': conv.get_remote('sdn-ip'),
        }

    def dns_ready(self):
        """Return True if we have all DNS info from the master.

        """
        return all(self.get_dns().values())

    def set_gpu(self, enabled=True):
        """Tell the master that we're gpu-enabled (or not).

        """
        hookenv.log('Setting gpu={} on kube-control relation'.format(enabled))
        conv = self.conversation()
        conv.set_remote(gpu=enabled)
