"""Shared fixtures."""

import pytest
from pytest_homeassistant_custom_component.syrupy import HomeAssistantSnapshotExtension
from syrupy.assertion import SnapshotAssertion


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Load custom_components/huawei_lte instead of the built-in one."""
    return


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Pin the Home Assistant snapshot extension (core layout: snapshots/).

    Which `snapshot` fixture wins otherwise depends on plugin load order,
    which differs between environments.
    """
    return snapshot.use_extension(HomeAssistantSnapshotExtension)
