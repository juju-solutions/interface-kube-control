import json
from collections import namedtuple

from ops import CharmBase, Relation, Unit
from typing import List

AuthRequest = namedtuple("KubeControlAuthRequest", ["unit", "user", "group"])


class KubeControlProvides:
    """Implemenets the Provides side of the kube-control interface."""

    def __init__(self, charm: CharmBase, endpoint: str):
        self.charm = charm
        self.endpoint = endpoint

    @property
    def auth_requests(self) -> List[AuthRequest]:
        requests = []
        for relation in self.relations:
            for unit in relation.units:
                user = relation.data[unit].get("kubelet_user")
                group = relation.data[unit].get("auth_group")
                if user and group:
                    request = AuthRequest(unit=unit.name, user=user, group=group)
                    requests.append(request)
        requests.sort()
        return requests

    def clear_creds(self) -> None:
        for relation in self.relations:
            relation.data[self.unit]["creds"] = ""

    @property
    def relations(self) -> List[Relation]:
        return self.charm.model.relations[self.endpoint]

    def set_api_endpoints(self, endpoints) -> None:
        endpoints = json.dumps(endpoints)
        for relation in self.relations:
            relation.data[self.unit]["api-endpoints"] = endpoints

    def set_cluster_name(self, cluster_name) -> None:
        for relation in self.relations:
            relation.data[self.unit]["cluster-tag"] = cluster_name

    def set_default_cni(self, default_cni) -> None:
        value = json.dumps(default_cni)
        for relation in self.relations:
            relation.data[self.unit]["default-cni"] = value

    def set_dns_address(self, address) -> None:
        for relation in self.relations:
            relation.data[self.unit]["sdn-ip"] = address

    def set_dns_domain(self, domain) -> None:
        for relation in self.relations:
            relation.data[self.unit]["domain"] = domain

    def set_dns_enabled(self, enabled) -> None:
        value = str(enabled)
        for relation in self.relations:
            relation.data[self.unit]["enable-kube-dns"] = value

    def set_dns_port(self, port) -> None:
        value = str(port)
        for relation in self.relations:
            relation.data[self.unit]["port"] = value

    def set_has_external_cloud_provider(self, has_xcp) -> None:
        value = str(has_xcp).lower()
        for relation in self.relations:
            relation.data[self.unit]["has-xcp"] = value

    def set_image_registry(self, image_registry) -> None:
        for relation in self.relations:
            relation.data[self.unit]["image-registry"] = image_registry

    def set_labels(self, labels) -> None:
        value = json.dumps(labels)
        for relation in self.relations:
            relation.data[self.unit]["labels"] = value

    def set_taints(self, taints) -> None:
        value = json.dumps(taints)
        for relation in self.relations:
            relation.data[self.unit]["taints"] = value

    def sign_auth_request(
        self, request, client_token, kubelet_token, proxy_token
    ) -> None:
        creds = {}
        for relation in self.relations:
            creds.update(json.loads(relation.data[self.unit].get("creds", "{}")))
        creds[request.user] = {
            "client_token": client_token,
            "kubelet_token": kubelet_token,
            "proxy_token": proxy_token,
        }
        value = json.dumps(creds)
        for relation in self.relations:
            relation.data[self.unit]["creds"] = value

    @property
    def unit(self) -> Unit:
        return self.charm.unit
