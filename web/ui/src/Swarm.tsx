/** @jsxImportSource solid-js */
import { JSX } from 'solid-js';
import {
  children,
  createEffect,
  createMemo,
  createResource,
  createSignal,
  onCleanup,
  onMount,
  ParentProps,
  untrack
} from 'solid-js';
import * as d3 from 'd3';
import { getGossip, getLeaderboard, GossipResponse, LeaderboardResponse } from './swarm.api';
import PeerNetwork from './PeerNetwork';

// -- Simple placeholder Modal component so TS can resolve 'Modal'
function Modal(props: { open: boolean; message: string }) {
  return props.open ? (
    <div class="fixed top-0 left-0 w-full h-full flex items-center justify-center bg-black/40">
      <div class="bg-white p-4">
        <p>{props.message}</p>
      </div>
    </div>
  ) : null;
}

async function fetchLeaderboardData(): Promise<LeaderboardResponse | undefined> {
  try {
    const response = await getLeaderboard();
    return response;
  } catch (e) {
    return undefined;
  }
}

async function fetchGossipData(since: number): Promise<GossipResponse | undefined> {
  try {
    const response = await getGossip({ since });
    return response;
  } catch (e) {
    return undefined;
  }
}

/**
 * mergeLeaderboardData constructs the datapoints needed by the graphing library to render a node's score change over time.
 * The backend returns a snapshot of the current cumulative reward, so the client must build the history when polling.
 *
 * It is exported only for testing.
 *
 * @param xVal the current poll iteration
 * @param apiRes the leaderboard response
 * @param accumulator accumulated leaders data, stores old values
 * @returns A new accumulator with the updated values.
 */
export function mergeLeaderboardData(
  xVal: number,
  apiRes: LeaderboardResponse | undefined,
  accumulator: LeaderboardResponse | null | undefined
): LeaderboardResponse | null | undefined {
  if (apiRes === undefined) {
    return accumulator;
  }

  // If this is the first poll, then no accumulator will have been created yet.
  if (accumulator === undefined || accumulator === null) {
    apiRes.leaders.forEach((leader) => {
      leader.values = [{ x: xVal, y: leader.score }];
    });
    return apiRes;
  }

  const output = { ...apiRes };

  const accumLeadersById: Record<string, { id: string; values: { x: number; y: number }[]; score: number }> = {};
  accumulator.leaders.forEach((leader) => {
    accumLeadersById[leader.id] = { ...leader };
  });

  // The values stored are capped at 100 (arbitrarily chosen).
  output.leaders.forEach((leader) => {
    const prevVals = accumLeadersById[leader.id]?.values ?? [];
    const nextVals = [...prevVals, { x: xVal, y: leader.score }].slice(-100);
    leader.values = nextVals;
  });

  return output;
}

