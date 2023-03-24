# Copyright 2022 Canonical Ltd.
# See LICENSE file for licensing details.
from ipaddress import ip_network
import unittest.mock as mock
from pathlib import Path

import pytest
import yaml
from ops.charm import RelationBrokenEvent, CharmBase
from ops.interface_kube_control import KubeControlRequirer


@pytest.fixture(scope="function")
def kube_control_requirer():
    mock_charm = mock.MagicMock(auto_spec=CharmBase)
    mock_charm.framework.model.unit.name = "test/0"
    yield KubeControlRequirer(mock_charm)


@pytest.fixture(autouse=True)
def mock_ca_cert(tmpdir):
    ca_cert = Path(tmpdir) / "ca.crt"
    ca_cert.write_bytes(b"abcd")
    yield ca_cert


@pytest.fixture()
def relation_data():
    yield yaml.safe_load(Path("tests/data/kube_control_data.yaml").open())


@pytest.mark.parametrize(
    "event_type", [None, RelationBrokenEvent], ids=["unrelated", "dropped relation"]
)
def test_is_ready_no_relation(kube_control_requirer, event_type):
    with mock.patch.object(
        KubeControlRequirer, "relation", new_callable=mock.PropertyMock
    ) as mock_prop:
        relation = mock_prop.return_value
        relation.__bool__.return_value = event_type is not None
        relation.units = []
        event = mock.MagicMock(spec=event_type)
        event.relation = relation
        assert kube_control_requirer.is_ready is False
        assert "Missing" in kube_control_requirer.evaluate_relation(event)
        assert kube_control_requirer.has_xcp is False
        assert kube_control_requirer.get_controller_taints() == []
        assert kube_control_requirer.get_controller_labels() == []
        assert kube_control_requirer.get_api_endpoints() == []
        assert kube_control_requirer.get_default_cni() is None
        assert kube_control_requirer.cohort_keys is None
        assert kube_control_requirer.get_registry_location() is None
        assert kube_control_requirer.get_cluster_tag() is None
        assert kube_control_requirer.dns_ready() is False
        assert len(kube_control_requirer.get_dns()) == 4
        assert not any(kube_control_requirer.get_dns().values())
        assert kube_control_requirer.get_auth_credentials("bob") is None


def test_is_ready_invalid_data(kube_control_requirer, relation_data):
    relation_data["creds"] = 123
    with mock.patch.object(
        KubeControlRequirer, "relation", new_callable=mock.PropertyMock
    ) as mock_prop:
        relation = mock_prop.return_value
        relation.units = ["remote/0"]
        relation.data = {"remote/0": relation_data}
        assert kube_control_requirer.is_ready is False


def test_is_ready_success(kube_control_requirer, relation_data):
    with mock.patch.object(
        KubeControlRequirer, "relation", new_callable=mock.PropertyMock
    ) as mock_prop:
        relation = mock_prop.return_value
        relation.units = ["remote/0"]
        relation.data = {"remote/0": relation_data}
        assert kube_control_requirer.is_ready is True


def test_create_kubeconfig(kube_control_requirer, relation_data, mock_ca_cert, tmpdir):
    unit_name = kube_control_requirer.model.unit.name
    with mock.patch.object(
        KubeControlRequirer, "relation", new_callable=mock.PropertyMock
    ) as mock_prop:
        relation = mock_prop.return_value
        relation.units = ["remote/0"]
        relation.data = {"remote/0": relation_data}

        kube_config = Path(tmpdir) / "kube_config"

        # First run creates a new file
        assert not kube_config.exists()
        kube_control_requirer.create_kubeconfig(
            mock_ca_cert, kube_config, "ubuntu", unit_name
        )
        config = yaml.safe_load(kube_config.read_text())
        assert config["kind"] == "Config"
        assert config["users"][0]["user"]["token"] == "admin::redacted"

        # Second call alters existing file
        kube_config.write_text("")
        kube_control_requirer.create_kubeconfig(
            mock_ca_cert, kube_config, "ubuntu", unit_name
        )
        config = yaml.safe_load(kube_config.read_text())
        assert config["kind"] == "Config"


def test_taints_and_labels(kube_control_requirer, relation_data):
    with mock.patch.object(
        KubeControlRequirer, "relation", new_callable=mock.PropertyMock
    ) as mock_prop:
        relation = mock_prop.return_value
        relation.units = ["remote/0"]
        relation.data = {"remote/0": relation_data}
        taints = kube_control_requirer.get_controller_taints()
        labels = kube_control_requirer.get_controller_labels()
        assert taints[0].groups == (
            "node-role.kubernetes.io/control-plane",
            None,
            "NoSchedule",
        )
        assert taints[0].key == "node-role.kubernetes.io/control-plane"
        assert taints[0].value is None, "Taints may not have a value, it can be None"
        assert taints[0].effect == "NoSchedule"

        assert labels[0].groups == ("node-role.kubernetes.io/control-plane", "")
        assert labels[0].key == "node-role.kubernetes.io/control-plane"
        assert labels[0].value == "", "Labels must have a value, it can be an empty str"


def test_cluster_cidr_undefined(kube_control_requirer, relation_data):
    with mock.patch.object(
        KubeControlRequirer, "relation", new_callable=mock.PropertyMock
    ) as mock_prop:
        relation = mock_prop.return_value
        relation.units = ["remote/0"]
        relation.data = {"remote/0": relation_data}
        cidr = kube_control_requirer.get_cluster_cidr()
        assert cidr is None


def test_cluster_cidr_ipv4(kube_control_requirer, relation_data):
    with mock.patch.object(
        KubeControlRequirer, "relation", new_callable=mock.PropertyMock
    ) as mock_prop:
        relation = mock_prop.return_value
        relation_data["cluster-cidr"] = "192.168.0.0/16"
        relation.units = ["remote/0"]
        relation.data = {"remote/0": relation_data}
        cidr = kube_control_requirer.get_cluster_cidr()
        assert cidr == ip_network("192.168.0.0/16")


def test_cluster_cidr_ipv6(kube_control_requirer, relation_data):
    with mock.patch.object(
        KubeControlRequirer, "relation", new_callable=mock.PropertyMock
    ) as mock_prop:
        relation = mock_prop.return_value
        relation_data["cluster-cidr"] = "2002:0:0:1234::0/64"
        relation.units = ["remote/0"]
        relation.data = {"remote/0": relation_data}
        cidr = kube_control_requirer.get_cluster_cidr()
        assert cidr == ip_network("2002:0:0:1234::0/64")

