"""
Simple peer discovery for RL Swarm using existing libraries.

This module provides two discovery mechanisms:
1. Local network discovery via mDNS/Zeroconf
2. DHT-based discovery for wider internet peers
"""

import logging
import os
import socket
import time
from typing import List, Optional, Set

import hivemind
from hivemind.dht import DHT
from hivemind.utils import get_dht_time

# Try to import zeroconf for local discovery
try:
    from zeroconf import ServiceInfo, Zeroconf, ServiceBrowser, ServiceStateChange
    ZEROCONF_AVAILABLE = True
except ImportError:
    ZEROCONF_AVAILABLE = False
    logging.warning("Zeroconf not available. Install with 'pip install zeroconf' for local discovery")

logger = logging.getLogger(__name__)

class PeerDiscovery:
    """
    Simple peer discovery using mDNS (local) and DHT (internet)
    """
    def __init__(self,
                 dht: DHT,
                 enable_local_discovery: bool = True,
                 service_name: str = "rlswarm",
                 cache_file: str = "~/.rlswarm/peers.json"):
        """
        Initialize peer discovery

        Args:
            dht: Hivemind DHT instance
            enable_local_discovery: Whether to use local network discovery
            service_name: Service name for mDNS
            cache_file: File to cache discovered peers
        """
        self.dht = dht
        self.enable_local_discovery = enable_local_discovery and ZEROCONF_AVAILABLE
        self.service_name = service_name
        self.service_type = f"_{service_name}._tcp.local."
        self.cache_file = os.path.expanduser(cache_file)

        # State
        self.discovered_peers = set()
        self.zeroconf = None
        self.browser = None
        self._active = False

        # Try to load cached peers
        self._load_cached_peers()

    def _load_cached_peers(self):
        """Load peers from cache file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    peers = f.read().splitlines()
                    for peer in peers:
                        if peer.strip():
                            self.discovered_peers.add(peer.strip())
                    logger.info(f"Loaded {len(self.discovered_peers)} peers from cache")
            except Exception as e:
                logger.warning(f"Failed to load peers from cache: {e}")

    def _save_cached_peers(self):
        """Save peers to cache file"""
        try:
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w') as f:
                for peer in self.discovered_peers:
                    f.write(f"{peer}\n")
            logger.info(f"Saved {len(self.discovered_peers)} peers to cache")
        except Exception as e:
            logger.warning(f"Failed to save peers to cache: {e}")

    def start(self):
        """Start peer discovery"""
        if self._active:
            return

        self._active = True

        # Start local discovery if enabled
        if self.enable_local_discovery:
            self._start_local_discovery()

        # Get peers from DHT
        self._discover_dht_peers()

        logger.info(f"Peer discovery started with {len(self.discovered_peers)} peers")

    def stop(self):
        """Stop peer discovery"""
        if not self._active:
            return

        self._active = False

        # Stop local discovery
        if self.enable_local_discovery and self.zeroconf:
            self._stop_local_discovery()

        # Save peers to cache
        self._save_cached_peers()

        logger.info("Peer discovery stopped")

    def _start_local_discovery(self):
        """Start local network discovery using mDNS/Zeroconf"""
        if not ZEROCONF_AVAILABLE:
            logger.warning("Zeroconf not available, local discovery disabled")
            return

        try:
            self.zeroconf = Zeroconf()

            # Register our own service
            hostname = socket.gethostname()
            try:
                host_ip = socket.gethostbyname(hostname)
            except socket.gaierror:
                host_ip = "127.0.0.1"  # Fallback

            port = getattr(self.dht, 'port', 30303)  # Default port

            info = ServiceInfo(
                self.service_type,
                f"{hostname}.{self.service_type}",
                addresses=[socket.inet_aton(host_ip)],
                port=port,
                properties={},
                server=f"{hostname}.local.",
            )

            self.zeroconf.register_service(info)

            # Discover other services
            def on_service_state_change(zeroconf, service_type, name, state_change):
                if state_change == ServiceStateChange.Added:
                    info = zeroconf.get_service_info(service_type, name)
                    if info:
                        for addr in info.addresses:
                            ip = socket.inet_ntoa(addr)
                            multiaddr = f"/ip4/{ip}/tcp/{info.port}"

                            # Add to discovered peers
                            self.discovered_peers.add(multiaddr)

                            # Try to connect via DHT
                            try:
                                self.dht.add_initial_peers([multiaddr])
                                logger.info(f"Discovered local peer: {multiaddr}")
                            except Exception as e:
                                logger.debug(f"Failed to connect to local peer {multiaddr}: {e}")

            self.browser = ServiceBrowser(
                self.zeroconf,
                self.service_type,
                handlers=[on_service_state_change]
            )

            logger.info("Local discovery started")
        except Exception as e:
            logger.error(f"Failed to start local discovery: {e}")
            self._stop_local_discovery()

    def _stop_local_discovery(self):
        """Stop local network discovery"""
        if self.browser:
            self.browser.cancel()
            self.browser = None

        if self.zeroconf:
            try:
                hostname = socket.gethostname()
                service_name = f"{hostname}.{self.service_type}"
                self.zeroconf.unregister_service(service_name)
            except:
                pass

            self.zeroconf.close()
            self.zeroconf = None

        logger.info("Local discovery stopped")

    def _discover_dht_peers(self):
        """Discover peers through DHT"""
        # Get visible peers from DHT
        try:
            # This gets peers that the current node is directly connected to
            visible_maddrs = self.dht.get_visible_maddrs()
            for maddr in visible_maddrs:
                self.discovered_peers.add(maddr)

            # Check if there are active peers from DHT metrics
            try:
                # Look for active peers via dht.get_active_peers if available
                if hasattr(self.dht, 'get_active_peers'):
                    active_peers = self.dht.get_active_peers()
                    for peer_id in active_peers:
                        if hasattr(peer_id, 'addresses'):
                            for addr in peer_id.addresses:
                                maddr_str = str(addr)
                                if maddr_str:
                                    self.discovered_peers.add(maddr_str)
                                    logger.debug(f"Found DHT active peer: {maddr_str}")
            except Exception as e:
                logger.debug(f"Failed to get active peers from DHT: {e}")

            # Try to find peers through DHT routing table
            try:
                # Check routing table if available
                if hasattr(self.dht, 'routing_table'):
                    for bucket in self.dht.routing_table.buckets:
                        for peer in bucket.peers:
                            for addr in peer.addresses:
                                maddr_str = str(addr)
                                if maddr_str:
                                    self.discovered_peers.add(maddr_str)
                                    logger.debug(f"Found routing table peer: {maddr_str}")
            except Exception as e:
                logger.debug(f"Failed to get peers from routing table: {e}")

            # Look for peers in DHT store
            try:
                from hivemind_exp.dht_utils import ROUND_STAGE_NUMBER_KEY, get_dht_value

                # Try to find any active nodes in the DHT by checking for published keys
                rs_value = get_dht_value(self.dht, key=ROUND_STAGE_NUMBER_KEY, latest=True)
                if rs_value:
                    logger.info(f"Found active swarm at round {rs_value[0]}, stage {rs_value[1]}")

                    # If we found an active swarm, try to find peers via other DHT keys
                    from hivemind_exp.dht_utils import leaderboard_key, rewards_key
                    round_num, stage_num = rs_value

                    # Check for peers in the leaderboard
                    lb_key = leaderboard_key(round_num, stage_num)
                    lb_value = get_dht_value(self.dht, key=lb_key, latest=True)
                    if lb_value and isinstance(lb_value, list):
                        logger.info(f"Found {len(lb_value)} peers in leaderboard")
                        # Leaderboard contains (node_uuid, score) pairs
                        # We can't directly get multiaddrs from this, but it's a sign of active peers

                    # Check for peers in the rewards
                    rw_key = rewards_key(round_num, stage_num)
                    rw_value = get_dht_value(self.dht, key=rw_key, latest=True)
                    if rw_value and isinstance(rw_value, dict):
                        logger.info(f"Found {len(rw_value)} peers in rewards")
                        # Similar to leaderboard, we just have node UUIDs, not multiaddrs
            except Exception as e:
                logger.debug(f"Failed to get peers from DHT store: {e}")

        except Exception as e:
            logger.warning(f"Failed to discover DHT peers: {e}")

    def get_peers(self) -> List[str]:
        """
        Get list of all discovered peers

        Returns:
            List of peer multiaddrs
        """
        # First update from DHT
        self._discover_dht_peers()

        # Filter out invalid addresses
        valid_peers = [p for p in self.discovered_peers if p and str(p).startswith('/')]

        return valid_peers

    def get_bootstrap_peers(self, count: int = 3) -> List[str]:
        """
        Get a list of best peers to use for bootstrapping

        Args:
            count: Maximum number of peers to return

        Returns:
            List of multiaddrs to use for bootstrapping
        """
        peers = self.get_peers()

        # Currently we don't have sophisticated metrics, so just return a few random peers
        # In a real-world system, we might want to prioritize peers based on latency, etc.
        import random
        if len(peers) <= count:
            return peers
        return random.sample(peers, count)