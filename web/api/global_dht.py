import multiprocessing

import hivemind

# DHT singletons for the client
# Initialized in main and used in the API handlers.
dht: hivemind.DHT | None = None


def setup_global_dht(initial_peers, coordinator, logger, kinesis_client):
    global dht
    dht = hivemind.DHT(
        start=True,
        startup_timeout=60,
        initial_peers=initial_peers,
        cache_nearest=2,
        cache_size=2000,
        client_mode=True,
    )
