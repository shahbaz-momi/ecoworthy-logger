from prometheus_client import Gauge

from lib import JbdBasicInfo, JbdCellVoltages, JbdHardwareInfo

LABELS = ["name", "mac"]

battery_voltage = Gauge(
    "battery_voltage_volts",
    "Battery pack voltage",
    LABELS,
)

battery_current = Gauge(
    "battery_current_amperes",
    "Battery current (positive = discharge)",
    LABELS,
)

battery_remaining_capacity = Gauge(
    "battery_remaining_capacity_ampere_hours",
    "Remaining battery capacity",
    LABELS,
)

battery_nominal_capacity = Gauge(
    "battery_nominal_capacity_ampere_hours",
    "Nominal battery capacity",
    LABELS,
)

battery_cycles = Gauge(
    "battery_cycles_total",
    "Battery charge/discharge cycles",
    LABELS,
)

battery_soc = Gauge(
    "battery_state_of_charge_percent",
    "Battery state of charge",
    LABELS,
)

battery_cells_total = Gauge(
    "battery_cells_total",
    "Number of cells in battery",
    LABELS,
)

battery_ntc_temp = Gauge(
    "battery_ntc_temperature_celsius",
    "NTC temperature sensors",
    LABELS + ["index"],
)

battery_cell_voltage = Gauge(
    "battery_cell_voltage_volts",
    "Individual cell voltages",
    LABELS + ["index"],
)


def publish_basic_info(hw: JbdHardwareInfo, info: JbdBasicInfo):
    labels = dict(name=hw.name, mac=hw.mac)

    battery_voltage.labels(**labels).set(info.battery_voltage)
    battery_current.labels(**labels).set(info.active_current)
    battery_remaining_capacity.labels(**labels).set(info.remaining_capacity)
    battery_nominal_capacity.labels(**labels).set(info.nominal_capacity)
    battery_cycles.labels(**labels).set(info.cycles)
    battery_soc.labels(**labels).set(info.soc)
    battery_cells_total.labels(**labels).set(info.n_cells)

    for i, temp in enumerate(info.ntc_temps):
        battery_ntc_temp.labels(
            **labels,
            index=str(i),
        ).set(temp)


def publish_cell_voltages(hw: JbdHardwareInfo, cells: JbdCellVoltages):
    labels = dict(name=hw.name, mac=hw.mac)

    for i, v in enumerate(cells.cells_v):
        battery_cell_voltage.labels(
            **labels,
            index=str(i),
        ).set(v)
