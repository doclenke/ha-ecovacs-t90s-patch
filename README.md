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

## Install

1. Add this repository to HACS / the Marketplace as a custom repository (category *Integration*) and download it.
2. Restart Home Assistant.
3. Settings → Devices & services → Add integration → **Ecovacs T90S Patch**.
4. The patch reloads the Ecovacs integration; the T90S then appears as a device with its map image.

## Remove

Once the installed `deebot-client` knows `298z64`, the patch does nothing and shows a
notification. Then delete the integration entry, uninstall it in HACS / the Marketplace and restart.

## Caveats

- Uses internal registries of `deebot-client`; a library update may break the patch. It
  then logs an error and does nothing.
- Room cleaning through `vacuum.clean_area` reportedly fails on this model (error 20011),
  see the upstream PR.
