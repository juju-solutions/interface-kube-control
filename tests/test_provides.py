import pytest
from unittest.mock import MagicMock
import provides
from models import Taint, Label, Effect


def test_set_default_cni():
    provider = provides.KubeControlProvider()
    provider.relations = [MagicMock(), MagicMock()]
    provider.set_default_cni("test")
    for relation in provider.relations:
        relation.to_publish.__setitem__.assert_called_once_with("default-cni", "test")


@pytest.mark.parametrize(
    "taints, expected",
    [
        ([], []),
        (
            [Taint("test.io/key", "value", Effect.NoSchedule)],
            ["test.io/key=value:NoSchedule"],
        ),
        (
            ["test.io/key=value:NoSchedule"],
            ["test.io/key=value:NoSchedule"],
        ),
    ],
    ids=["empty", "single object taint", "single str taint"],
)
def test_set_taints(taints, expected):
    provider = provides.KubeControlProvider()
    provider.relations = [MagicMock(), MagicMock()]
    assert provider.set_controller_taints(taints)
    for relation in provider.relations:
        relation.to_publish.__setitem__.assert_called_once_with("taints", expected)


@pytest.mark.parametrize(
    "labels, expected",
    [
        ([], []),
        (
            [Label("test.io/key", "value")],
            ["test.io/key=value"],
        ),
        (
            ["test.io/key=value"],
            ["test.io/key=value"],
        ),
    ],
    ids=["empty", "single object label", "single str label"],
)
def test_set_labels(labels, expected):
    provider = provides.KubeControlProvider()
    provider.relations = [MagicMock(), MagicMock()]
    assert provider.set_controller_labels(labels)
    for relation in provider.relations:
        relation.to_publish.__setitem__.assert_called_once_with("labels", expected)
