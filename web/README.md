# RL Swarm Web

This package provides an API and UI for displaying gossip messages and metrics about training.

# Running the web server
From the root directory:
- run `docker build -t swarmui -f Dockerfile.webserver .` to build the container.
- then run `docker run -d -p 8080:8000 swarmui` to fire up an instance of the webserver on port 8080.

You can then access locally through `0.0.0.0:8080` on your machine.

Example command to connect to a peer:
```
docker run -p 8080:8000 --env INITIAL_PEERS="/dns/rl-swarm.gensyn.ai/tcp/38331/p2p/QmQ2gEXoPJg6iMBSUFWGzAabS2VhnzuS782Y637hGjfsRJ" swarmui
```

**Environment variables**
- `SWARM_UI_PORT` defaults to 8000. The port of the HTTP server.
- `INITIAL_PEERS` defaults to "". A comma-separated list of multiaddrs.