export default function Swarm() {
  // The UI tracks the latest round seen so it can query only for new data.
  // When the training loop resets on the backend, we expect to receive round=-1 back in the response.
  // Otherwise the backend will report its current round.
  const [lastGossipRound, setLastGossipRound] = createSignal(0);
  const [lastGossipStage, setLastGossipStage] = createSignal(0);

  const leaderboardSubtitle = createMemo(() => {
    let out = '';
    if (lastGossipRound() >= 0) {
      out = out + `: Round ${lastGossipRound()}`;

      if (lastGossipStage() >= 0) {
        out = out + `, stage ${lastGossipStage()}`;
      }
    }
    return out;
  });

  // The UI also maintains a state for how many leaderboard polls we've done.
  // Currently just a side-effect of how the API/DHT is constructed.
  // This value is increased with each leaderboard poll as a way to show time.
  const [rewardXValue, setRewardXValue] = createSignal(0);

  // `leaderboardData` data represents the snapshot of leaderboard data at a given polling interval.
  const [leaderboardData, { refetch: refetchLeaderboard }] = createResource(fetchLeaderboardData);
  const [leaders, setLeaders] = createSignal<LeaderboardResponse | null | undefined>(null, {
    equals: (oldData, newData) => {
      return JSON.stringify(oldData) === JSON.stringify(newData);
    }
  });

  // If no leaders are coming in the response, it's the signal of a new round.
  const showNewRoundModal = createMemo(() => {
    const currentLeaders = leaderboardData()?.leaders ?? [];
    return currentLeaders.length <= 0;
  });

  // Use ReturnType<typeof setTimeout> to handle both browser & Node type definitions
  let leaderboardTimer: ReturnType<typeof setTimeout> | undefined = undefined;

  // `gossipData` is the raw gossip response from the API.
  const [gossipData, { refetch: refetchGossip }] = createResource(lastGossipRound, fetchGossipData);
  let seenMessageIds = new Set<string>();
  const [gossipMessages, setGossipMessages] = createSignal<{ id: string; message: string; node: string }[]>([]);
  let gossipTimer: ReturnType<typeof setTimeout> | undefined = undefined;
  let gossipContainerRef: HTMLDivElement | undefined;

  // pollGossip fetches the latest gossip messages for the current round.
  const pollGossip = async () => {
    const nextGossip = await refetchGossip();

    if (nextGossip && nextGossip.currentRound) {
      setLastGossipRound(nextGossip?.currentRound);
    }
    if (nextGossip && nextGossip.currentStage) {
      setLastGossipStage(nextGossip?.currentStage);
    }

    if (gossipTimer !== undefined) {
      clearTimeout(gossipTimer);
    }
    gossipTimer = setTimeout(pollGossip, 10_000);
  };

  // pollLeaderboard fetches the latest leaderboard snapshot.
  const pollLeaderboard = async () => {
    await refetchLeaderboard();

    if (leaderboardTimer !== undefined) {
      clearTimeout(leaderboardTimer);
    }
    leaderboardTimer = setTimeout(pollLeaderboard, 10_000);
  };

  // Merge the new leaderboard results with the old whenever it refetches.
  createEffect(() => {
    if (!leaderboardData()) {
      setRewardXValue(0);
      setLeaders(undefined);
      return;
    }

    if (leaderboardData()?.leaders.length === 0) {
      setRewardXValue(0);
      setLeaders(undefined);
      return;
    }

    setRewardXValue(untrack(rewardXValue) + 1);

    // Multiply by 10 as an approximation of seconds.
    const xVal = rewardXValue() * 10;
    const next = mergeLeaderboardData(xVal, leaderboardData(), leaders());
    setLeaders(next);
  });

  // Dedupe new gossip messages each time gossipData updates.
  createEffect(() => {
    const g = gossipData();
    if (!g || !g.messages || g.messages.length <= 0) {
      return;
    }

    const msgs = g.messages
      .filter((msg) => !seenMessageIds.has(msg.id))
      .map((msg) => {
        seenMessageIds.add(msg.id);
        return msg;
      });

    setGossipMessages([...untrack(gossipMessages), ...msgs].slice(-200));
    setLastGossipRound(g.currentRound);

    if (seenMessageIds.size > 2000) {
      const temp = Array.from(seenMessageIds).slice(-2000);
      seenMessageIds = new Set<string>(temp);
    }

    if (gossipContainerRef) {
      gossipContainerRef.scrollTop = gossipContainerRef.scrollHeight;
    }
  });

  onMount(() => {
    // Wait 10s before firing, since we already fetch once on mount.
    const lt = setTimeout(pollLeaderboard, 10_000);
    const gt = setTimeout(pollGossip, 10_000);

    onCleanup(() => {
      clearTimeout(lt);
      clearTimeout(gt);
    });
  });

  const LeaderboardTooltipMessage = () => (
    <>
      <p class="uppercase">Models in the swarm receive rewards based on the following criteria:</p>
      <ul class="mt-4 uppercase">
        <li class="mb-2">
          <strong>Formatted &rarr;</strong> does the model generate output matching the specified format?
        </li>
        <li class="mb-2">
          <strong>Correct &rarr;</strong> is the final answer mathematically correct and formatted correctly?
        </li>
        <li>
          <strong>Insightful &rarr;</strong> in stages requiring reference to best messages from prior rounds, does the
          model reference those messages, and do they meet the reward criteria for that round?
        </li>
      </ul>
      <p class="uppercase text-center mt-4 mb-4">* * *</p>
      <p class="uppercase">
        This graph displays the cumulative reward for each node from the moment the page is loaded, not the full history
        from the start of a round.
      </p>
    </>
  );

  return (
    <main class="tracking-wider !font-normal !antialiased max-w-[876px] p-2 md:pt-12 md:pl-12 md:pr-0 flex flex-col justify-between md:min-h-screen ml-auto mr-auto">
      <Modal open={showNewRoundModal()} message="Starting new stage..." />
      <header>
        <h1 class="uppercase text-2xl tracking-[0.25em] mb-4">Gensyn: RL Swarm Client Interface</h1>
        <Banner>
          <p class="uppercase leading-[calc(1em+8px)] mt-4 mb-4">
            <mark class="p-[3px]">
              A peer-to-peer system for collaborative reinforcement learning over the internet, running on consumer
              hardware.
            </mark>
          </p>
        </Banner>
      </header>

      <article class="flex flex-grow md:h-0 md:min-h-[600px] md:max-h-full gap-4 flex-col md:flex-row mb-12 mt-8">
        <section class="flex flex-grow flex-col min-h-0 border-dashed border-gensyn-brown border-b md:border-b-0 pb-4 mb:pb-0 md:border-r md:pr-8">
          <div class="flex-none">
            <SectionHeader title="cumulative reward" tooltip={<LeaderboardTooltipMessage />} />
            {leaders() ? (
              <MultiLineChart data={leaders()!} />
            ) : (
              <span class="block w-[400px]">&lt; FETCHING LEADERS &gt;</span>
            )}
          </div>

          <div class="flex-none mt-8">
            <SectionHeader title={`leaderboard ${leaderboardSubtitle()}`} />
          </div>

          <div id="leaderboard-container" class="mt-0 overflow-auto overflow-x-hidden flex-grow min-h-0">
            <Leaderboard leaders={leaders()?.leaders || []} />
          </div>
        </section>

        <section class="flex flex-grow flex-col min-h-0 pl-0 md:pl-8">
          <div class="flex-none">
            <SectionHeader title="gossip" />
            <div
              ref={gossipContainerRef}
              class="overflow-scroll overflow-x-hidden flex-grow min-h-0 max-h-[50vh] md:max-h-none"
              id="gossip-container"
            >
              <ul class="list-none">
                {gossipMessages()?.length > 0 ? (
                  gossipMessages().map((msg) => (
                    <li>
                      <NodeMessage id={msg.node} message={msg.message} />
                    </li>
                  ))
                ) : (
                  <span>&lt; FETCHING GOSSIP &gt;</span>
                )}
              </ul>
            </div>
          </div>

          <div class="flex-none mt-8">
            <PeerNetwork />
          </div>
        </section>
      </article>

      <Banner>
        <footer class="flex items-center uppercase mt-8 mb-8">
          <div class="flex-1">
            <a href="https://github.com/gensyn-ai/rl-swarm">
              <mark>Join swarm</mark>
            </a>
          </div>
          <div class="flex items-center">
            <a class="flex items-center" href="https://gensyn.ai" target="_blank" rel="noopener noreferrer">
              <img class="h-[50px]" src="/images/logo.gif" alt="A spinning gensyn logo" />
              <img class="h-[30px]" src="/images/gen-logotype-dark-rgb.svg" alt="The gensyn name" />
            </a>
          </div>
          <div class="flex items-center ml-8">gensyn &copy;2025</div>
        </footer>
      </Banner>
    </main>
  );
}

