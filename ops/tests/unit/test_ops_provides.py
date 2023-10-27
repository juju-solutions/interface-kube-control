# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
import unittest.mock as mock

import pytest
from ops.charm import CharmBase
from ops.interface_kube_control import KubeControlProvides


@pytest.fixture(scope="function")
def kube_control_provider():
    mock_charm = mock.MagicMock(auto_spec=CharmBase)
    mock_charm.framework.model.unit.name = "test/0"
    yield KubeControlProvides(mock_charm, "kube-control")


def test_sign_auth_request(kube_control_provider):
    with mock.patch.object(
        KubeControlProvides, "relations", new_callable=mock.PropertyMock
    ) as mock_prop:
        mock_relation = mock.MagicMock()
        mock_relation.data = {kube_control_provider.unit: {}}
        mock_prop.return_value = [mock_relation]
        mock_request = mock.MagicMock()
        mock_request.user = "system:node:juju-561c45-7"
        mock_request.unit = "kubernetes-worker/0"

        kube_control_provider.sign_auth_request(
            request=mock_request,
            client_token="admin::client-token-1",
            kubelet_token="kubernetes-worker/0::kubelet-token-1",
            proxy_token="kube-proxy::proxy-token-1",
        )
        assert mock_relation.data[kube_control_provider.unit] == {
            "creds": '{"system:node:juju-561c45-7": {"client_token": '
            '"admin::client-token-1", "kubelet_token": '
            '"kubernetes-worker/0::kubelet-token-1", "proxy_token": '
            '"kube-proxy::proxy-token-1", "scope": "kubernetes-worker/0"}}',
        }

        mock_request.user = "system:node:juju-561c45-8"
        mock_request.unit = "kubernetes-worker/1"
        kube_control_provider.sign_auth_request(
            request=mock_request,
            client_token="admin::client-token-2",
            kubelet_token="kubernetes-worker/1::kubelet-token-2",
            proxy_token="kube-proxy::proxy-token-2",
        )
        assert mock_relation.data[kube_control_provider.unit] == {
            "creds": '{"system:node:juju-561c45-7": {"client_token": '
            '"admin::client-token-1", "kubelet_token": '
            '"kubernetes-worker/0::kubelet-token-1", "proxy_token": '
            '"kube-proxy::proxy-token-1", "scope": "kubernetes-worker/0"},'
            ' "system:node:juju-561c45-8": {"client_token": '
            '"admin::client-token-2", "kubelet_token": '
            '"kubernetes-worker/1::kubelet-token-2", "proxy_token": '
            '"kube-proxy::proxy-token-2", "scope": "kubernetes-worker/1"}}',
        }
