"""Test Control4 Light."""

from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest_homeassistant.common import MockConfigEntry

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_SUPPORTED_COLOR_MODES,
    ColorMode,
)
from homeassistant.const import STATE_ON, Platform
from homeassistant.core import HomeAssistant

from . import setup_integration

RELAY_ENTITY_ID = "light.test_controller_hallway_relay"
DIMMER_ENTITY_ID = "light.test_controller_kitchen_dimmer"


@pytest.fixture
def platforms() -> list[Platform]:
    """Platforms which should be loaded during the test."""
    return [Platform.LIGHT]


def _mock_director_variables(
    mock_c4_director: MagicMock, rows: list[dict[str, Any]]
) -> None:
    """Make the director answer like pyControl4, including the empty response."""

    async def _get_all_item_variable_value(
        var_names: set[str],
    ) -> list[dict[str, Any]]:
        matching_rows = [row for row in rows if row["varName"] in var_names]
        if not matching_rows:
            raise ValueError(
                f"Empty response received from Director! The variable {var_names} "
                "doesn't seem to exist for any items."
            )
        return matching_rows

    mock_c4_director.get_all_item_variable_value.side_effect = (
        _get_all_item_variable_value
    )


@pytest.mark.usefixtures("mock_c4_account")
async def test_lights_without_dimmers(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_c4_director: MagicMock,
) -> None:
    """Test on/off lights are created when no light has dimmer variables."""
    _mock_director_variables(
        mock_c4_director, [{"id": 345, "varName": "LIGHT_STATE", "value": 1}]
    )

    await setup_integration(hass, mock_config_entry)

    state = hass.states.get(RELAY_ENTITY_ID)
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.ONOFF]
    assert hass.states.get(DIMMER_ENTITY_ID) is None


@pytest.mark.usefixtures("mock_c4_account")
async def test_lights_without_non_dimmers(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_c4_director: MagicMock,
) -> None:
    """Test dimmer lights are created when no light has the on/off variable."""
    _mock_director_variables(
        mock_c4_director, [{"id": 346, "varName": "LIGHT_LEVEL", "value": 50}]
    )

    await setup_integration(hass, mock_config_entry)

    state = hass.states.get(DIMMER_ENTITY_ID)
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes[ATTR_SUPPORTED_COLOR_MODES] == [ColorMode.BRIGHTNESS]
    assert state.attributes[ATTR_BRIGHTNESS] == 127
    assert hass.states.get(RELAY_ENTITY_ID) is None
