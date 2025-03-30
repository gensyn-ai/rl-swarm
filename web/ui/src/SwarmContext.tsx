import { createContext, createResource, createSignal, useContext, onMount, onCleanup, ParentProps } from "solid-js"
import { LeaderboardResponse, GossipResponse, RewardsResponse } from "./swarm.api"
import api from "./swarm.api"

export interface SwarmContextType {
	// Gossip info
	gossipMessages: () => { id: string; message: string; node: string }[]

	// The data for the actual leaderboard + loading, error states.
	leaders: () => LeaderboardResponse | null | undefined
	leadersLoading: () => boolean
	leadersError: () => Error | null

	// The number of nodes connected to the swarm.
	nodesConnected: () => number

	// The number of unique voters *(all time) + loading, error states.
	uniqueVoters: () => number
	uniqueVotersLoading: () => boolean
	uniqueVotersError: () => Error | null

	// Rewards info + loading, error states.
	rewards: () => RewardsResponse | null | undefined
	rewardsLoading: () => boolean
	rewardsError: () => Error | null

	// Swarm state
	currentRound: () => number
	currentStage: () => number

	// The number of polls that have occurred.
	// Currently used in place of a timestamp for simplicity.
	pollCount: () => number
}

export const SwarmContext = createContext<SwarmContextType>()

export function useSwarm() {
	const context = useContext(SwarmContext)
	if (!context) {
		throw new Error("useSwarm must be used within a SwarmProvider")
	}
	return context
}

