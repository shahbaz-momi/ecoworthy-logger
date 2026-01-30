## Ecoworthy logger

Tired of your batteries connecting to arbitrary Chinese servers? Well look no further. This is a simple utility that connects via Bluetooth
to your Ecoworthy batteries and exposes them either via a simple command line log, or via Prometheus for use in Grafana, etc.

This can be useful when setting up dashboards to monitor battery balance, thermals, and state of charge.

Bluetooth only for now; feel free to contribute CAN/RS485 support.

#### Tested batteries

- Ecoworthy 48V Server Rack Batteries - V3

#### Tested hardware

- Raspberry Pi Zero W

Anything that supports Bluetooth should theoretically work.

### How to run

You can run in two modes:

#### Logging mode

```bash
uv run src/main.py log -m AA:BB:CC:DD:EE:FF
```

This starts the logger which will output to the command line, e.g.

```
2026-01-30 01:13:10,968.968 ecoworthy-lib INFO     Connected, polling
2026-01-30 01:13:12,182.182 ecoworthy-logger INFO     JbdHardwareInfo(mac='AA:C2:37:06:5D:99', name='ECO-LFP48100-3U-065D99')
2026-01-30 01:13:13,293.293 ecoworthy-logger INFO     JbdBasicInfo(battery_voltage=54.11, active_current=0.0, remaining_capacity=99.2, nominal_capacity=100.0, cycles=0, soc=99, n_cells=16, ntc_temps=[9.4, 10.9, 8.3, 7.1, 12.5, 12.4])
2026-01-30 01:13:14,401.401 ecoworthy-logger INFO     JbdCellVoltages(cells_v=[3.391, 3.394, 3.392, 3.386, 3.385, 3.385, 3.384, 3.381, 3.381, 3.381, 3.38, 3.378, 3.375, 3.374, 3.374, 3.374])
2026-01-30 01:13:15,510.510 ecoworthy-logger INFO     JbdBasicInfo(battery_voltage=54.11, active_current=0.0, remaining_capacity=99.2, nominal_capacity=100.0, cycles=0, soc=99, n_cells=16, ntc_temps=[9.4, 10.9, 8.3, 7.1, 12.5, 12.5])
2026-01-30 01:13:16,619.619 ecoworthy-logger INFO     JbdCellVoltages(cells_v=[3.391, 3.394, 3.392, 3.386, 3.384, 3.385, 3.383, 3.381, 3.38, 3.381, 3.38, 3.378, 3.374, 3.373, 3.374, 3.374])
2026-01-30 01:13:17,728.728 ecoworthy-logger INFO     JbdBasicInfo(battery_voltage=54.11, active_current=0.0, remaining_capacity=99.2, nominal_capacity=100.0, cycles=0, soc=99, n_cells=16, ntc_temps=[9.4, 10.9, 8.3, 7.1, 12.5, 12.5])
2026-01-30 01:13:18,836.836 ecoworthy-logger INFO     JbdCellVoltages(cells_v=[3.391, 3.394, 3.392, 3.386, 3.385, 3.385, 3.384, 3.381, 3.381, 3.381, 3.38, 3.378, 3.374, 3.373, 3.374, 3.374])
2026-01-30 01:13:19,945.945 ecoworthy-logger INFO     JbdBasicInfo(battery_voltage=54.11, active_current=0.0, remaining_capacity=99.2, nominal_capacity=100.0, cycles=0, soc=99, n_cells=16, ntc_temps=[9.4, 10.9, 8.3, 7.1, 12.5, 12.5])
```

#### Publish mode

```bash

uv run src/main.py publish [-p port] [-h host] -m AA:BB:CC:DD:EE:FF [-m ...]
```

This starts a Prometheus metrics server which can be accessed via http://host:port/metrics.

### Grafana

With this, it is quite trivial to setup a nice dashboard:
![Grafana Dashboard 1](https://raw.githubusercontent.com/shahbaz-momi/ecoworthy-logger/main/media/grafana1.png)
![Grafana Dashboard 2](https://raw.githubusercontent.com/shahbaz-momi/ecoworthy-logger/main/media/grafana2.png)
