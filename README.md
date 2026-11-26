# Ecovacs T90S Patch

Temporary Home Assistant integration that makes the built-in **Ecovacs** integration
recognise the **DEEBOT T90S PRO OMNI** (device class `298z64`), including its map.

Home Assistant's Ecovacs integration uses the `deebot-client` library, which does not
know this device class yet and logs:

> Device class "298z64" not recognized

Upstream support is pending in
[DeebotUniverse/client.py#2012](https://github.com/DeebotUniverse/client.py/pull/2012).
This patch registers the same definition at runtime: the DEEBOT T90 PRO OMNI (`twunby`)
capabilities with the V2 clean commands (`CleanV2` / `CleanAreaV2`), which the PR author
validated on the hardware.

It also fixes the map: the T90S sends its map outline (`getMapInfo_V2` /
`onMapInfo_V2`) with `outlineVer: "2"`. The payload has the same layout as version 1
(outline, rooms, block lines), but `deebot-client` only accepts version 1 and silently drops
everything else, so the map image entity never gets an image (HTTP 500 on the image proxy).
The patch treats version 2 like version 1. It checks first whether the installed library
already accepts version 2 and then leaves it alone.

## Install

1. Add this repository to HACS / the Marketplace as a custom repository (category *Integration*) and download it.
2. Restart Home Assistant.
3. Settings → Devices & services → Add integration → **Ecovacs T90S Patch**.
4. The patch reloads the Ecovacs integration; the T90S then appears as a device with its map image.

## Remove

Once the installed `deebot-client` knows `298z64` and accepts map outline version 2, the
patch does nothing and shows a notification. If only the device class is supported, it keeps
fixing the map. Then delete the integration entry, uninstall it in HACS / the Marketplace and restart.

## Caveats

- Uses internal registries of `deebot-client`; a library update may break the patch. It
  then logs an error and does nothing.
- Room cleaning through `vacuum.clean_area` reportedly fails on this model (error 20011),
  see the upstream PR.