export function SwarmProvider(props: ParentProps) {
	// Gossip state
	const [gossipMessages, setGossipMessages] = createSignal<{ id: string; message: string; node: string }[]>([])
	let seenMessageIds = new Set<string>()

	// Round and stage state
	const [currentRound, setCurrentRound] = createSignal(-1)
	const [currentStage, setCurrentStage] = createSignal(-1)

	// Leaderboard state
	const [pollCount, setPollCount] = createSignal(0)
	const [leaders, setLeaders] = createSignal<LeaderboardResponse | null | undefined>(null)
	const [rewards, setRewards] = createSignal<RewardsResponse | null | undefined>(null)

	const [nodesConnected, setNodesConnected] = createSignal(-1)
	const [uniqueVoters, setUniqueVoters] = createSignal(-1)

	// @ts-expect-warning - Intentionally unused variable
	const [_roundAndStage, { refetch: refetchRoundAndStage }] = createResource(async () => {
		const data = await api.getRoundAndStage()
		if (!data) {
			return undefined
		}

		setCurrentRound(data.round)
		setCurrentStage(data.stage)

		return data
	})

	const [_uniqueVoters, { refetch: refetchUniqueVoters }] = createResource(async () => {
		const data = await api.getUniqueVotersCount()
		if (!data) {
			return undefined
		}

		setUniqueVoters(data)
		return data
	})

	// Resources for data fetching
	// @ts-expect-warning - Intentionally unused variable
	const [_leaderboardData, { refetch: refetchLeaderboard }] = createResource(async () => {
		const data = await fetchLeaderboardData()
		if (!data || data.leaders.length === 0) {
			setLeaders(null)
			return
		}

		setLeaders(data)
		setNodesConnected(data.total)

		return data
	})

	// @ts-expect-warning - Intentionally unused variable
	const [_rewardsData, { refetch: refetchRewards }] = createResource(async () => {
		const data = await fetchRewardsData()
		if (!data || data.leaders.length === 0) {
			setRewards(null)
			return
		}

		// Multiply by 10 as an approximation of seconds.
		// TODO: Use actual timestamp.
		const xVal = pollCount() * 10
		const next = mergeLeaderboardData(xVal, data, rewards())

		// Truncate to top 10 for display.
		const nextRewards: RewardsResponse = {
			leaders: next?.leaders.slice(0, 10) ?? [],
			total: next?.total ?? 0,
		}

		setRewards(nextRewards)
		setPollCount((prev) => prev + 1)

		return nextRewards
	})

	// @ts-expect-warning - Intentionally unused variable
	const [_gossipData, { refetch: refetchGossip }] = createResource(async () => {
		const data = await fetchGossipData(currentRound())
		if (!data) {
			return undefined
		}

		const msgs = data.messages
			.filter((msg) => !seenMessageIds.has(msg.id))
			.map((msg) => {
				seenMessageIds.add(msg.id)
				return msg
			})

		setGossipMessages((prev) => {
			const newMessages = [...prev, ...msgs].slice(-200)
			return newMessages
		})

		if (seenMessageIds.size > 2000) {
			const temp = Array.from(seenMessageIds).slice(-2000)
			seenMessageIds = new Set(temp)
		}

		return { ...data, messages: msgs }
	})

	// Polling timers
	let leaderboardTimer: ReturnType<typeof setTimeout> | undefined = undefined
	let gossipTimer: ReturnType<typeof setTimeout> | undefined = undefined
	let roundAndStageTimer: ReturnType<typeof setTimeout> | undefined = undefined
	let rewardsTimer: ReturnType<typeof setTimeout> | undefined = undefined

	// Polling functions
	const pollGossip = async () => {
		await refetchGossip()

		if (gossipTimer !== undefined) {
			clearTimeout(gossipTimer)
		}

		gossipTimer = setTimeout(pollGossip, 10_000)
	}

	const pollLeaderboard = async () => {
		await refetchLeaderboard()
		await refetchUniqueVoters()

		if (leaderboardTimer !== undefined) {
			clearTimeout(leaderboardTimer)
		}

		leaderboardTimer = setTimeout(pollLeaderboard, 10_000)
	}

	const pollRoundAndStage = async () => {
		await refetchRoundAndStage()

		if (roundAndStageTimer !== undefined) {
			clearTimeout(roundAndStageTimer)
		}

		roundAndStageTimer = setTimeout(pollRoundAndStage, 10_000)
	}

	const pollRewards = async () => {
		await refetchRewards()

		if (rewardsTimer !== undefined) {
			clearTimeout(rewardsTimer)
		}

		rewardsTimer = setTimeout(pollRewards, 10_000)
	}

	// Setup and cleanup
	onMount(() => {
		// These already fire once immediately since the calls are created through createResource,
		// so we can add a 10s delay to start firing after that.
		leaderboardTimer = setTimeout(pollLeaderboard, 10_000)
		gossipTimer = setTimeout(pollGossip, 10_000)
		roundAndStageTimer = setTimeout(pollRoundAndStage, 10_000)
		rewardsTimer = setTimeout(pollRewards, 10_000)
	})

	onCleanup(() => {
		if (leaderboardTimer) {
			clearTimeout(leaderboardTimer)
		}

		if (gossipTimer) {
			clearTimeout(gossipTimer)
		}

		if (roundAndStageTimer) {
			clearTimeout(roundAndStageTimer)
		}

		if (rewardsTimer) {
			clearTimeout(rewardsTimer)
		}
	})

	const value: SwarmContextType = {
		currentRound,
		currentStage,

		gossipMessages,

		leaders,
		leadersLoading: () => _leaderboardData.loading,
		leadersError: () => _leaderboardData.error,

		pollCount,
		nodesConnected,

		uniqueVoters,
		uniqueVotersLoading: () => _uniqueVoters.loading,
		uniqueVotersError: () => _uniqueVoters.error,

		rewards,
		rewardsLoading: () => _rewardsData.loading,
		rewardsError: () => _rewardsData.error,
	}

	return <SwarmContext.Provider value={value}>{props.children}</SwarmContext.Provider>
}

async function fetchLeaderboardData(): Promise<LeaderboardResponse | undefined> {
	try {
		return await api.getLeaderboard()
	} catch (e) {
		console.error("fetchLeaderboardData failed", e)
		return undefined
	}
}

async function fetchGossipData(since: number): Promise<GossipResponse | undefined> {
	try {
		return await api.getGossip({ since })
	} catch (e) {
		console.error("fetchGossipData failed", e)
		return undefined
	}
}

async function fetchRewardsData(): Promise<RewardsResponse | undefined> {
	try {
		return await api.getRewards()
	} catch (e) {
		console.error("fetchRewardsData failed", e)
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
export function mergeLeaderboardData(xVal: number, apiRes: RewardsResponse | undefined, accumulator: RewardsResponse | null | undefined): RewardsResponse | null | undefined {
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

	const output = { ...apiRes }

	const accumLeadersById: Record<string, { id: string; values: { x: number; y: number }[]; score: number }> = {}
	accumulator.leaders.forEach((leader) => {
		accumLeadersById[leader.id] = { ...leader }
	})

	// The values stored are capped at 100 (arbitrarily chosen).
	output.leaders.forEach((leader) => {
		const prevVals = accumLeadersById[leader.id]?.values ?? []
		const nextVals = [...prevVals, { x: xVal, y: leader.score }].slice(-100)
		leader.values = nextVals
	})

	return output
}