function SectionHeader(props: { title: string; tooltip?: string | JSX.Element }) {
  return (
    <header class="flex items-center mb-4">
      <div class="flex-1">
        <mark class="uppercase">{props.title}</mark>
      </div>
      {props.tooltip ? <Tooltip message={props.tooltip} /> : null}
    </header>
  );
}

function Tooltip(props: { message: string | JSX.Element }) {
  // Use explicit type for detailsRef
  let detailsRef: HTMLDetailsElement | undefined;

  const close = (_: MouseEvent) => {
    // Type-safe check ensures detailsRef is not undefined
    if (detailsRef) {
      detailsRef.removeAttribute('open');
    }
  };

  onMount(() => {
    document.addEventListener('click', close);
  });

  onCleanup(() => {
    document.removeEventListener('click', close);
  });

  return (
    <div class="relative">
      {/* Use callback ref to store the details element */}
      <details class="group" ref={(el) => (detailsRef = el)}>
        <summary class="cursor-pointer list-none flex-none tracking-tightest text-xs tracking-[-0.25em]">[+]</summary>
        <div class="fixed inset-0 bg-black/50 flex items-center justify-center">
          <div class="max-w-[80vw] md:max-w-[33vw] px-8 py-8 bg-[#fcc6be] text-[#2A0D04] text-sm border border-[#2A0D04] max-h-[90vh] md:max-h-[50vh] overflow-y-auto overflow-x-hidden">
            <div class="justify-end w-full text-right mb-2">
              <button class="cursor-pointer" onClick={close}>
                <mark>[&times; Close]</mark>
              </button>
            </div>
            <div onClick={(e) => e.stopPropagation()}>{props.message}</div>
          </div>
        </div>
      </details>
    </div>
  );
}

function Banner(props: ParentProps) {
  const resolvedChildren = children(() => props.children);
  return (
    <>
      <hr class="h-4 bg-[url('/images/line-asterisk.svg')] bg-repeat-x bg-left border-0 flex-shrink-0" />
      {resolvedChildren()}
      <hr class="h-4 bg-[url('/images/line-oblique.svg')] bg-repeat-x bg-left border-0 flex-shrink-0" />
    </>
  );
}

function NodeMessage(props: { id: string; message: string }) {
  const reAnswer = new RegExp(/Answer:.+$/);
  const match = props.message.match(reAnswer);

  let mainText = props.message;
  let answer = '';

  if (match) {
    mainText = mainText.slice(0, props.message.length - match[0].length);
    answer = match[0];
  }

  return (
    <p class="uppercase">
      <span class="text-gensyn-green">[{props.id}]</span> {mainText} <strong>{answer}</strong>
    </p>
  );
}

