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
import json

from charms.reactive import (
    Endpoint,
    set_flag,
    clear_flag
)

from charms.reactive import (
    when,
    when_any,
    when_not
)

from charmhelpers.core.hookenv import log


class KubeControlRequirer(Endpoint):
    """
    Implements the kubernetes-worker side of the kube-control interface.
    """
    @when_any('endpoint.{endpoint_name}.joined',
              'endpoint.{endpoint_name}.changed')
    def joined_or_changed(self):
        """
        Set states corresponding to the data we have.
        """
        set_flag(self.expand_name('{endpoint_name}.connected'))
        self.check_states()
        clear_flag(self.expand_name('endpoint.{endpoint_name}.changed'))

    @when_not('endpoint.{endpoint_name}.joined')
    def departed(self):
        """
        Remove states corresponding to the data we have.
        """
        clear_flag(
            self.expand_name(
                '{endpoint_name}.connected'))
        clear_flag(
            self.expand_name(
                '{endpoint_name}.dns.available'))
        clear_flag(
            self.expand_name(
                '{endpoint_name}.auth.available'))
        clear_flag(
            self.expand_name(
                '{endpoint_name}.cluster_tag.available'))
        clear_flag(
            self.expand_name(
                '{endpoint_name}.registry_location.available'))

    def check_states(self):
        """
        Toggle states based on available data.
        """
        if self.dns_ready():
            set_flag(
                self.expand_name(
                    '{endpoint_name}.dns.available'))
        else:
            clear_flag(
                self.expand_name(
                    '{endpoint_name}.dns.available'))

        if self._has_auth_credentials():
            set_flag(
                self.expand_name(
                    '{endpoint_name}.auth.available'))
        else:
            clear_flag(
                self.expand_name(
                    '{endpoint_name}.auth.available'))

        if self.get_cluster_tag():
            set_flag(
                self.expand_name(
                    '{endpoint_name}.cluster_tag.available'))
        else:
            clear_flag(
                self.expand_name(
                    '{endpoint_name}.cluster_tag.available'))

        if self.get_registry_location():
            set_flag(
                self.expand_name(
                    '{endpoint_name}.registry_location.available'))
        else:
            clear_flag(
                self.expand_name(
                    '{endpoint_name}.registry_location.available'))

    def get_auth_credentials(self, user):
        """
        Return the authentication credentials.
        """
        rx = {}
        for unit in self.all_joined_units:
            rx.update(unit.received.get('creds', {}))
        if not rx:
            return None

        if user in rx:
            return {
                'user': user,
                'kubelet_token': rx[user]['kubelet_token'],
                'proxy_token': rx[user]['proxy_token'],
                'client_token': rx[user]['client_token']
            }
        else:
            return None

    def get_dns(self):
        """
        Return DNS info provided by the master.
        """
        rx = self.all_joined_units.received_raw

        return {
            'port': rx.get('port'),
            'domain': rx.get('domain'),
            'sdn-ip': rx.get('sdn-ip'),
            'enable-kube-dns': rx.get('enable-kube-dns'),
        }

    def dns_ready(self):
        """
        Return True if we have all DNS info from the master.
        """
        keys = ['port', 'domain', 'sdn-ip', 'enable-kube-dns']
        dns_info = self.get_dns()
        return (set(dns_info.keys()) == set(keys) and
                dns_info['enable-kube-dns'] is not None)

    def set_auth_request(self, kubelet, group='system:nodes'):
        """
        Tell the master that we are requesting auth, and to use this
        hostname for the kubelet system account.

        Param groups - Determines the level of eleveted privleges of the
        requested user. Can be overridden to request sudo level access on the
        cluster via changing to system:masters.
        """
        for relation in self.relations:
            relation.to_publish_raw.update({
                'kubelet_user': kubelet,
                'auth_group': group
            })

    def set_gpu(self, enabled=True):
        """
        Tell the master that we're gpu-enabled (or not).
        """
        log('Setting gpu={} on kube-control relation'.format(enabled))
        for relation in self.relations:
            relation.to_publish_raw.update({
                'gpu': enabled
            })

    def _has_auth_credentials(self):
        """
        Predicate method to signal we have authentication credentials.
        """
        if self.all_joined_units.received_raw.get('creds'):
            return True

    def get_cluster_tag(self):
        """
        Tag for identifying resources that are part of the cluster.
        """
        return self.all_joined_units.received_raw.get('cluster-tag')

    def get_registry_location(self):
        """
        URL for container image registry.
        """
        return self.all_joined_units.received_raw.get('registry-location')
