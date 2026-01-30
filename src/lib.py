from encodings.hex_codec import hex_encode
import logging
import time
from typing import Callable, TypeAlias, override
import attrs
from bluepy.btle import Peripheral, DefaultDelegate, Characteristic, Service
from construct import Array, Byte, Bytes, ExprAdapter, PascalString, Short, Struct

logger = logging.getLogger("ecoworthy-lib")


class JbdAbi:
    service_uuid = 0xFF00
    characteristic_uuid = 0xFF02

    query_basic_info = b"\xdd\xa5\x03\x00\xff\xfd\x77"
    query_basic_info_resp_prefix = b"\xdd\x03"

    query_voltages = b"\xdd\xa5\x04\x00\xff\xfc\x77"
    query_voltages_resp_prefix = b"\xdd\x04"

    hardware_info = b"\xdd\xa5\x05\x00\xff\xfb\x77"
    hardware_info_resp_prefix = b"\xdd\x05"

    query_voltages_resp = Struct(
        "start_bit" / Bytes(1),
        "state_bit" / Bytes(1),
        "status" / Bytes(1),
        "length" / Byte,  # type: ignore
        "cells_mv" / Array(lambda ctx: ctx["length"] // 2, Short),
        "checksum" / Bytes(2),
        "end_bit" / Byte,  # type: ignore
    )

    NTCValueC = ExprAdapter(
        Short,
        decoder=lambda n, _: (n - 2731) / 10.0,
        encoder=lambda v, _: int(v * 10 + 2731),
    )

    basic_info_resp = Struct(
        "start_bit" / Bytes(1),
        "state_bit" / Bytes(1),
        "status" / Bytes(1),
        "length" / Byte,  # type: ignore
        "total_10mv" / Short,  # type: ignore
        "current_10ma" / Short,  # type: ignore
        "remaining_capacity_10mah" / Short,  # type: ignore
        "nominal_capacity_10mah" / Short,  # type: ignore
        "cycles" / Short,  # type: ignore
        "prod_date" / Short,  # type: ignore
        "equilibrium" / Bytes(4),
        "prot_status" / Short,  # type: ignore
        "sw_version" / Byte,  # type: ignore
        "remaining_soc" / Byte,  # type: ignore
        "fet_status" / Byte,  # type: ignore
        "n_cells" / Byte,  # type: ignore
        "n_ntc" / Byte,  # type: ignore
        "ntc_vals_c" / Array(lambda ctx: ctx["n_ntc"], NTCValueC),
        "checksum" / Bytes(2),
        "end_bit" / Byte,  # type: ignore
    )

    hardware_info_resp = Struct(
        "start_bit" / Bytes(1),
        "state_bit" / Bytes(1),
        "status" / Bytes(1),
        "name" / PascalString(Byte, "ascii"),
        "checksum" / Bytes(2),
        "end_bit" / Byte,  # type: ignore
    )


@attrs.define()
class JbdBasicInfo:
    battery_voltage: float  # In V
    active_current: float  # In A
    remaining_capacity: float  # In Ah
    nominal_capacity: float  # In Ah
    cycles: int
    soc: int  # 0-100%
    n_cells: int  # Typically 16
    ntc_temps: list[float]  # In degrees celsius


@attrs.define()
class JbdCellVoltages:
    cells_v: list[float]  # In V


@attrs.define()
class JbdHardwareInfo:
    mac: str
    name: str


JbdEvent: TypeAlias = JbdBasicInfo | JbdCellVoltages | JbdHardwareInfo


@attrs.define()
class JbdDelegate(DefaultDelegate):
    device_mac: str
    _on_event: Callable[[JbdEvent], None]

    _buffer: bytearray = attrs.field(init=False, factory=bytearray)

    @override
    def handleNotification(self, cHandle, data: bytes):
        logger.debug("Got data %s", hex_encode(data)[0])

        self._buffer.extend(data)

    def consume(self):
        data = bytes(self._buffer)
        self._buffer.clear()

        match data[0:2]:
            case JbdAbi.query_voltages_resp_prefix:
                try:
                    obj = JbdAbi.query_voltages_resp.parse(data)

                    if obj is None:
                        logger.debug(
                            "Failed to parse object with data %s",
                            hex_encode(data)[0].decode(),
                        )
                        return

                    logger.debug("Got object %s", obj)

                    event = JbdCellVoltages(
                        cells_v=[mv / 1000.0 for mv in obj["cells_mv"]]
                    )

                    self._on_event(event)
                except Exception:
                    logger.info("Failed to parse cell voltage data", exc_info=True)

            case JbdAbi.query_basic_info_resp_prefix:
                try:
                    obj = JbdAbi.basic_info_resp.parse(data)

                    if obj is None:
                        logger.debug(
                            "Failed to parse object with data %s",
                            hex_encode(data)[0].decode(),
                        )
                        return

                    logger.debug("Got object %s", obj)

                    event = JbdBasicInfo(
                        battery_voltage=obj["total_10mv"] / 100.0,
                        active_current=obj["current_10ma"] / 100.0,
                        remaining_capacity=obj["remaining_capacity_10mah"] / 100.0,
                        nominal_capacity=obj["nominal_capacity_10mah"] / 100.0,
                        cycles=obj["cycles"],
                        soc=obj["remaining_soc"],
                        n_cells=obj["n_cells"],
                        ntc_temps=list(obj["ntc_vals_c"]),
                    )

                    self._on_event(event)
                except Exception:
                    logger.info("Failed to parse basic info", exc_info=True)

            case JbdAbi.hardware_info_resp_prefix:
                try:
                    obj = JbdAbi.hardware_info_resp.parse(data)

                    if obj is None:
                        logger.debug(
                            "Failed to parse object with data %s",
                            hex_encode(data)[0].decode(),
                        )
                        return

                    logger.debug("Got object %s", obj)

                    event = JbdHardwareInfo(mac=self.device_mac, name=str(obj["name"]))

                    self._on_event(event)
                except Exception:
                    logger.info("Failed to parse basic info", exc_info=True)

            case _:
                if len(data) != 0:
                    logger.error(
                        "Received garbage data: %s", hex_encode(data)[0].decode()
                    )


def poll_device(
    mac: str, callback: Callable[[JbdEvent], None], cancelled: Callable[[], bool]
):
    try:
        device = Peripheral(mac)
    except Exception:
        logger.error("Failed to connect to device", exc_info=True)
        return

    delegate = JbdDelegate(mac, callback)
    device.withDelegate(delegate)

    service: Service = device.getServiceByUUID(JbdAbi.service_uuid)
    characteristic: Characteristic = service.getCharacteristics(
        JbdAbi.characteristic_uuid
    )[0]

    logger.info("Connected, polling")

    def sink_data():
        while True:
            if not device.waitForNotifications(0.1):
                break

        delegate.consume()

    # Identify ourselves first
    characteristic.write(JbdAbi.hardware_info)
    sink_data()

    time.sleep(1)

    while not cancelled():
        # Issue our device command, then collect our response
        characteristic.write(JbdAbi.query_basic_info)
        sink_data()

        time.sleep(1)

        characteristic.write(JbdAbi.query_voltages)
        sink_data()

        time.sleep(1)

    device.disconnect()
