# RL Swarm Web

This package provides an API and UI for displaying gossip messages and metrics about training.

# Running the web server

From the rl_swarm directory, use docker-compose to spin up containers for the webserver and OpenTelemetry.
```
docker-compose build --no-cache
```

```
docker-compose up
```

docker-compose sets the initial peer environment variable for you, so for local testing 
the server will already be connected to the seed node, and will emit metrics to the OTEL container.

Access your local server from `0.0.0.0:8080`

**Environment variables**
- `SWARM_UI_PORT` defaults to 8000. The port of the HTTP server.
- `INITIAL_PEERS` defaults to "". A comma-separated list of multiaddrs.

To only run the webserver, you can use the file Dockerfile.webserver from the root directory:
```
docker build -t swarmui -f Dockerfile.webserver .
```

## Smart contract
The UI is set up to receive information from a smart contract. For development, it is assumed a smart contract is running locally using anvil.