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


class KubeControlProvider(RelationBase):
    """Implements the kubernetes-master side of the kube-control interface.

    """
    scope = scopes.UNIT

    @hook('{provides:kube-control}-relation-{joined,changed}')
    def joined_or_changed(self):
        conv = self.conversation()
        conv.set_state('{relation_name}.connected')

        hookenv.log('Checking for gpu-enabled workers')
        if self._get_gpu():
            conv.set_state('{relation_name}.gpu.available')
        else:
            conv.remove_state('{relation_name}.gpu.available')

        if self._has_auth_request():
            conv.set_state('{relation_name}.auth.requested')

    @hook('{provides:kube-control}-relation-{broken,departed}')
    def departed(self):
        """Remove all states.

        """
        conv = self.conversation()
        conv.remove_state('{relation_name}.connected')
        conv.remove_state('{relation_name}.gpu.available')

    def set_dns(self, port, domain, sdn_ip):
        """Send DNS info to the remote units.

        We'll need the port, domain, and sdn_ip of the dns service. If
        sdn_ip is not required in your deployment, the units private-ip
        is available implicitly.

        """
        credentials = {
            'port': port,
            'domain': domain,
            'sdn-ip': sdn_ip,
        }
        for conv in self.conversations():
            conv.set_remote(data=credentials)

    def auth_user(self):
        """ return the kubelet_user value on the wire from the requestor """
        conv = self.conversation()
        return (conv.scope, conv.get_remote('kubelet_user'))

    def sign_auth_request(self, kubelet_token, proxy_token):
        """Send authorization tokens to the requesting unit """
        conv = self.conversation()
        conv.set_remote(data={'kubelet_token': kubelet_token,
                              'proxy_token': proxy_token})
        conv.remove_state('{relation_name}.auth.requested')

    def _get_gpu(self):
        """Return True if any remote worker is gpu-enabled.

        """
        for conv in self.conversations():
            if conv.get_remote('gpu') == 'True':
                hookenv.log('Unit {} has gpu enabled'.format(conv.scope))
                return True
        return False

    def _has_auth_request(self):
        """Check if there's a kubelet user on the wire requesting auth. This
        action implies requested kube-proxy auth as well, as kube-proxy should
        be run everywhere there is a kubelet.
        """
        conv = self.conversation()
        if conv.get_remote('kubelet_user'):
            return conv.get_remote('kubelet_user')
