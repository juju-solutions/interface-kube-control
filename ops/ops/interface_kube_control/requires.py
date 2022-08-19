# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
"""Implementation of kube-control interface (requires)

This re-implements the requires side of the interface in ops.framework
style rather than the reactive style.
"""

import base64
import logging
from os import PathLike
from pathlib import Path
from typing import Optional, Mapping

import yaml
from backports.cached_property import cached_property
from .model import Data
from pydantic import ValidationError

from ops.charm import CharmBase, RelationBrokenEvent
from ops.framework import Object
from ops.model import Relation

log = logging.getLogger("KubeControlRequirer")


class KubeControlRequirer(Object):
    """
    Implements the requirer side of the kube-control interface.
    """

    def __init__(self, charm: CharmBase, endpoint: str = "kube-control"):
        super().__init__(charm, f"relation-{endpoint}")
        self.endpoint = endpoint

    @cached_property
    def relation(self) -> Optional[Relation]:
        """The lone relation endpoint or None."""
        return self.model.get_relation(self.endpoint)

    @cached_property
    def _data(self) -> Data:
        raw_data = {}
        if self.relation and self.relation.units:
            raw_data = self.relation.data[list(self.relation.units)[0]]
        return Data(**raw_data)

    def evaluate_relation(self, event) -> Optional[str]:
        """Determine if relation is ready."""
        no_relation = not self.relation or (
            isinstance(event, RelationBrokenEvent) and event.relation is self.relation
        )
        if not self.is_ready:
            if no_relation:
                return f"Missing required {self.endpoint} relation"
            return f"Waiting for {self.endpoint} relation"
        return None

    @property
    def is_ready(self):
        """Whether the request for this instance has been completed."""
        try:
            self._data
        except ValidationError:
            log.error(f"{self.endpoint} relation data not yet valid.")
            return False
        return True

    def create_kubeconfig(
        self, ca: PathLike, kubeconfig: PathLike, user: str, k8s_user: str
    ):
        """Write kubeconfig based on available creds."""
        creds = self.get_auth_credentials(k8s_user)

        cluster = "juju-cluster"
        context = "juju-context"
        endpoints = self.get_api_endpoints()
        server = endpoints[0] if endpoints else None
        token = creds["client_token"] if creds else None
        ca_b64 = base64.b64encode(Path(ca).read_bytes()).decode("utf-8")

        # Create the config file with the address of the control-plane server.
        config_contents = {
            "apiVersion": "v1",
            "kind": "Config",
            "preferences": {},
            "clusters": [
                {
                    "cluster": {
                        "certificate-authority-data": ca_b64,
                        "server": server,
                    },
                    "name": cluster,
                }
            ],
            "contexts": [
                {"context": {"cluster": cluster, "user": user}, "name": context}
            ],
            "users": [{"name": user, "user": {"token": token}}],
            "current-context": context,
        }
        old_kubeconfig = Path(kubeconfig)
        new_kubeconfig = Path(f"{kubeconfig}.new")
        new_kubeconfig.parent.mkdir(exist_ok=True, mode=0o750)
        new_kubeconfig.write_text(yaml.safe_dump(config_contents))
        new_kubeconfig.chmod(mode=0o600)

        if old_kubeconfig.exists():
            changed = new_kubeconfig.read_text() != old_kubeconfig.read_text()
        else:
            changed = True
        if changed:
            new_kubeconfig.rename(old_kubeconfig)

    def get_auth_credentials(self, user) -> Optional[Mapping[str, str]]:
        """Return the authentication credentials."""
        creds = self._data.creds

        if user in creds:
            return {
                "user": user,
                "kubelet_token": creds[user].kubelet_token,
                "proxy_token": creds[user].proxy_token,
                "client_token": creds[user].client_token,
            }
        return None

    def get_dns(self) -> Mapping[str, str]:
        """
        Return DNS info provided by the control-plane.
        """
        return {
            "port": self._data.port,
            "domain": self._data.domain,
            "sdn-ip": self._data.sdn_ip,
            "enable-kube-dns": self._data.enable_kube_dns,
        }

    def dns_ready(self) -> bool:
        """
        Return True if we have all DNS info from the control-plane.
        """
        keys = ["port", "domain", "sdn-ip", "enable-kube-dns"]
        dns_info = self.get_dns()
        return (
            set(dns_info.keys()) == set(keys)
            and dns_info["enable-kube-dns"] is not None
        )

    def set_auth_request(self, user, group="system:nodes") -> None:
        """Notify contol-plane that we are requesting auth.

        Also, use this hostname for the kubelet system account.

        @params user   - user requesting authentication
        @params groups - Determines the level of eleveted privileges of the
                         requested user.
                         Can be overridden to request sudo level access on the
                         cluster via changing to
                         system:masters.  #wokeignore:rule=master
        """
        for relation in self.model.relations:
            relation.data[self.model.unit].update(
                dict(kubelet_user=user, auth_group=group)
            )

    def set_gpu(self, enabled=True):
        """
        Tell the control-plane that we're gpu-enabled (or not).
        """
        log("Setting gpu={} on kube-control relation".format(enabled))
        for relation in self.model.relations:
            relation.data[self.model.unit].update(dict(gpu=enabled))

    def get_cluster_tag(self):
        """
        Tag for identifying resources that are part of the cluster.
        """
        return self._data.cluster_tag

    def get_registry_location(self):
        """
        URL for container image registry.
        """
        return self._data.registry_location

    @property
    def cohort_keys(self):
        """
        The cohort snapshot keys sent by the control-plane.
        """
        return self._data.cohort_keys

    def get_default_cni(self):
        """
        Default CNI network to use.
        """
        return self._data.default_cni

    def get_api_endpoints(self):
        """
        Returns a list of API endpoint URLs.
        """
        endpoints = set(map(str,self._data.api_endpoints) or [])
        return sorted(endpoints)

    @property
    def has_xcp(self):
        """The has-xcp value."""
        return self._data.has_xcp or False
