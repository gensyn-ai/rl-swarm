import { useSwarm } from "../SwarmContext"
import LoadingSpinner from "./LoadingSpinner"
import ErrorMessage from "./ErrorMessage"
import SectionHeader from "./SectionHeader"
import { createResource, createSignal, Show } from "solid-js"

export default function Leaderboard() {
	const { leaders, leadersLoading, leadersError } = useSwarm()

	// Search state: input is the raw text from the <input>, but query is what is searched for.
	// This only exists in two signals so that we search on submit, not on each keystroke.
	const [searchInput, setSearchInput] = createSignal("")
	const [leaderSearchQuery, setLeaderSearchQuery] = createSignal<string | null>(null)

	const [leaderSearchResult] = createResource(leaderSearchQuery, async (query: string) => {
		if (!query || query.length === 0) {
			return
		}

		// If the leaderboard contains the query, no reason to search.
		// The row will be highlighted.
		const found = leaders()?.leaders.find((leader) => leader.id === query) !== undefined
		if (found) {
			return
		}

		// Simulate network request
		await new Promise((resolve) => setTimeout(resolve, 2_000))

		// TODO: Need this data in the API
		return {
			id: query,
			score: 1,
			values: [],
			index: 99,
		}
	})

	const searchLeaderboard = (e: SubmitEvent) => {
		e.preventDefault()

		// This will trigger the refetch for the leaderSearchResult.
		setLeaderSearchQuery(searchInput())
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
					Nodes Connected: 12345
				</div>
				<div class="border border-2 border-dotted p-2">
					Total Models Trained: 67890
				</div>
			</div>

			{/* Header + Search */}
			<div class="grid grid-cols-1 md:grid-cols-2 gap-2">
				<SectionHeader title="Leaderboard" tooltip="Foobarbaz" />

				<div class="md:ml-2 relative">
					<form onSubmit={searchLeaderboard} class="flex uppercase mt-2 mb-2 uppercase" inert={leaderSearchResult.loading}>
						<input type="text" value={searchInput()} onInput={(e) => setSearchInput(e.currentTarget.value)} placeholder="ENTER YOUR NODE ADDRESS" class="border border-gensyn-brown p-2 flex-grow focus:outline-none focus:ring-0 focus:border-gensyn-green" />
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
							Cumulative&nbsp;Reward
							<span class="absolute bottom-0 left-0 w-[100%] border-b border-dotted"></span>
						</th>
					</tr>
				</thead>
				<tbody>
					{leaders()?.leaders.slice(0, 10).map((leader, index) => (
						<tr class={`${leader.id === leaderSearchQuery() ? "bg-gensyn-green text-white" : ""}`}>
							{/* Rank */}
							<td class="text-left">{index + 1}</td>

							{/* Name */}
							<td class="text-left">
								<span>{leader.id}</span>
							</td>

							{/* Participation */}
							<td class="text-left">
								<span>{leader.score}</span>
							</td>

							{/* Cumulative Reward */}
							<td class="text-right hidden md:table-cell">
								<span>{leader.score}</span>
							</td>
						</tr>
					))}
				</tbody>
				<tbody>
					<Show when={leaderSearchResult()}>
						<tr class={`${leaderSearchResult() && leaderSearchResult()?.id === leaderSearchQuery() ? "bg-gensyn-green text-white" : ""}`}>
							<td class="text-left">{leaderSearchResult()?.index}</td>
							<td class="text-left">
								<span>{leaderSearchResult()?.id}</span>
							</td>
							<td class="text-left">
								<span>{leaderSearchResult()?.score}</span>
							</td>
							<td class="text-right hidden md:table-cell">
								<span>{leaderSearchResult()?.score}</span>
							</td>
						</tr>
					</Show>
					<Show when={leaderSearchResult.loading}>
						<tr>
							<td colspan="4" class="text-center">
								<LoadingSpinner message="Searching..." />
							</td>
						</tr>
					</Show>
					<Show when={leaderSearchResult.error}>
						<tr>
							<td colspan="4" class="text-center">
								<ErrorMessage message="Failed to search leaderboard" />
							</td>
						</tr>
					</Show>
				</tbody>
			</table>
		</div>
	)
}
