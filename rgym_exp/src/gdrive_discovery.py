"""
Google Drive-based Peer Discovery for RL Swarm

Enables peer discovery without hardcoded bootnodes using Google Drive as a
discovery mechanism. Nodes publish their multiaddrs and discover others dynamically.
"""

import json
import os
import time
from typing import List, Dict, Any, Optional
from genrl.logging_utils.global_defs import get_logger


class GDrivePeerDiscovery:
    """
    Peer discovery mechanism using Google Drive.
    Nodes publish their multiaddrs to shared directory.
    """

    def __init__(self, discovery_path: str, stale_threshold_seconds: int = 3600):
        """
        Initialize peer discovery.

        Args:
            discovery_path: Path to discovery directory in Google Drive
            stale_threshold_seconds: Time before entry considered stale (default 1 hour)
        """
        self.discovery_path = discovery_path
        self.stale_threshold = stale_threshold_seconds
        os.makedirs(discovery_path, exist_ok=True)

        get_logger().info(f"Initialized peer discovery at {discovery_path}")

    def publish_multiaddr(self, peer_id: str, multiaddr: str, node_role: str = 'worker'):
        """
        Publish this node's multiaddr for others to discover.

        Args:
            peer_id: Unique peer identifier
            multiaddr: Multiaddress string (e.g., '/ip4/1.2.3.4/tcp/12345/p2p/QmAbc...')
            node_role: Role of this node ('coordinator' or 'worker')
        """
        discovery_file = os.path.join(self.discovery_path, f'{peer_id}.json')
        data = {
            "peer_id": peer_id,
            "multiaddr": multiaddr,
            "node_role": node_role,
            "published_at": time.time(),
            "last_heartbeat": time.time()
        }

        try:
            with open(discovery_file, 'w') as f:
                json.dump(data, f, indent=2)
            get_logger().debug(f"Published multiaddr for {peer_id}")
        except Exception as e:
            get_logger().error(f"Failed to publish multiaddr: {e}")

    def update_heartbeat(self, peer_id: str):
        """
        Update heartbeat timestamp to show node is still alive.

        Args:
            peer_id: Peer identifier
        """
        discovery_file = os.path.join(self.discovery_path, f'{peer_id}.json')

        if not os.path.exists(discovery_file):
            get_logger().warning(f"Cannot update heartbeat: {discovery_file} does not exist")
            return

        try:
            with open(discovery_file, 'r') as f:
                data = json.load(f)

            data['last_heartbeat'] = time.time()

            with open(discovery_file, 'w') as f:
                json.dump(data, f, indent=2)

            get_logger().debug(f"Updated heartbeat for {peer_id}")

        except Exception as e:
            get_logger().error(f"Failed to update heartbeat: {e}")

    def discover_peers(
        self,
        exclude_self: Optional[str] = None,
        max_peers: int = 10,
        role_filter: Optional[str] = None
    ) -> List[str]:
        """
        Discover active peers from Google Drive.

        Args:
            exclude_self: Peer ID to exclude from results (usually self)
            max_peers: Maximum number of peers to return
            role_filter: Optional filter by node role ('coordinator' or 'worker')

        Returns:
            List of multiaddrs from active peers
        """
        peers = []
        current_time = time.time()

        try:
            if not os.path.exists(self.discovery_path):
                get_logger().debug(f"Discovery path does not exist: {self.discovery_path}")
                return []

            for filename in os.listdir(self.discovery_path):
                if not filename.endswith('.json'):
                    continue

                filepath = os.path.join(self.discovery_path, filename)

                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)

                    # Skip self
                    if exclude_self and data['peer_id'] == exclude_self:
                        continue

                    # Filter by role if specified
                    if role_filter and data.get('node_role') != role_filter:
                        continue

                    # Skip stale entries
                    last_heartbeat = data.get('last_heartbeat', 0)
                    if current_time - last_heartbeat > self.stale_threshold:
                        get_logger().debug(f"Skipping stale peer: {data['peer_id']}")
                        continue

                    peers.append(data['multiaddr'])

                    if len(peers) >= max_peers:
                        break

                except (json.JSONDecodeError, KeyError) as e:
                    get_logger().debug(f"Error reading {filename}: {e}")
                    continue

        except Exception as e:
            get_logger().error(f"Error discovering peers: {e}")

        get_logger().info(f"Discovered {len(peers)} peers")
        return peers

    def get_peer_info(self, peer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific peer.

        Args:
            peer_id: Peer identifier

        Returns:
            Dictionary with peer info, or None if not found
        """
        discovery_file = os.path.join(self.discovery_path, f'{peer_id}.json')

        if not os.path.exists(discovery_file):
            return None

        try:
            with open(discovery_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            get_logger().error(f"Error getting peer info: {e}")
            return None

    def cleanup_stale_entries(self):
        """Remove stale discovery entries (optional maintenance)"""
        current_time = time.time()
        removed_count = 0

        try:
            if not os.path.exists(self.discovery_path):
                return

            for filename in os.listdir(self.discovery_path):
                if not filename.endswith('.json'):
                    continue

                filepath = os.path.join(self.discovery_path, filename)

                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)

                    last_heartbeat = data.get('last_heartbeat', 0)
                    if current_time - last_heartbeat > self.stale_threshold:
                        os.remove(filepath)
                        removed_count += 1
                        get_logger().info(f"Removed stale discovery entry: {filename}")

                except Exception as e:
                    get_logger().error(f"Error cleaning {filename}: {e}")

            if removed_count > 0:
                get_logger().info(f"Cleaned up {removed_count} stale entries")

        except Exception as e:
            get_logger().error(f"Error during cleanup: {e}")

    def get_all_active_peers(self) -> List[Dict[str, Any]]:
        """
        Get information about all active peers.

        Returns:
            List of peer info dictionaries
        """
        peers = []
        current_time = time.time()

        try:
            if not os.path.exists(self.discovery_path):
                return []

            for filename in os.listdir(self.discovery_path):
                if not filename.endswith('.json'):
                    continue

                filepath = os.path.join(self.discovery_path, filename)

                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)

                    # Skip stale entries
                    last_heartbeat = data.get('last_heartbeat', 0)
                    if current_time - last_heartbeat > self.stale_threshold:
                        continue

                    peers.append(data)

                except (json.JSONDecodeError, KeyError) as e:
                    get_logger().debug(f"Error reading {filename}: {e}")
                    continue

        except Exception as e:
            get_logger().error(f"Error getting active peers: {e}")

        return peers

    def get_stats(self) -> Dict[str, Any]:
        """
        Get discovery statistics.

        Returns:
            Dictionary with statistics
        """
        active_peers = self.get_all_active_peers()

        coordinators = [p for p in active_peers if p.get('node_role') == 'coordinator']
        workers = [p for p in active_peers if p.get('node_role') == 'worker']

        return {
            "total_active": len(active_peers),
            "coordinators": len(coordinators),
            "workers": len(workers),
            "discovery_path": self.discovery_path,
            "stale_threshold_seconds": self.stale_threshold
        }
