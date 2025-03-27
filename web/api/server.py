import aiofiles
import argparse
from datetime import datetime, timedelta
import hivemind
import logging
from threading import Thread
import multiprocessing
from .server_cache import Cache
from fastapi import FastAPI, Query, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import httpx
import os
import time

from hivemind_exp.dht_utils import *

# Import peer discovery module
try:
    from hivemind_exp.peer_discovery import PeerDiscovery
except ImportError:
    PeerDiscovery = None

# UI is served from the filesystem
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(BASE_DIR, "ui", "dist")

# DHT singleton for the client
# Initialized in main and used in the API handlers.
dht: hivemind.DHT | None = None

dht_cache: Cache

# Global peer discovery instance
peer_discovery_instance = None

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
    global dht_cache
    assert dht_cache

    lpt = dht_cache.get_last_polled()
    if lpt is None:
        raise HTTPException(status_code=500, detail="dht never polled")

    diff = datetime.now() - lpt
    if diff > timedelta(minutes=5):
        raise HTTPException(status_code=500, detail="dht last poll exceeded 5 minutes")

    return {
        "message": "OK",
        "lastPolled": diff,
    }


@app.get("/api/leaderboard")
def get_leaderboard():
    global dht_cache
    assert dht_cache

    leaderboard = dht_cache.get_leaderboard()
    return dict(leaderboard)


@app.get("/api/gossip")
def get_gossip(since_round: int = Query(0)):
    global dht_cache
    assert dht_cache

    gs = dht_cache.get_gossips()
    return dict(gs)


@app.get("/api/peers")
def get_peers():
    """
    Get information about discovered peers

    Returns:
        JSON with peer information
    """
    global dht
    global peer_discovery_instance

    # Initialize peer discovery if needed
    if dht and not peer_discovery_instance:
        try:
            if PeerDiscovery:
                peer_discovery_instance = PeerDiscovery(dht)
                peer_discovery_instance.start()
                logger.info("Peer discovery started")
        except Exception as e:
            logger.error(f"Failed to start peer discovery: {e}")

    # Get peers
    peers = []

    # First, add peers from peer discovery if available
    if peer_discovery_instance:
        discovered = peer_discovery_instance.get_peers()
        peers.extend([{
            "multiaddr": peer,
            "source": "discovery",
            "connected": _is_peer_connected(peer)
        } for peer in discovered])

    # Add directly connected peers from DHT
    if dht:
        try:
            visible_maddrs = dht.get_visible_maddrs()
            for maddr in visible_maddrs:
                if not any(p["multiaddr"] == maddr for p in peers):
                    peers.append({
                        "multiaddr": maddr,
                        "source": "connected",
                        "connected": True
                    })
        except Exception as e:
            logger.warning(f"Failed to get connected peers: {e}")

    # Add myself
    my_addr = dht.get_visible_maddrs()[0] if dht and dht.get_visible_maddrs() else None
    if my_addr:
        peers.append({
            "multiaddr": my_addr,
            "source": "self",
            "connected": True
        })

    # Format the response
    return {
        "peers": peers,
        "discovery_active": peer_discovery_instance is not None,
        "total_count": len(peers),
        "connected_count": sum(1 for p in peers if p["connected"])
    }


def _is_peer_connected(multiaddr):
    """Check if a peer is connected"""
    global dht
    if not dht:
        return False

    try:
        visible_maddrs = dht.get_visible_maddrs()
        return multiaddr in visible_maddrs
    except:
        return False


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
    global dht_cache
    assert dht_cache

    try:
        while True:
            logger.info("pulling latest dht data...")
            dht_cache.poll_dht()
            time.sleep(10)
    except Exception as e:
        logger.error("uncaught exception while polling dht", e)


def main(args):
    global dht
    global dht_cache
    global peer_discovery_instance

    # Allows either an environment variable for peering or fallback to command line args.
    initial_peers_env = os.getenv("INITIAL_PEERS", "")
    initial_peers_list = (
        initial_peers_env.split(",") if initial_peers_env else args.initial_peers
    )

    # Supplied with the bootstrap node, the client will have access to the DHT.
    logger.info(f"initializing DHT with peers {initial_peers_list}")
    dht = hivemind.DHT(start=True, initial_peers=initial_peers_list)
    dht_cache = Cache(dht, multiprocessing.Manager(), logger)

    # Initialize peer discovery
    try:
        if PeerDiscovery:
            peer_discovery_instance = PeerDiscovery(dht)
            peer_discovery_instance.start()
            logger.info("Peer discovery started")
    except Exception as e:
        logger.error(f"Failed to start peer discovery: {e}")

    thread = Thread(target=populate_cache)
    thread.daemon = True
    thread.start()

    logger.info(f"initializing server on port {port}")
    server.run()


if __name__ == "__main__":
    main(parse_arguments())