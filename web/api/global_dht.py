import multiprocessing
import hivemind

from . import server_cache

# DHT singletons for the client
# Initialized in main and used in the API handlers.
dht: hivemind.DHT | None = None
dht_cache = None

def setup_global_dht(initial_peers, logger):
    global dht
    global dht_cache
    dht = hivemind.DHT(start=True, initial_peers=initial_peers)
    dht_cache = server_cache.Cache(dht, multiprocessing.Manager(), logger)