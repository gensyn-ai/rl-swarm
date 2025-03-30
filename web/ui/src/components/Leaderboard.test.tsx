import { render, waitFor, fireEvent } from "@solidjs/testing-library"
import Leaderboard from "./Leaderboard"
import { vi, afterEach, beforeEach, describe, expect, it } from "vitest"
import { MockSwarmProvider } from "../test-utils"
import { LeaderboardResponse } from "../swarm.api"

vi.mock("../swarm.api", () => ({
	default: {
		getPeerInfoFromName: vi.fn(),
	},
}))

describe("Leaderboard", () => {
	const mockLeaders: LeaderboardResponse = {
		leaders: [
			{ id: "node1", values: [{ x: 0, y: 1 }], score: 1, nickname: "nn1", participation: 10 },
			{ id: "node2", values: [{ x: 0, y: 2 }], score: 2, nickname: "nn2", participation: 20 },
		],
		total: 2,
	}

	beforeEach(() => {
		vi.resetAllMocks()
	})

	afterEach(() => {
		vi.clearAllMocks()
	})

	it("should show loading state", () => {
		const result = render(() => (
			<MockSwarmProvider
				values={{
					leaders: () => ({ leaders: [], total: 0 }),
					leadersLoading: () => true,
					nodesConnected: () => -1,
					uniqueVoters: () => -1,
				}}
			>
				<Leaderboard />
			</MockSwarmProvider>
		))

		expect(result.getByText("Fetching leaders")).toBeTruthy()
	})

	it("should show error state", () => {
		const result = render(() => (
			<MockSwarmProvider
				values={{
					leaders: () => null,
					leadersError: () => new Error("Failed to fetch"),
					nodesConnected: () => -1,
					uniqueVoters: () => -1,
				}}
			>
				<Leaderboard />
			</MockSwarmProvider>
		))

		expect(result.getByText("Failed to fetch leaderboard data")).toBeTruthy()
	})

	it("should render leaderboard data", async () => {
		const result = render(() => (
			<MockSwarmProvider
				values={{
					leaders: () => mockLeaders,
					nodesConnected: () => 2,
					uniqueVoters: () => 5,
				}}
			>
				<Leaderboard />
			</MockSwarmProvider>
		))

		await waitFor(() => {
			// Check names are displayed
			expect(result.getByText("nn1", { selector: '[data-column="name"]' })).toBeTruthy()
			expect(result.getByText("nn2", { selector: '[data-column="name"]' })).toBeTruthy()

			// Check rewards are displayed
			expect(result.getByText("1", { selector: '[data-column="reward"]' })).toBeTruthy()
			expect(result.getByText("2", { selector: '[data-column="reward"]' })).toBeTruthy()

			// Check participation values are displayed
			expect(result.getByText("10", { selector: '[data-column="participation"]' })).toBeTruthy()
			expect(result.getByText("20", { selector: '[data-column="participation"]' })).toBeTruthy()

			// Check ranks are displayed
			expect(result.getByText("1", { selector: '[data-column="rank"]' })).toBeTruthy()
			expect(result.getByText("2", { selector: '[data-column="rank"]' })).toBeTruthy()
		})
	})

	describe("Search functionality", () => {
		it("should handle finding a leader in the top 10", async () => {
			const mockTopLeaders = {
				leaders: [
					{ id: "node1", values: [{ x: 0, y: 1 }], score: 1, nickname: "alpha", participation: 10 },
					{ id: "node2", values: [{ x: 0, y: 2 }], score: 2, nickname: "beta", participation: 20 },
					{ id: "node3", values: [{ x: 0, y: 3 }], score: 3, nickname: "gamma", participation: 30 },
					{ id: "node4", values: [{ x: 0, y: 4 }], score: 4, nickname: "delta", participation: 40 },
					{ id: "node5", values: [{ x: 0, y: 5 }], score: 5, nickname: "epsilon", participation: 50 },
				],
				total: 5,
			}

			const result = render(() => (
				<MockSwarmProvider
					values={{
						leaders: () => mockTopLeaders,
						nodesConnected: () => 5,
						uniqueVoters: () => 5,
					}}
				>
					<Leaderboard />
				</MockSwarmProvider>
			))

			const searchInput = result.getByPlaceholderText("ENTER YOUR NODE NAME")
			fireEvent.input(searchInput, { target: { value: "gamma" } })
			fireEvent.click(result.getByText("Search"))

			// Wait for and verify the searched leader is highlighted
			await waitFor(() => {
				const searchedLeader = result.getByTestId("leader-node3")
				expect(searchedLeader).toBeTruthy()
				expect(searchedLeader.classList.contains("bg-gensyn-green")).toBeTruthy()
				expect(searchedLeader.classList.contains("text-white")).toBeTruthy()
			})
		})

		it("should handle finding a leader outside the top 10 but in the leaderboard", async () => {
			const mockLeaders = {
				leaders: Array.from({ length: 11 }, (_, i) => ({
					id: `node${i + 1}`,
					values: [{ x: 0, y: i + 1 }],
					score: i + 1,
					nickname: `node${i + 1}`,
					participation: (i + 1) * 10
				})),
				total: 11,
			}

			const result = render(() => (
				<MockSwarmProvider
					values={{
						leaders: () => mockLeaders,
						nodesConnected: () => 11,
						uniqueVoters: () => 11
					}}
				>
					<Leaderboard />
				</MockSwarmProvider>
			))

			const searchInput = result.getByPlaceholderText("ENTER YOUR NODE NAME")
			fireEvent.input(searchInput, { target: { value: "node11" } })
			fireEvent.click(result.getByText("Search"))

			await waitFor(() => {
				const searchedLeader = result.getByTestId("leader-search-result=node11")
				expect(searchedLeader).toBeTruthy()
			})
		})
	})
})
