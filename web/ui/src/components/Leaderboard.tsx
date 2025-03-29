import { useSwarm } from "../SwarmContext"
import LoadingSpinner from "./LoadingSpinner"
import ErrorMessage from "./ErrorMessage"
import SectionHeader from "./SectionHeader"
import { createResource, createSignal, Show, Switch, Match } from "solid-js"
import swarmApi, { LeaderboardResponse } from "../swarm.api"

export default function Leaderboard() {
	const { leaders, leadersLoading, leadersError, nodesConnected, uniqueVoters, uniqueVotersLoading } = useSwarm()

	// Search state: input is the raw text from the <input>, but query is what is searched for.
	// This only exists in two signals so that we search on submit, not on each keystroke.
	const [searchInput, setSearchInput] = createSignal("")
	const [leaderSearchQuery, setLeaderSearchQuery] = createSignal<string | null>(null)
	const [searchTrigger, setSearchTrigger] = createSignal(0)

	type SearchResult = {
		index: number,
		leader: LeaderboardResponse["leaders"][number],
		inLeaderboard: boolean,
	}

	// This is a little hacky, but I want to allow triggering another search even if the leaderSearchQuery hasn't changed.
	// The searchTrigger() signal is incremented with each search, so we can always re-fire the search.
	const [leaderSearchResult] = createResource(() => ({ query: leaderSearchQuery(), trigger: searchTrigger() }), async ({ query }) => {
		if (!query || query.length === 0) {
			return
		}

		const index = leaders()?.leaders.findIndex((leader) => {
			const qlc = query.toLowerCase()
			return leader.nickname.toLowerCase() === qlc || leader.id.toLowerCase() === qlc
		})

		// Index must be tracked, because if the leader is outside the top 10, 
		// it needs to render elsewhere in the leaderboard table.
		if (index !== undefined && index !== null && index >= 0) {
			return {
				index: index,
				leader: leaders()?.leaders[index],
				inLeaderboard: true,
			} as SearchResult
		}

		// The searched name is not in the leaderboard.
		// There's three cases here to consider:
		// 1. The name doesn't exist at all.
		// 2. The name exists, but the peer is not connected to the DHT.
		// 3. The name exists, and the peer is connected to the DHT, so we can find it.
		//
		// We can't tell the difference between 1 and 2, so those can be handled the same way.
		const leader = await swarmApi.getPeerInfoFromName(query)
		if (!leader) {
			throw new Error(`could not find peer ${query}`)
		}

		// Otherwise the searched leader is not in the leaderboard.

		/*
		if (index !== undefined && index !== null) {
			return {
				id: query,
				score: 1,
				values: [],
			}
		if (found !== undefined && found !== null) {
			return found
		}

		const leader = await swarmApi.getPeerInfoFromName(query)
		if (!leader) {
			return
		}
			*/

			/*
		// Simulate network request
		await new Promise((resolve) => setTimeout(resolve, 2_000))

		// TODO: Need this data in the API
		return {
			id: query,
			score: 1,
			values: [],
			index: 99,
			nickname: "foobarbaz",
			participation: 0.5,
		} as SearchResult
			*/
	})

	const searchLeaderboard = (e: SubmitEvent) => {
		e.preventDefault()

		// This will trigger the refetch for the leaderSearchResult.
		setLeaderSearchQuery(searchInput())
		setSearchTrigger(prev => prev + 1)
	}

	/**
	 * Checks if the leader is the searched leader.
	 * @param leader - The leader to check.
	 * @returns True if the leader is the searched leader, false otherwise.
	 */
	const isSearchedLeader = (target: LeaderboardResponse["leaders"][number]) => {
		if (!leaderSearchResult()) {
			return false
		}
		const leader = leaderSearchResult()?.leader
		if (!leader) {
			return false
		}
		const matchId = leader.id.toLowerCase() === target.id.toLowerCase()
		const matchName = leader.nickname.toLowerCase() === target.nickname.toLowerCase()

		return matchId || matchName
	}

	// Only show spinner on the first render.
	// Otherwise we silently refresh.
	if (leadersLoading() && leaders()?.leaders.length === 0) {
		return <LoadingSpinner message="Fetching leaders" />
	}

	if (leadersError()) {
		return <ErrorMessage message="Failed to fetch leaderboard data" />
	}

	return (
		<div class="w-full">
			{/* Stats */}
			<div class="grid grid-cols-1 md:grid-cols-2 gap-2 mb-4">
				<div class="border border-2 border-dotted p-2">
					{/* This value comes from the leaderboard API since it's the total number of peers (DHT). */}
					current Nodes Connected:
					<Show when={leadersLoading() && leaders()?.leaders.length === 0} fallback={nodesConnected()}>
						<LoadingSpinner message="..." />
					</Show>
				</div>
				<div class="border border-2 border-dotted p-2">
					Total Models Trained:
					<Show when={uniqueVotersLoading() && uniqueVoters() === -1} fallback={uniqueVoters()}>
						<LoadingSpinner message="..." />
					</Show>
				</div>
			</div>

			{/* Header + Search */}
			<div class="grid grid-cols-1 md:grid-cols-2 gap-2">
				<SectionHeader title="Leaderboard" tooltip="Foobarbaz" />

				<div class="md:ml-2 relative">
					<form onSubmit={searchLeaderboard} class="flex uppercase mt-2 mb-2 uppercase" inert={leaderSearchResult.loading}>
						<input type="text" value={searchInput()} onInput={(e) => setSearchInput(e.currentTarget.value)} placeholder="ENTER YOUR NODE NAME" class="border border-gensyn-brown p-2 flex-grow focus:outline-none focus:ring-0 focus:border-gensyn-green" />
						<button type="submit" class="uppercase border-t border-b border-r border-gensyn-brown p-2 bg-[rgba(0,0,0,0.05)]">
							Search
						</button>
					</form>
				</div>
			</div>

			<table class="min-w-full table-auto border-collapse border-dotted border-separate border-spacing-1 border-spacing-x-0 border-2 py-1 px-4">
				<thead>
					<tr class="align-top">
						<th class="font-normal text-left w-auto relative">
							Rank
							<span class="absolute bottom-0 left-0 w-[90%] border-b border-dotted"></span>
						</th>
						<th class="font-normal text-left w-auto relative">
							Name
							<span class="absolute bottom-0 left-0 w-[90%] border-b border-dotted"></span>
						</th>
						<th class="font-normal text-left w-auto pr-4 relative">
							Participation
							<span class="absolute bottom-0 left-0 w-[90%] border-b border-dotted"></span>
						</th>
						<th class="font-normal text-left w-auto relative hidden md:table-cell">
							Training&nbsp;Reward
							<span class="absolute bottom-0 left-0 w-[100%] border-b border-dotted"></span>
						</th>
					</tr>
				</thead>
				<tbody class="uppercase">
					{leaders()
						?.leaders.slice(0, 10)
						.map((leader, index) => (
							<tr classList={{ "bg-gensyn-green text-white": isSearchedLeader(leader) }}>
								{/* Rank */}
								<td class="text-left">{index + 1}</td>

								{/* Name */}
								<td class="text-left">
									<span>{leader.nickname}</span>
								</td>

								{/* Participation */}
								<td class="text-left">
									<span>{leader.participation}</span>
								</td>

								{/* Cumulative Reward */}
								<td class="text-right hidden md:table-cell">
									<span>{leader.score}</span>
								</td>
							</tr>
						))}
				</tbody>
				<tbody class="uppercase">
					<Switch>
						<Match when={leaderSearchResult.loading}>
							<tr>
								<td colspan="4" class="text-center"><LoadingSpinner message="Searching..." /></td>
							</tr>
						</Match>
						<Match when={leaderSearchResult.error}>
							<tr>
								<td colspan="4" class="text-center"><ErrorMessage message={`${leaderSearchResult.error?.message || "Failed to search leaderboard"}`} /></td>
							</tr>
						</Match>
						<Match when={leaderSearchResult() && leaderSearchResult()!.index > 10}>
							<tr class="bg-gensyn-green text-white">
								<td class="text-left">
									{leaderSearchResult()?.inLeaderboard ? leaderSearchResult()!.index : ">99"}
								</td>
								<td class="text-left">
									<span>{leaderSearchResult()?.leader?.nickname}</span>
								</td>
								<td class="text-left">
									<span>{leaderSearchResult()?.leader?.participation}</span>
								</td>
								<td class="text-right hidden md:table-cell">
									<span>{leaderSearchResult()?.leader?.score}</span>
								</td>
							</tr>
						</Match>
					</Switch>
				</tbody>
			</table>
		</div>
	)
}