const MultiLineChart = (props: { data: LeaderboardResponse }) => {
  let svgRef: SVGSVGElement | undefined;

  const chartData = createMemo(() => props.data);

  const margin = { top: 10, right: 10, bottom: 30, left: 50 };
  const width = 400 - margin.left - margin.right;
  const height = 300 - margin.top - margin.bottom;

  onMount(() => {
    drawChart();
  });

  createEffect(() => {
    updateChart();
  });

  function drawChart() {
    if (!svgRef) {
      return;
    }

    const svg = d3
      .select(svgRef)
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    const xScale = d3.scaleLinear().domain([0, 0]).range([0, width]);
    const yScale = d3.scaleLinear().domain([0, 0]).range([height, 0]);

    const allXs = chartData().leaders.flatMap((leader) => leader.values.map((d) => d.x));
    const allYs = chartData().leaders.flatMap((leader) => leader.values.map((d) => d.y));
    yScale.domain([d3.min(allYs)!, d3.max(allYs)!]);
    xScale.domain([d3.min(allXs)!, d3.max(allXs)!]);

    const xTicksCount = Math.min(5, allXs.length);

    // Horizontal grid lines
    svg
      .append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(yScale).tickSize(-width).tickFormat(() => '').ticks(5))
      .selectAll('.tick line')
      .attr('stroke', () => 'rgba(0, 0, 0, 0.3)')
      .attr('stroke-dasharray', '3,3')
      .filter((_, i) => i === 6)
      .attr('stroke', 'none');

    // Vertical grid lines
    svg
      .append('g')
      .attr('class', 'grid')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale).tickSize(-height).tickFormat(() => '').ticks(xTicksCount))
      .selectAll('line')
      .attr('stroke', () => 'rgba(0, 0, 0, 0.3)')
      .attr('stroke-dasharray', '3,3');

    const color = (i: number) => {
      const cs = [
        '#2A0D04',
        '#14BD4A',
        '#B800C4',
        '#FF6600',
        '#00A8F3',
        '#FFD700',
        '#8B4513',
        '#FF1493',
        '#7FFF00',
        '#9400D3'
      ];
      return cs[i % cs.length];
    };

    // Provide types for d in line generator
    const line = d3
      .line<{ x: number; y: number }>()
      .x((d) => xScale(d.x))
      .y((d) => yScale(d.y));

    svg
      .selectAll('.line')
      .data(chartData().leaders)
      .enter()
      .append('path')
      .attr('class', 'line')
      .attr('fill', 'none')
      .attr('stroke', (_, i) => color(i))
      .attr('stroke-width', 2)
      .attr('stroke-dasharray', '2 2')
      .attr('stroke-linejoin', 'round')
      .attr('d', leader => line(leader.values) as string)

    // Add X and Y axis
    svg
      .append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale).tickSize(0).tickPadding(10))
      .call(d3.axisBottom(xScale).tickSize(0).tickFormat((val) => `${Math.round(val.valueOf())}`).ticks(xTicksCount))
      .attr('stroke-width', 2)
      .selectAll('text')
      .style('font-size', '12px')
      .style('font-family', 'monospace');

    svg
      .append('g')
      .attr('class', 'y-axis')
      .attr('stroke-width', 2)
      .call(d3.axisLeft(yScale).tickSize(0).tickPadding(10))
      .selectAll('text')
      .style('font-size', '12px')
      .style('font-family', 'monospace');

    // Removes the top-most and right-most borders of the chart
    svg
      .selectAll('.domain')
      .filter((_, i) => i === 0 || i === 1)  // Removed explicit type annotations
      .attr('stroke', 'none');

    // Add X-axis label
    svg
      .append('text')
      .attr('class', 'x-axis-label')
      .attr('x', width / 2)
      .attr('y', height + margin.bottom)
      .attr('text-anchor', 'middle')
      .style('font-size', '10px')
      .style('font-family', 'Aux Mono')
      .text('SECONDS ELAPSED');
  }

  function updateChart() {
    if (!svgRef) {
      return;
    }
    // Remove previous chart before re-adding
    d3.select(svgRef).selectAll('*').remove();
    drawChart();
  }

  return <svg ref={svgRef}></svg>;
};

function Leaderboard(props: { leaders: { id: string; score: number }[] }) {
  return (
    <ul class="list-none uppercase">
      {props.leaders.map((leader, i) => (
        <li data-testid={`leader-${i}`}>
          <span class="text-gensyn-green">[{i}]</span>&nbsp;
          <span>
            {leader.id} [{leader.score}]
          </span>
        </li>
      ))}
    </ul>
  );
}