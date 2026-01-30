import logging
import signal
import sys
from threading import Event
from typing import Annotated
from typer import Typer
import typer

from lib import poll_device

app = Typer()
logger = logging.getLogger("eco-sense")


@app.command()
def main(
    mac: Annotated[str, typer.Option("-m")],
):
    cancelled = Event()
    signal.signal(signal.SIGTERM, lambda _, __: cancelled.set())

    poll_device(mac, lambda ev: logger.info("%s", str(ev)), lambda: cancelled.is_set())


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s.%(msecs)03d %(name)-12s %(levelname)-8s %(message)s",
        stream=sys.stdout,
    )


if __name__ == "__main__":
    configure_logging()
    app()
