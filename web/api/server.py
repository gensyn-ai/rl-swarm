import argparse
import logging
import os
from datetime import datetime, timedelta

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pythonjsonlogger import jsonlogger

from hivemind_exp.chain_utils import ModalSwarmCoordinator, setup_web3
from hivemind_exp.dht_utils import *
from hivemind_exp.name_utils import *

from . import global_dht
from .dht_pub import GossipDHTPublisher
from .kinesis import Kinesis


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message):
        # Ensure that 'extra' fields are included in the log record
        super().add_fields(log_record, record, message)

        # Include both adapter extra fields and log call extra fields
        if hasattr(record, "extra_fields"):
            for key, value in record.extra_fields.items():
                log_record[key] = value


json_formatter = CustomJsonFormatter("%(asctime)s %(levelname)s %(message)s")

# Configure the root logger
root_logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(json_formatter)
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

# Get the module logger
logger = logging.getLogger(__name__)

app = FastAPI()
port = os.getenv("SWARM_UI_PORT", "8000")

try:
    port = int(port)
except ValueError:
    logger.warning(f"invalid port {port}. Defaulting to 8000")
    port = 8000

config = uvicorn.Config(
    app,
    host="0.0.0.0",
    port=port,
    timeout_keep_alive=10,
    timeout_graceful_shutdown=10,
    h11_max_incomplete_event_size=8192,  # Max header size in bytes
)

server = uvicorn.Server(config)


@app.exception_handler(Exception)
async def internal_server_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "message": str(exc),
        },
    )


@app.get("/api/healthz")
async def get_health():
    lpt = global_dht.dht_cache.get_last_polled()
    if lpt is None:
        raise HTTPException(status_code=500, detail="dht never polled")

    diff = datetime.now() - lpt
    if diff > timedelta(minutes=5):
        raise HTTPException(status_code=500, detail="dht last poll exceeded 5 minutes")

    return {
        "message": "OK",
        "lastPolled": diff,
    }


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-ip", "--initial_peers", help="initial peers", nargs="+", type=str, default=[]
    )
    return parser.parse_args()


def main(args):
    contract_addr = os.getenv("CONTRACT_ADDRESS")

    if contract_addr is None:
        raise Exception("CONTRACT_ADDRESS is required in environment")

    coordinator = ModalSwarmCoordinator(
        setup_web3(), contract_addr, org_id=""
    )  # Only allows contract calls
    initial_peers = coordinator.get_bootnodes()

    # Supplied with the bootstrap node, the client will have access to the DHT.
    logger.info(f"initializing DHT with peers {initial_peers}")

    kinesis_stream = os.getenv("KINESIS_STREAM", "")
    kinesis_client = Kinesis(kinesis_stream)

    global_dht.setup_global_dht(initial_peers, coordinator, logger, kinesis_client)

    # Start publishing to kinesis. This will eventually replace the populate_cache thread.
    logger.info("Starting gossip publisher")
    gossip_publisher = GossipDHTPublisher(
        dht=global_dht.dht,
        kinesis_client=kinesis_client,
        logger=logger,
        coordinator=coordinator,
        poll_interval_seconds=150,  # 2.5 minute
    )
    gossip_publisher.start()

    logger.info(f"initializing server on port {port}")
    server.run()


if __name__ == "__main__":
    main(parse_arguments())
