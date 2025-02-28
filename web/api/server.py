import aiofiles
import argparse
import sys
import hivemind
from threading import Thread
import multiprocessing
from .server_cache import Cache
from fastapi import FastAPI, Query, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import httpx
import os
import time

from hivemind_exp.dht_utils import *

# UI is served from the filesystem
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(BASE_DIR, "ui", "dist")

# DHT singleton for the client
# Initialized in main and used in the API handlers.
dht: hivemind.DHT | None = None

dht_cache: Cache

index_html = None


async def load_index_html():
    global index_html
    if index_html is None:
        index_path = os.path.join(BASE_DIR, "ui", "dist", "index.html")
        async with aiofiles.open(index_path, mode="r") as f:
            index_html = await f.read()


app = FastAPI()
port = os.getenv("SWARM_UI_PORT", "8000")

try:
    port = int(port)
except ValueError:
    print(f"invalid port {port}. Defaulting to 8000")
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
    print(f"Internal server error: {exc}", file=sys.stderr)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "message": str(exc),
        },
    )


@app.get("/api/leaderboard")
def get_leaderboard():
    global dht_cache
    assert dht_cache

    leaderboard = dht_cache.get_leaderboard()
    return leaderboard


@app.get("/api/gossip")
def get_gossip(since_round: int = Query(0)):
    global dht_cache
    assert dht_cache

    return dht_cache.get_gossips()


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
        print(f"proxying {full_path} into local UI development environment on 5173...")
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
    global dht_cache
    assert dht_cache

    while True:
        print("pulling latest dht data...")
        dht_cache.poll_dht()
        time.sleep(10)


def main(args):
    global dht
    global dht_cache

    # Allows either an environment variable for peering or fallback to command line args.
    initial_peers_env = os.getenv("INITIAL_PEERS", "")
    initial_peers_list = (
        initial_peers_env.split(",") if initial_peers_env else args.initial_peers
    )

    # Supplied with the bootstrap node, the client will have access to the DHT.
    print(f"Initializing DHT...{initial_peers_list}")
    dht = hivemind.DHT(start=True, initial_peers=initial_peers_list)
    dht_cache = Cache(dht, multiprocessing.Manager())

    thread = Thread(target=populate_cache)
    thread.daemon = True
    thread.start()

    print(f"Initializing server on port {port}...")
    server.run()


if __name__ == "__main__":
    main(parse_arguments())
