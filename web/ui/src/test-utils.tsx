import { ParentProps } from "solid-js"
import { SwarmContext, SwarmContextType } from "./SwarmContext"
import { LeaderboardResponse, RewardsResponse } from "./swarm.api"

export const defaultMockSwarmContext: SwarmContextType = {
	gossipMessages: () => [],
	leaders: () => null,
	leadersLoading: () => false,
	leadersError: () => null,
	nodesConnected: () => -1,
	uniqueVoters: () => -1,
	uniqueVotersLoading: () => false,
	uniqueVotersError: () => null,
	rewards: () => null,
	rewardsLoading: () => false,
	rewardsError: () => null,
	currentRound: () => -1,
	currentStage: () => -1,
	pollCount: () => 0,
}

interface MockSwarmProviderProps extends ParentProps {
	values: {
		gossipMessages?: () => { id: string; message: string; node: string }[]
		leaders?: () => LeaderboardResponse | null | undefined
		leadersLoading?: () => boolean
		leadersError?: () => Error | null
		nodesConnected?: () => number
		uniqueVoters?: () => number
		uniqueVotersLoading?: () => boolean
		uniqueVotersError?: () => Error | null
		rewards?: () => RewardsResponse | null | undefined
		rewardsLoading?: () => boolean
		rewardsError?: () => Error | null
		currentRound?: () => number
		currentStage?: () => number
		pollCount?: () => number
	}
}

export function MockSwarmProvider(props: MockSwarmProviderProps) {
	// Destructuring loses reactivity.
	const value: SwarmContextType = {
		gossipMessages: () => props.values.gossipMessages?.() || defaultMockSwarmContext.gossipMessages(),
		leaders: () => props.values.leaders?.() || defaultMockSwarmContext.leaders(),
		leadersLoading: () => props.values.leadersLoading?.() || defaultMockSwarmContext.leadersLoading(),
		leadersError: () => props.values.leadersError?.() || defaultMockSwarmContext.leadersError(),
		nodesConnected: () => props.values.nodesConnected?.() || defaultMockSwarmContext.nodesConnected(),
		uniqueVoters: () => props.values.uniqueVoters?.() || defaultMockSwarmContext.uniqueVoters(),
		uniqueVotersLoading: () => props.values.uniqueVotersLoading?.() || defaultMockSwarmContext.uniqueVotersLoading(),
		uniqueVotersError: () => props.values.uniqueVotersError?.() || defaultMockSwarmContext.uniqueVotersError(),
		rewards: () => props.values.rewards?.() || defaultMockSwarmContext.rewards(),
		rewardsLoading: () => props.values.rewardsLoading?.() || defaultMockSwarmContext.rewardsLoading(),
		rewardsError: () => props.values.rewardsError?.() || defaultMockSwarmContext.rewardsError(),
		currentRound: () => props.values.currentRound?.() || defaultMockSwarmContext.currentRound(),
		currentStage: () => props.values.currentStage?.() || defaultMockSwarmContext.currentStage(),
		pollCount: () => props.values.pollCount?.() || defaultMockSwarmContext.pollCount(),
	}

	return <SwarmContext.Provider value={value}>{props.children}</SwarmContext.Provider>
}
