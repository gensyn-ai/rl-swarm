/** @jsxImportSource solid-js */
import type { Component } from 'solid-js';
import { createResource, For, Show } from "solid-js";

export type PeerResponse = {
  peers: {
    multiaddr: string;
    source: string;
    connected: boolean;
  }[];
  discovery_active: boolean;
  total_count: number;
  connected_count: number;
};

async function fetchPeers(): Promise<PeerResponse | undefined> {
  try {
    const res = await fetch('/api/peers');
    const json = await res.json();

    if (res.status > 499) {
      console.error('5xx error fetching peer details');
      throw new Error('could not get peers: internal server error');
    }

    return json as PeerResponse;
  } catch (e) {
    console.error('error fetching peer details', e);
    return undefined;
  }
}

const PeerNetwork: Component = () => {
  const [peerData, { refetch: refetchPeers }] = createResource(fetchPeers);
  let peerTimer: ReturnType<typeof setTimeout> | undefined = undefined;

  // Poll peers every 10 seconds
  const pollPeers = async () => {
    await refetchPeers();

    if (peerTimer !== undefined) {
      clearTimeout(peerTimer);
    }
    peerTimer = setTimeout(pollPeers, 10000);
  };

  // Start polling on mount
  setTimeout(pollPeers, 10000);

  return (
    <section class="flex flex-grow flex-col min-h-0">
      <header class="flex items-center mb-4">
        <div class="flex-1"><mark class="uppercase">swarm peers</mark></div>
      </header>

      <div class="mb-4 flex items-center uppercase">
        <div class="flex-1">
          <Show when={peerData()} fallback={<span>&lt; FETCHING PEERS &gt;</span>}>
            <mark>
              {peerData()?.connected_count || 0} connected / {peerData()?.total_count || 0} total
            </mark>
          </Show>
        </div>
        <div>
          <Show when={peerData()?.discovery_active}>
            <mark class="bg-gensyn-green text-gensyn-brown">[discovery active]</mark>
          </Show>
          <Show when={!peerData()?.discovery_active}>
            <mark>[discovery inactive]</mark>
          </Show>
        </div>
      </div>

      <div id="peers-container" class="overflow-scroll overflow-x-hidden flex-grow min-h-0 max-h-[50vh] md:max-h-none">
        <Show when={peerData()?.peers.length} fallback={<span>&lt; NO PEERS FOUND &gt;</span>}>
          <ul class="list-none">
            <For each={peerData()?.peers}>
              {(peer) => (
                <li class="mb-2">
                  <div class="flex items-center">
                    <div class="mr-2">
                      {peer.connected ?
                        <span class="text-gensyn-green">[connected]</span> :
                        <span>[disconnected]</span>
                      }
                    </div>
                    <div class="lowercase break-all">{peer.multiaddr}</div>
                  </div>
                </li>
              )}
            </For>
          </ul>
        </Show>
      </div>
    </section>
  );
};

export default PeerNetwork;