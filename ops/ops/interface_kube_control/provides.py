import json
from collections import namedtuple

from ops import CharmBase, Relation, Unit
from typing import List

AuthRequest = namedtuple("KubeControlAuthRequest", ["unit", "user", "group"])


class KubeControlProvides:
    """Implements the Provides side of the kube-control interface."""

    def __init__(self, charm: CharmBase, endpoint: str):
        self.charm = charm
        self.endpoint = endpoint

    @property
    def auth_requests(self) -> List[AuthRequest]:
        """Return a list of authentication requests from related units."""
        requests = [
            AuthRequest(unit=unit.name, user=user, group=group)
            for relation in self.relations
            for unit in relation.units
            if (user := relation.data[unit].get("kubelet_user")) and (group := relation.data[unit].get("auth_group"))
        ]
        requests.sort()
        return requests

    def clear_creds(self) -> None:
        """Clear creds from the relation. This is used by non-leader units to
        stop advertising creds so that the leader can assume full control of
        them.
        """
        for relation in self.relations:
            relation.data[self.unit]["creds"] = ""

    @property
    def ingress_addresses(self) -> List[str]:
        """Ingress addresses for this endpoint."""
        return [
            # RFC 5280 section 4.2.1.6: "For IP version 6 ... the octet string
            # MUST contain exactly sixteen octets." We'll use .exploded to be
            # safe.
            addr.exploded
            for addr in self.charm.model.get_binding(
                self.endpoint
            ).network.ingress_addresses
        ]

    @property
    def relations(self) -> List[Relation]:
        """List of relations on this endpoint."""
        return self.charm.model.relations[self.endpoint]

    def set_api_endpoints(self, endpoints) -> None:
        """Send the list of API endpoint URLs to which workers should connect.
        """
        endpoints = json.dumps(endpoints)
        for relation in self.relations:
            relation.data[self.unit]["api-endpoints"] = endpoints

    def set_cluster_name(self, cluster_name) -> None:
        """Send the cluster name to the remote units."""
        for relation in self.relations:
            relation.data[self.unit]["cluster-tag"] = cluster_name

    def set_default_cni(self, default_cni) -> None:
        """Send the default CNI. The default_cni value should be a string
        containing the name of a related CNI application to use as the default
        CNI. For example: "flannel" or "calico". If no default has been chosen
        then "" can be sent instead."""
        value = json.dumps(default_cni)
        for relation in self.relations:
            relation.data[self.unit]["default-cni"] = value

    def set_dns_address(self, address) -> None:
        """Send DNS address to the remote units for use in Kubelet configuration.
        This will typically be the cluster IP of the kube-dns service belonging
        to CoreDNS."""
        for relation in self.relations:
            relation.data[self.unit]["sdn-ip"] = address

    def set_dns_domain(self, domain) -> None:
        """Send DNS domain to the remote units for use in Kubelet configuration.
        """
        for relation in self.relations:
            relation.data[self.unit]["domain"] = domain

    def set_dns_enabled(self, enabled) -> None:
        """Send DNS enabled status. This indicates to remote units if they should
        wait for DNS info or not."""
        value = str(enabled)
        for relation in self.relations:
            relation.data[self.unit]["enable-kube-dns"] = value

    def set_dns_port(self, port) -> None:
        """Send DNS port to the remote units for use in Kubelet configuration."""
        value = str(port)
        for relation in self.relations:
            relation.data[self.unit]["port"] = value

    def set_has_external_cloud_provider(self, has_xcp) -> None:
        """Send indicator to remote units that an external cloud provider is in use."""
        value = str(has_xcp).lower()
        for relation in self.relations:
            relation.data[self.unit]["has-xcp"] = value

    def set_image_registry(self, image_registry) -> None:
        """Send the image registry location to the remote units."""
        for relation in self.relations:
            relation.data[self.unit]["registry-location"] = image_registry

    def set_labels(self, labels) -> None:
        """Send the Juju config labels of the control-plane."""
        value = json.dumps(labels)
        for relation in self.relations:
            relation.data[self.unit]["labels"] = value

    def set_taints(self, taints) -> None:
        """Send the Juju config taints of the control-plane."""
        value = json.dumps(taints)
        for relation in self.relations:
            relation.data[self.unit]["taints"] = value

    def sign_auth_request(
        self, request, client_token, kubelet_token, proxy_token
    ) -> None:
        """Send authorization tokens to the requesting unit."""
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
        """ Local unit. """
        return self.charm.unit
