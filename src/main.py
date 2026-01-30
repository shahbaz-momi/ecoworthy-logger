from concurrent.futures import ThreadPoolExecutor
import logging
import signal
import sys
from threading import Event
from typing import Annotated
from typer import Typer
import typer
import multiprocessing as mp
from prometheus_client import start_http_server


from lib import JbdBasicInfo, JbdCellVoltages, JbdEvent, JbdHardwareInfo, poll_device
from metrics import publish_basic_info, publish_cell_voltages

app = Typer()
logger = logging.getLogger("ecoworthy-logger")

mp.set_start_method("spawn", force=True)


@app.command()
def log(
    mac: Annotated[
        str, typer.Option("-m", help="MAC address of the battery to connect to")
    ],
):
    """
    Collect and log battery events to the command line. Always begins with a JbdHardwareInfo, followed by JbdBasicInfo and JbdCellVoltage events in a loop that lasts forever.
    """

    cancelled = Event()
    signal.signal(signal.SIGINT, lambda _, __: cancelled.set())
    signal.signal(signal.SIGTERM, lambda _, __: cancelled.set())

    poll_device(mac, lambda ev: logger.info("%s", str(ev)), lambda: cancelled.is_set())


@app.command()
def publish(
    macs: Annotated[
        list[str],
        typer.Option(
            "-m",
            help="MAC address of the batteries to connect to. Note that your device may have limits to how many devices can be concurrently connected; usually that is 3.",
        ),
    ],
    host: Annotated[
        str,
        typer.Option(
            "-h",
            help="Host address to bind to. Will restrict prometheus server availability to this host only.",
        ),
    ] = "0.0.0.0",
    port: Annotated[
        int, typer.Option("-p", help="Port to publish /metrics to.")
    ] = 8080,
):
    cancelled = Event()
    signal.signal(signal.SIGINT, lambda _, __: cancelled.set())
    signal.signal(signal.SIGTERM, lambda _, __: cancelled.set())

    def worker(mac: str):
        hardware_info: JbdHardwareInfo | None = None

        def submit_event(ev: JbdEvent):
            nonlocal hardware_info

            match ev:
                case JbdHardwareInfo():
                    hardware_info = ev

                case JbdBasicInfo():
                    assert hardware_info is not None
                    publish_basic_info(hardware_info, ev)

                case JbdCellVoltages():
                    assert hardware_info is not None
                    publish_cell_voltages(hardware_info, ev)

        poll_device(mac, submit_event, lambda: cancelled.is_set())

    # Host our metrics server
    logger.info("Starting server at http://%s:%d/metrics", host, port)
    start_http_server(port, addr=host)

    # Spawn a new process per mac
    with ThreadPoolExecutor(max_workers=len(macs)) as pool:
        for mac in macs:
            pool.submit(worker, mac)

        cancelled.wait()


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s.%(msecs)03d %(name)-12s %(levelname)-8s %(message)s",
        stream=sys.stdout,
    )


if __name__ == "__main__":
    configure_logging()
    app()
