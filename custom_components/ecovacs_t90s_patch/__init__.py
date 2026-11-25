"""Temporary patch: teach the built-in Ecovacs integration the DEEBOT T90S PRO OMNI.

deebot-client (the library behind Home Assistant's Ecovacs integration) does not
know the device class "298z64" yet. Upstream support is pending in
https://github.com/DeebotUniverse/client.py/pull/2012, which defines the T90S
as the T90 PRO OMNI ("twunby") with the V2 clean commands.

This integration registers exactly that definition at runtime and then reloads
the Ecovacs config entries so the device is picked up. As soon as the installed
deebot-client ships its own definition, the patch does nothing and raises a
notification saying it can be removed.
"""

from __future__ import annotations

import dataclasses
import importlib
import logging

from homeassistant.components import persistent_notification
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import CoreState, Event, HomeAssistant, callback

from .const import BASE_CLASS, DOMAIN, ECOVACS_DOMAIN, PATCHED_CLASSES, UPSTREAM_PR

_LOGGER = logging.getLogger(__name__)

NOTIFICATION_ID = f"{DOMAIN}_status"


def _official_support_available() -> bool:
    """Return True if the installed deebot-client already knows our classes."""
    for class_ in PATCHED_CLASSES:
        try:
            importlib.import_module(f"deebot_client.hardware.{class_}")
        except ModuleNotFoundError:
            return False
    return True


def _build_device_info():  # noqa: ANN202 - types live in deebot_client
    """Build the T90S device info: T90 PRO OMNI capabilities with V2 clean commands."""
    from deebot_client.capabilities import CapabilityCleanAction
    from deebot_client.commands.json.clean import CleanAreaV2, CleanV2

    base = importlib.import_module(f"deebot_client.hardware.{BASE_CLASS}")
    info = base.get_device_info()
    caps = info.capabilities
    clean = dataclasses.replace(
        caps.clean,
        action=CapabilityCleanAction(command=CleanV2, area=CleanAreaV2),
    )
    return dataclasses.replace(
        info, capabilities=dataclasses.replace(caps, clean=clean)
    )


def _apply_patch() -> list[str]:
    """Register the device info in deebot-client's hardware registry.

    Runs in the executor because it imports modules.
    """
    from deebot_client import hardware

    info = _build_device_info()
    patched: list[str] = []
    for class_ in PATCHED_CLASSES:
        hardware._DEVICES[class_] = info  # noqa: SLF001
        hardware._NOT_FOUND.discard(class_)  # noqa: SLF001
        patched.append(class_)
    return patched


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up the patch."""
    if await hass.async_add_executor_job(_official_support_available):
        _LOGGER.warning(
            "deebot-client supports %s natively now; this patch is no longer "
            "needed and can be removed",
            ", ".join(PATCHED_CLASSES),
        )
        persistent_notification.async_create(
            hass,
            "Die eingebaute Ecovacs-Integration unterstützt den DEEBOT T90S PRO "
            "OMNI jetzt selbst. Der Patch macht nichts mehr und kann entfernt "
            "werden: Integration „Ecovacs T90S Patch“ löschen und im Marketplace "
            "deinstallieren.",
            title="Ecovacs T90S Patch nicht mehr nötig",
            notification_id=NOTIFICATION_ID,
        )
        return True

    try:
        patched = await hass.async_add_executor_job(_apply_patch)
    except Exception:
        _LOGGER.exception(
            "Could not patch deebot-client; the library layout may have changed. "
            "See %s",
            UPSTREAM_PR,
        )
        return False

    _LOGGER.warning(
        "Registered device classes %s in deebot-client (temporary patch, see %s)",
        ", ".join(patched),
        UPSTREAM_PR,
    )

    @callback
    def _reload_ecovacs(_: Event | None = None) -> None:
        for ecovacs_entry in hass.config_entries.async_entries(ECOVACS_DOMAIN):
            if ecovacs_entry.state is ConfigEntryState.LOADED:
                _LOGGER.info("Reloading Ecovacs entry %s", ecovacs_entry.title)
                hass.config_entries.async_schedule_reload(ecovacs_entry.entry_id)

    # The Ecovacs entries may already have asked the cloud for their devices
    # before the patch was in place; a reload makes them ask again.
    if hass.state is CoreState.running:
        _reload_ecovacs()
    else:
        entry.async_on_unload(
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _reload_ecovacs)
        )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the patch.

    The registry entry stays until the next restart; nothing else to undo.
    """
    return True
