# Rinnai Boiler for Home Assistant

Home Assistant integration for Rinnai gas boilers controlled by a **WF-100W / WF-S100** Wi-Fi room controller
(sold in Russia/Kazakhstan as *Rinnai Smart IoT* / «Смарт управление», in Korea as *Rinnai Smart Boiler*).

Tested on **RBK-197 RTU** with a **WF-100W-RU** controller.

## Two ways to run

| Mode | How it works | Needs internet |
|---|---|---|
| **Cloud** | Home Assistant polls the Rinnai cloud the same way the phone app does | yes |
| **Local** | The controller talks to Home Assistant instead of the cloud | **no** |

The integration switches automatically: as soon as the controller registers on the built-in local
server, Home Assistant stops using the cloud. The `Источник` / `Source` sensor shows which one is active.

## Entities

* `climate` — heating (current room temperature, setpoint 10–40 °C, on/off)
* `water_heater` — domestic hot water (current temperature, setpoint 35–60 °C, on/off)
* `number` — heating circuit water temperature (20–80 °C)
* `sensor` — room temperature, hot water temperature, circuit setpoint, mode, burner state,
  **error code**, schedule, data source
* `binary_sensor` — fault, hot water flowing, controller offline
* `switch` — power, heating, hot water, circuit mode, away, economy, night

`climate` and `water_heater` work with the HomeKit bridge, so the boiler shows up in Apple Home.

## Installation

1. Copy `custom_components/rinnai` into your Home Assistant `config/custom_components/`
   (or add this repository to HACS as a custom repository).
2. Restart Home Assistant.
3. *Settings → Devices & Services → Add Integration → Rinnai*.
4. Enter:
   * **RoomControlId** — the Wi-Fi MAC address of the controller, 12 hex characters,
     e.g. `bcff4d3b2f6b`. Find it in your router's client list (the device is usually
     called `Thermostat`).
   * **DeviceId** — the UUID of a phone already registered in the Rinnai app.
     The cloud rejects an unknown DeviceId, so it must be an existing one.
     Capture it with any HTTPS sniffer (HTTP Catcher, Proxyman) from a request to
     `wifiboilers1.rinnai.co.kr`.

No password is stored: the API authenticates by these two headers only.

## Going cloud-free (optional)

The controller resolves `wifiboilers1.rinnai.co.kr` and connects to port **9105**.
Point that name at your Home Assistant and it will talk to the built-in server instead.

1. Add a static DNS record on your router: `wifiboilers1.rinnai.co.kr` → *Home Assistant IP*.
   Make sure there is **exactly one** record for that name.
2. Make the controller re-resolve it. It caches the address in RAM, so simply dropping the
   connection is not enough — restart the Wi-Fi access point (or power-cycle the controller).
3. The `Source` sensor turns to *Local*. Nothing leaves your network any more.

Note: while the controller is local, the official Rinnai phone app can no longer see the boiler.

## Protocol notes

Packets are ASCII: `<prefix:6><command:2><length:2><data><checksum:2>7d`, where `length` counts
**hex characters** of `data` and the checksum is `sum(ord(c) for c in data) % 256`.
The cloud HTTP API always sends `00` instead of a real checksum; the controller does not — it
rejects replies with a wrong one.

Controller endpoints (port 9105, plain HTTP):

* `POST /register` — `re0000` + MAC + product code. Reply `re0100` + any 32-character token.
* `POST /state` — `re0101` + full status. The reply must echo the payload; to send a command,
  change the prefix to `sm0101` and patch the bytes you want.

**This integration never rebuilds the status payload from parsed fields** — it patches only the
bytes it intends to change and echoes everything else verbatim, so unknown fields of a gas
appliance can never be corrupted.

Known status bytes: `0` flags (`0x01` power, `0x02` circuit mode, `0x04` heating, `0x08` hot water,
`0x10` preheat, `0x20` quick heat), `1` room setpoint, `2` circuit setpoint, `3` hot water setpoint,
`4` room temperature, `5` hot water temperature, `6` burner/flow status
(`&0x0f` combustion, `0x20` hot water flowing), `7–8` error code (`ffff` = none), `9` away.
Temperatures with bit `0x80` set carry an extra half degree.

Cloud commands (`POST /control`): `01` flags, `02` room setpoint, `03` circuit setpoint,
`04` hot water setpoint, `05` away, `07` economy, `08` night.

## Credits

Protocol groundwork: [mog422/open-rinnai-server](https://github.com/mog422/open-rinnai-server)
and [zobithecat/rinnai-ha](https://github.com/zobithecat/rinnai-ha).

## Disclaimer

This controls a **gas appliance**. It is not affiliated with or endorsed by Rinnai.
Use at your own risk.

## License

MIT
