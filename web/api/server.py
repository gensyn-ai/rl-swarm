import argparse
import logging
import os
import time
from datetime import datetime, timedelta
from threading import Thread

import aiofiles
import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import json

from hivemind_exp.dht_utils import *
from hivemind_exp.name_utils import get_name_from_peer_id

from . import global_dht

# UI is served from the filesystem
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(BASE_DIR, "ui", "dist")

index_html = None


async def load_index_html():
    global index_html
    if index_html is None:
        index_path = os.path.join(BASE_DIR, "ui", "dist", "index.html")
        async with aiofiles.open(index_path, mode="r") as f:
            index_html = await f.read()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

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


@app.get("/api/round_and_stage")
def get_round_and_stage():
    r, s = global_dht.dht_cache.get_round_and_stage()

    return {
        "round": r,
        "stage": s,
    }


@app.get("/api/leaderboard")
def get_leaderboard():
    leaderboard = global_dht.dht_cache.get_leaderboard()
    return dict(leaderboard)


@app.get("/api/name-to-id")
def get_id_from_name(name: str = Query("")):
	global dht_cache
	assert dht_cache

	leaderboard = global_dht.dht_cache.get_leaderboard()
	leader_ids = [leader["id"] for leader in leaderboard["leaders"]] or []

	uuid = search_peer_ids_for_name(leader_ids, name)

	return {
		"id": uuid,
	}

@app.post("/api/id-to-name")
async def id_to_name(request: Request):
    # Check request body size (100KB limit)
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 100 * 1024:  # 100KB in bytes
        raise HTTPException(
            status_code=413,
            detail="Request body too large. Maximum size is 100KB."
        )

    # Parse request body
    try:
        body = await request.json()
        if not isinstance(body, list):
            raise HTTPException(
                status_code=400,
                detail="Request body must be a list of peer IDs"
            )
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request body: {str(e)}"
        )

    # Validate input size
    if len(body) > 1000:  # Limit number of IDs that can be processed
        raise HTTPException(
            status_code=400,
            detail="Too many peer IDs. Maximum is 1000."
        )

    # Process each ID
    id_to_name_map = {}
    for peer_id in body:
        try:
            name = get_name_from_peer_id(peer_id)
            if name is not None:
                id_to_name_map[peer_id] = name
        except Exception as e:
            logger.error(f"Error looking up name for peer ID {peer_id}: {str(e)}")

    return id_to_name_map

@app.get("/api/gossip")
def get_gossip():
    gs = global_dht.dht_cache.get_gossips()
    return dict(gs)


if os.getenv("API_ENV") != "dev":
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(DIST_DIR, "assets")),
        name="assets",
    )
    app.mount(
        "/fonts", StaticFiles(directory=os.path.join(DIST_DIR, "fonts")), name="fonts"
    )
    app.mount(
        "/images",
        StaticFiles(directory=os.path.join(DIST_DIR, "images")),
        name="images",
    )


@app.get("/{full_path:path}")
async def catch_all(full_path: str, request: Request):
    # Development reverse proxies to ui dev server
    if os.getenv("API_ENV") == "dev":
        logger.info(
            f"proxying {full_path} into local UI development environment on 5173..."
        )
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url=f"http://localhost:5173/{full_path}", headers=request.headers
            )
            headers = {
                k: v
                for k, v in resp.headers.items()
                if k.lower() not in ["content-length", "transfer-encoding"]
            }
            return Response(
                content=resp.content, status_code=resp.status_code, headers=headers
            )

    # Live environment (serve from dist)
    # We don't want to cache index.html, but other static assets are fine to cache.
    await load_index_html()
    return HTMLResponse(
        content=index_html,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-ip", "--initial_peers", help="initial peers", nargs="+", type=str, default=[]
    )
    return parser.parse_args()


def populate_cache():
    logger.info("populate_cache initialized")
    try:
        while True:
            logger.info("pulling latest dht data...")
            global_dht.dht_cache.poll_dht()
            time.sleep(10)
            logger.info("dht polled")
    except Exception as e:
        logger.error("uncaught exception while polling dht", e)


def main(args):
    # Allows either an environment variable for peering or fallback to command line args.
    initial_peers_env = os.getenv("INITIAL_PEERS", "")
    initial_peers_list = (
        initial_peers_env.split(",") if initial_peers_env else args.initial_peers
    )

    # Supplied with the bootstrap node, the client will have access to the DHT.
    logger.info(f"initializing DHT with peers {initial_peers_list}")
    global_dht.setup_global_dht(initial_peers_list, logger)

    thread = Thread(target=populate_cache)
    thread.daemon = True
    thread.start()

    logger.info(f"initializing server on port {port}")
    server.run()


if __name__ == "__main__":
    main(parse_arguments())
