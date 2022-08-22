import pytest
from unittest.mock import MagicMock
import provides
from models import DecodeError, Taint, Label, Effect


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
        (
            ["test.io/key:NoSchedule"],
            ["test.io/key:NoSchedule"],
        ),
        (
            ["test.io/key=:NoSchedule"],
            ["test.io/key=:NoSchedule"],
        ),
    ],
    ids=[
        "empty",
        "single object taint",
        "single str taint",
        "taint without value",
        "taint with empty string value",
    ],
)
def test_set_taints(taints, expected):
    provider = provides.KubeControlProvider()
    provider.relations = [MagicMock(), MagicMock()]
    assert provider.set_controller_taints(taints) is provider
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
        (
            ["test.io/key="],
            ["test.io/key="],
        ),
    ],
    ids=["empty", "single object label", "single str label", "empty label value"],
)
def test_set_labels(labels, expected):
    provider = provides.KubeControlProvider()
    provider.relations = [MagicMock(), MagicMock()]
    assert provider.set_controller_labels(labels) is provider
    for relation in provider.relations:
        relation.to_publish.__setitem__.assert_called_once_with("labels", expected)


@pytest.mark.parametrize(
    "taint",
    [
        "missing colon",
        "too:many:colons",
        "bad:effect",
        "too=many=equals:NoSchedule",
    ],
)
def test_set_taint_failure(taint):
    provider = provides.KubeControlProvider()
    with pytest.raises(DecodeError):
        provider.set_controller_taints([taint])


@pytest.mark.parametrize("label", ["missing equals", "too=many=equals"])
def test_set_label_failure(label):
    provider = provides.KubeControlProvider()
    with pytest.raises(DecodeError):
        provider.set_controller_labels([label])
