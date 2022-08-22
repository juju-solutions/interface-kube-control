import requires
from models import Taint, Effect, Label
import pytest


def test_get_default_cni():
    requirer = requires.KubeControlRequirer()
    requirer.all_joined_units.received = {"default-cni": "test"}
    assert requirer.get_default_cni() == "test"


@pytest.mark.parametrize(
    "relation_field, expected",
    [
        ([], []),
        (
            ["test.io/key=value:NoSchedule"],
            [Taint("test.io/key", "value", Effect.NoSchedule)],
        ),
        (
            ["test.io/key:NoSchedule"],
            [Taint("test.io/key", None, Effect.NoSchedule)],
        ),
    ],
    ids=["empty", "single taint", "label without empty value"],
)
def test_get_taints(relation_field, expected):
    requirer = requires.KubeControlRequirer()
    requirer.all_joined_units.received = {"taints": relation_field}
    assert requirer.get_controller_taints() == expected


@pytest.mark.parametrize(
    "relation_field, expected",
    [
        ([], []),
        (
            ["test.io/key=value"],
            [Label("test.io/key", "value")],
        ),
        (
            ["test.io/key="],
            [Label("test.io/key", "")],
        ),
    ],
    ids=["empty", "single label", "label without empty value"],
)
def test_get_labels(relation_field, expected):
    requirer = requires.KubeControlRequirer()
    requirer.all_joined_units.received = {"labels": relation_field}
    assert requirer.get_controller_labels() == expected
