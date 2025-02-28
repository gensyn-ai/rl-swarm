import { children, createEffect, createMemo, createResource, createSignal, onCleanup, onMount, ParentProps, untrack } from 'solid-js'
import * as d3 from 'd3'
import Modal from './Modal'
import { getGossip, getLeaderboard, GossipResponse, LeaderboardResponse } from './swarm.api'

async function fetchLeaderboardData(): Promise<LeaderboardResponse|undefined> {
    try {
        const response = await getLeaderboard()
        return response
    } catch (e) {
        return undefined
    }
}

async function fetchGossipData(since: number): Promise<GossipResponse|undefined> {
    try {
        const response = await getGossip({ since })
        return response
    } catch (e) {
        return undefined
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
export function mergeLeaderboardData(xVal: number, apiRes: LeaderboardResponse | undefined, accumulator: LeaderboardResponse | null | undefined): LeaderboardResponse | null | undefined {
    if (apiRes === undefined) {
        return accumulator
    }

    // If this is the first poll, then no accumulator will have been created yet.
    if (accumulator === undefined || accumulator === null) {
        apiRes.leaders.forEach((leader) => {
            leader.values = [{ x: xVal, y: leader.score }]
        })
        return apiRes
    }

    const output = {...apiRes}

    const accumLeadersById: Record<string, { id: string, values: { x: number, y : number}[], score: number}> = {}
    accumulator.leaders.forEach((leader) => {
        accumLeadersById[leader.id] = {...leader}
    })

    // The values stored are capped at 100 (arbitrarily chosen).
    output.leaders.forEach((leader) => {
        const prevVals = accumLeadersById[leader.id]?.values ?? []
        const nextVals = [...prevVals, { x: xVal, y: leader.score }].slice(-100)
        leader.values = nextVals
    })

    return output
}

export default function Swarm() {
    // The UI tracks the latest round seen so it can query only for new data.
    // When the training loop resets on the backend, we expect to receive round=-1 back in the response.
    // Otherwise the backend will report its current round.
    const [lastGossipRound, setLastGossipRound] = createSignal(0)
    const [lastGossipStage, setLastGossipStage] = createSignal(0)

    const leaderboardSubtitle = createMemo(() => {
        let out = ''
        if (lastGossipRound() >= 0) {
            out = out + `: Round ${lastGossipRound()}`

            if (lastGossipStage() >= 0) {
                out = out + `, stage ${lastGossipStage()}`
            }
        }

        return out
    })

    // The UI also maintains a state for how many leaderboard polls we've done.
    // Currently just a side-effect of how the API/DHT is constructed.
    // This value is increased with each leaderboard poll as a way to show time.
    const [rewardXValue, setRewardXValue] = createSignal(0)

    // TODO: fill in UI with leaderboardData.loading, leaderboardData.error
    //
    // `leaderboardData` data represents the snapshot of leaderboard data at a given polling interval.
    // `leaders` is the accumulator for all previous values.
    // `leaderBoardTimer` is a timer id of the current poll iteration.
    const [leaderboardData, { refetch: refetchLeaderboard }] = createResource(fetchLeaderboardData)
    const [leaders, setLeaders] = createSignal<LeaderboardResponse|null|undefined>(null, {
        // Prevents the leaders data from updating if there are no changes in the data.
        // It's not stupid if it works. JSON.stringify is a little spooky, but we know the data is: 1) not large, and 2) not circular.
        equals: (oldData, newData) => {
            return JSON.stringify(oldData) === JSON.stringify(newData)
        }
    })

    // A derived value based on the leaderboard data.
    // If no leaders are coming in the response, then it's the signal of a new round.
    const showNewRoundModal = createMemo(() => {
        const leaders = leaderboardData()?.leaders ?? []
        return leaders.length <= 0
    })

    let leaderboardTimer: number | undefined = undefined

    // TODO: fill in UI with gossipData.loading, gossipData.error
    // 
    // `gossipData` is the raw gossip response from the API, which includes current round information.
    // `seenMessageIds` is used as a mechanism to de-duplicate the gossip messages since last poll.
    // `gossipMessages` is an accumulation of all prior gossip messages deduplicated.
    // `gossipTimer` is a timer id of the current poll iteration.
    const [gossipData, { refetch: refetchGossip }] = createResource(lastGossipRound, fetchGossipData)
    let seenMessageIds = new Set<string>()
    const [gossipMessages, setGossipMessages] = createSignal<{id: string, message: string, node: string}[]>([])
    let gossipTimer: number | undefined = undefined
    let gossipContainerRef: HTMLDivElement | undefined

    // Note that for the pollers below, rather than use a setInterval, a timeout is used to ensure
    // that the next poll only happens *after* the request resolves.

    // pollGossip fetches the latest gossip messages for the current round.
    const pollGossip = async () => {
        const nextGossip = await refetchGossip()

        if (nextGossip && nextGossip.currentRound) {
            setLastGossipRound(nextGossip?.currentRound)
        }

        if (nextGossip && nextGossip.currentStage) {
            setLastGossipStage(nextGossip?.currentStage)
        }

        if (gossipTimer !== undefined) {
            clearTimeout(gossipTimer)
        }

        gossipTimer = setTimeout(pollGossip, 10_000)
    }

    // pollLeaderboard fetches the latest leaderboard snapshot.
    const pollLeaderboard = async () => {
        await refetchLeaderboard()

        if (leaderboardTimer !== undefined) {
            clearTimeout(leaderboardTimer)
        }
        leaderboardTimer = setTimeout(pollLeaderboard, 10_000)
    }

    // leaderboardData listener.
    // Every time the leaderboard data is refetched, merge the new results with the old.
    createEffect(() => {
        if (!leaderboardData()) {
            return
        }

        // We're going to plot some new data, so increment the x-axis value.
        // Untrack so the create effect is not re-triggered when this updates. We don't care about this value in that way.
        setRewardXValue(untrack(rewardXValue) + 1)

        const next = mergeLeaderboardData(rewardXValue(), leaderboardData(), leaders())
        setLeaders(next)
    })

    // gossip listener.
    // Filters and dedupes messages to render on the client.
    createEffect(() => {
        const g = gossipData();
        if (!g || !g.messages || g.messages.length <= 0) {
            return
        }

        // Only get new messages from the response, and mark them seen.
        const msgs = g.messages
            .filter((msg) => !seenMessageIds.has(msg.id))
            .map((msg) => {
                seenMessageIds.add(msg.id)
                return msg
            })

        setGossipMessages([...untrack(gossipMessages), ...msgs].slice(-200))
        setLastGossipRound(g.currentRound)

        // Avoid the seenMessageIds growing unbounded.
        // Sets preserve insertion order, so the latest values can be preserved safely.
        // The size here is arbitrarily chosen.
        if (seenMessageIds.size > 2000) {
            const temp = Array.from(seenMessageIds).slice(-2000)
            seenMessageIds = new Set<string>(temp)
        }

        // Scroll to the latest messages
        if (gossipContainerRef) {
            gossipContainerRef.scrollTop = gossipContainerRef.scrollHeight
        }
    })

    onMount(() => {
        // Wait 10s before firing, since we already fetch once on mount.
        const lt = setTimeout(pollLeaderboard, 10_000)
        const gt = setTimeout(pollGossip, 10_000)

        onCleanup(() => {
            clearInterval(lt)
            clearInterval(gt)
        })
    })

    return (
        <main class="tracking-wider !font-normal !antialiased max-w-[876px] p-2 md:pt-12 md:pl-12 md:pr-0 flex flex-col justify-between md:min-h-screen ml-auto mr-auto">
            <Modal open={showNewRoundModal()} message="new round starting..." />
            <header>
                <h1 class="uppercase text-2xl tracking-[0.25em] mb-4">Gensyn: RL Swarm Client Interface</h1>
                <Banner>
                    <p class="uppercase leading-[calc(1em+8px)] mt-4 mb-4">
                        <mark class="p-[3px]">
                            A peer-to-peer system for collaborative reinforcement learning over the internet, running on consumer hardware.
                        </mark>
                    </p>
                </Banner>
            </header>

            <article class="flex flex-grow md:h-0 md:min-h-[600px] md:max-h-full gap-4 flex-col md:flex-row mb-12 mt-8">
                <section class="border-b pb-4 md:pb-0 md:border-b-0 md:border-r border-dashed border-gensyn-brown md:pr-8">
                    <div>
                        <SectionHeader title="cumulative reward" tooltip="This graph displays the cumulative reward for each node from the moment the page is loaded, not the full history from the start of a round." />
                        {leaders() ? <MultiLineChart data={leaders()!} /> : <span class="block w-[400px]">&lt; FETCHING LEADERS &gt;</span>}
                    </div>

                    <div class="mt-8">
                        <SectionHeader title={`leaderboard ${leaderboardSubtitle()}`} />
                        <Leaderboard leaders={leaders()?.leaders || []} />
                    </div>
                </section>

                <section class="pl-0 md:pl-8 flex-grow flex flex-col min-h-0">
                    <SectionHeader title="gossip" />
                    <div ref={gossipContainerRef} class="overflow-scroll overflow-x-hidden flex-grow min-h-0 max-h-[50vh] md:max-h-none" id="gossip-container">
                        <ul class="list-none">
                            {gossipMessages()?.length > 0 ? gossipMessages().map((msg) => {
                                return (
                                    <li><NodeMessage id={msg.node} message={msg.message} /></li>
                                )
                            }) : <span>&lt; FETCHING GOSSIP &gt;</span>}
                        </ul>
                    </div>
                </section>
            </article>

            <Banner>
                <footer class="flex items-center uppercase mt-8 mb-8">
                    <div class="flex-1">
                        <a href="https://github.com/gensyn-ai/rl-swarm"><mark>Join swarm</mark></a>
                    </div>
                    <div class="flex items-center">
                        <a class="flex items-center" href="https://gensyn.ai" target="_blank" rel="noopener noreferrer">
                            <img class="h-[50px]" src="/images/logo.gif" alt="A spinning gensyn logo" />
                            <img class="h-[30px]" src="/images/gen-logotype-dark-rgb.svg" alt="The gensyn name" />
                        </a>
                    </div>
                    <div class="flex items-center ml-8">
                        gensyn &copy;2025
                    </div>
                </footer>
            </Banner>
        </main>
    )
}

function SectionHeader(props: { title: string, tooltip?: string }) {
    return (
        <header class="flex items-center mb-4">
            <div class="flex-1"><mark class="uppercase">{props.title}</mark></div>
            {props.tooltip ? <Tooltip message={props.tooltip} /> : null}
        </header>
    )
}

function Tooltip(props: {message: string}) {
    return (
        <div class="relative group uppercase">
            <div class="flex-none tracking-tightest text-xs tracking-[-0.25em]">[+]</div>
            <div class="max-w-[25vw] absolute left-1/2 -translate-x-1/2 bottom-full mb-2 w-max px-2 py-1 bg-[#fcc6be] text-[#2A0D04] textsm opacity-0 group-hover:opacity-100 border border-[#2A0D04]">
                {props.message}
                <div class="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-l-[8px] border-r-[8px] border-t-[15px] border-l-transparent border-r-transparent border-t-[#2A0D04]"></div>
                <div class="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-l-[7px] border-r-[7px] border-t-[14px] border-l-transparent border-r-transparent border-t-[#FCC6BE] -mt-[1px]"></div>
            </div>
        </div>
    )
}

function Banner(props: ParentProps) {
    const resolvedChildren = children(() => props.children)
    return (
        <>
            <hr class="h-4 bg-[url('/images/line-asterisk.svg')] bg-repeat-x bg-left border-0 flex-shrink-0" />
            {resolvedChildren()}
            <hr class="h-4 bg-[url('/images/line-oblique.svg')] bg-repeat-x bg-left border-0 flex-shrink-0" />
        </>
    )
}

function NodeMessage(props: { id: string, message: string }) {
    const reAnswer = new RegExp(/Answer:.+$/)
    const match = props.message.match(reAnswer)

    let mainText = props.message
    let answer = ''

    if (match) {
        mainText = mainText.slice(0, props.message.length - match[0].length)
        answer = match[0]
    }

    return (
        <p class="uppercase">
            <span class="text-gensyn-green">[{props.id}]</span> {mainText} <strong>{answer}</strong>
        </p>
    )
}

const MultiLineChart = (props: { data: LeaderboardResponse }) => {
    let svgRef: SVGSVGElement | undefined

    // Props aren't automatically reactive, so we need to turn the props into a signal.
    // createMemo automatically updates when props.data changes, opposed to createSignal which is manually reactive.
    const chartData = createMemo(() => props.data)

    // TODO: Set dimensions magically
    const margin = { top: 10, right: 10, bottom: 30, left: 50 }
    const width = 400 - margin.left - margin.right
    const height = 300 - margin.top - margin.bottom

    onMount(() => {
        drawChart()
    })

    createEffect(() => {
        updateChart()
    })

    function drawChart() {
        if (!svgRef) {
            return
        }

        const svg = d3.select(svgRef)
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom)
            .append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`) // push the chart a bit to account for labels/legends

        // Define scales.
        // Scales map data space into SVG space.
        const xScale = d3.scaleLinear().domain([0, 0]).range([0, width])
        const yScale = d3.scaleLinear().domain([0, 0]).range([height, 0])

        // Set scales based on data.
        const allXs = chartData().leaders.flatMap((leader) => leader.values.map((d) => d.x))
        const allYs = chartData().leaders.flatMap((leader) => leader.values.map((d) => d.y))
        yScale.domain([d3.min(allYs)!, d3.max(allYs)!])
        xScale.domain([d3.min(allXs)!, d3.max(allXs)!])

        const xTicksCount = Math.min(5, allXs.length)

        // Horizontal grid lines
        // Setting a tick size to a negative width here extends the ticks across the chart.
        svg.append('g')
            .attr('class', 'grid')
            .call(d3.axisLeft(yScale).tickSize(-width).tickFormat(() => '').ticks(5))
            .selectAll('.tick line')
            .attr('stroke', () => 'rgba(0, 0, 0, 0.3)')
            .attr('stroke-dasharray', '3,3')
            .filter((_, i, _nodes) => i === 6)
            .attr('stroke', 'none')

        // Vertical grid lines
        svg.append('g')
            .attr('class', 'grid')
            .attr('transform', `translate(0,${height})`)
            .call(d3.axisBottom(xScale).tickSize(-height).tickFormat(() => '').ticks(xTicksCount))
            .selectAll('line')
            .attr('stroke', () => 'rgba(0, 0, 0, 0.3)')
            .attr('stroke-dasharray', '3,3')

        // Define color scale
        const color = (i: number) => {
            const cs = ['#2A0D04', '#14BD4A', '#B800C4', '#FF6600', '#00A8F3', '#FFD700', '#8B4513', '#FF1493', '#7FFF00', '#9400D3']
            return cs[i % cs.length]
        }

        // Define line generator.
        // Given data points, it generates an SVG path.
        const line = d3.line<{ x: number; y: number }>()
            .x(d => xScale(d.x))
            .y(d => yScale(d.y))

        // Draw data.
        svg.selectAll('.line')
            .data(chartData().leaders)
            .enter()
            .append('path')
            .attr('class', 'line')
            .attr('fill', 'none')
            .attr('stroke', (_, i) => color(i))
            .attr('stroke-width', 2)
            .attr('stroke-dasharray', '2 2')
            .attr('stroke-linejoin', 'round')
            .attr('d', d => line(d.values) as string)


        // Add X and Y axis
        svg.append('g')
            .attr("class", "x-axis")
            .attr('transform', `translate(0,${height})`)
            .call(d3.axisBottom(xScale).tickSize(0).tickPadding(10))
            .call(d3.axisBottom(xScale).tickSize(0).tickFormat((d) => `${Math.round(d.valueOf())}`).ticks(xTicksCount))
            .attr('stroke-width', 2)
            .selectAll('text')
            .style('font-size', '12px')
            .style('font-family', 'monospace')

        svg.append('g')
            .attr("class", "y-axis")
            .attr('stroke-width', 2)
            .call(d3.axisLeft(yScale).tickSize(0).tickPadding(10))
            .selectAll('text')
            .style('font-size', '12px')
            .style('font-family', 'monospace')

        // Removes the top-most and right-most borders of the chart
        svg.selectAll('.domain')
            .filter((_, i, _nodes) => i == 0 || i == 1)
            .attr('stroke', 'none')

        // Add X-axis label
        svg.append('text')
            .attr('class', 'x-axis-label')
            .attr('x', width / 2)  // Center it horizontally
            .attr('y', height + margin.bottom)  // Position it below the X-axis
            .attr('text-anchor', 'middle')  // Center the text
            .style('font-size', '10px')
            .style('font-family', 'Aux Mono')
            .text('DHT POLLS');
  }

    function updateChart() {
        if (!svgRef) {
            return
        }
        // Remove previous chart before re-adding
        // This makes the chart update less smooth, but removes any issues with re-rendering.
        d3.select(svgRef).selectAll("*").remove()
        drawChart()
  }

  return <svg ref={svgRef}></svg>;
};

function Leaderboard(props: { leaders: { id: string, score: number}[] }) {
    return (
        <>
            <ul class="list-none uppercase">
                {props.leaders.map((leader, i) => {
                    return (
                        <li data-testid={`leader-${i}`}>
                            <span class="text-gensyn-green">[{i}]</span>&nbsp;
                            <span>{leader.id} [{leader.score}]</span>
                        </li>
                    )
                })}
            </ul>
        </>
    )
}
