# Node operations FAQ (RL Swarm)

This document answers common operational questions for node operators
participating in RL Swarm and the Gensyn Testnet.

It is intended as a complement to the main README and the online
getting-started and troubleshooting guides.

---

## 1. Where can I find the logs?

If you are running RL Swarm using Docker and the provided compose
configuration, you can usually find logs in one of two places:

- Docker logs:
  - `docker-compose logs -f` or `docker compose logs -f`
- log directory inside the container or mounted volume:
  - see the `docker-compose.yml` file for the configured log directory

When asking for help, it is useful to include a short excerpt from the
logs around the time when the problem occurs, with any sensitive data
removed.

---

## 2. What if the login page at localhost:3000 does not open?

If the browser does not reach `http://localhost:3000/` when RL Swarm
starts:

- check that the node is actually running and that the login service has
  started
- verify that you do not have a VPN or firewall blocking local
  connections
- if you are running RL Swarm inside a VM or container, confirm that:
  - the port is forwarded correctly
  - you are using the correct host address (for example `http://127.0.0.1:3000` or the VM IP)

If the problem persists, capture:

- the RL Swarm logs
- a short description of your environment
- any error messages from the browser or terminal

and include them when opening an issue.

---

## 3. How do I know if my node is visible on the testnet?

After completing the login and identity flow:

- wait a few minutes for the node to register and start participating
- open the Gensyn Testnet dashboard or explorer as described in the
  documentation
- look for your node, peer ID, or identity in the list of participants

If your node does not appear:

- confirm that it is still running and not repeatedly restarting
- check logs for errors related to:
  - identity or registration
  - network connectivity
- verify that you are running a supported version of RL Swarm

If needed, open an issue and include:

- your environment details (host, OS, CPU/GPU)
- the RL Swarm version and branch
- log excerpts showing what happens after login

---

## 4. Can I run RL Swarm on multiple machines?

Yes, you can run RL Swarm on more than one machine, but:

- each node should have a correctly configured identity
- you should follow the guidelines in the documentation regarding:
  - how identities are created
  - how they relate to participation and testnet rewards

If you copy configuration files between machines, be careful not to:

- accidentally share private keys or sensitive identity material with
  others
- create ambiguous setups where multiple machines try to use the same
  identity in conflicting ways

---

## 5. What should I check when upgrading?

Before upgrading to a new version of RL Swarm:

1. Read the release notes (if available) and the changelog.
2. Note any changes in:
   - supported Python versions
   - Docker images or compose configuration
   - identity and participation mechanisms
3. Upgrade in a controlled way:
   - stop your existing node
   - update the repository (for example `git pull`)
   - rebuild Docker images or refresh your Python environment
4. Restart RL Swarm and:
   - watch logs for errors
   - verify that the node appears on the dashboard again

If something breaks, consider rolling back to the previous known-good
version while you investigate.

---

## 6. Where can I ask for help?

If you run into an issue that you cannot resolve:

- check the online documentation and troubleshooting guides
- search existing GitHub issues to see if someone has reported a similar
  problem
- open a new GitHub issue with:
  - a clear summary
  - details about your environment
  - steps to reproduce
  - relevant logs

You can also join the official community channels mentioned in the
README or testnet documentation to ask questions and share feedback.
