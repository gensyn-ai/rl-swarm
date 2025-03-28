import { render } from "@solidjs/testing-library"
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest"
import { SwarmProvider, useSwarm, mergeLeaderboardData } from "./SwarmContext"
import api, { LeaderboardResponse } from "./swarm.api"

// Mock the API calls
vi.mock("./swarm.api", () => ({
	default: {
		getGossip: vi.fn(),
		getLeaderboard: vi.fn(),
		getRoundAndStage: vi.fn(),
	},
}))

describe("SwarmProvider", () => {
	beforeEach(() => {
		vi.useFakeTimers()
		vi.resetAllMocks()
	})

	afterEach(() => {
		vi.useRealTimers()
	})

	it("should initialize with default values", () => {
		const TestComponent = () => {
			const ctx = useSwarm()
			expect(ctx.currentRound()).toBe(-1)
			expect(ctx.currentStage()).toBe(-1)
			expect(ctx.gossipMessages()).toEqual([])
			expect(ctx.leaders()).toBeNull()
			expect(ctx.uniqueVoters()).toBe(-1)
			expect(ctx.pollCount()).toBe(0)
			return null
		}

		render(() => (
			<SwarmProvider>
				<TestComponent />
			</SwarmProvider>
		))
	})

	it("should update leaderboard when data is fetched", async () => {
		vi.mocked(api.getLeaderboard).mockResolvedValue({
			leaders: [
				{ id: "node1", score: 1.0, values: [], nickname: "nn1", participation: 1 },
				{ id: "node2", score: 0.5, values: [], nickname: "nn2", participation: 0.5 },
			],
			total: 2,
		})
		vi.mocked(api.getGossip).mockResolvedValue({ messages: [] })
		vi.mocked(api.getRoundAndStage).mockResolvedValue({ round: 1, stage: 1 })

		// TestComponent displays the data we want to test so we can validate that the data is correct.
		const TestComponent = () => {
			const ctx = useSwarm()
			return (
				<div>
					<div data-testid="leader-count">{ctx.leaders()?.leaders.length}</div>
				</div>
			)
		}

		const { findByTestId } = render(() => (
			<SwarmProvider>
				<TestComponent />
			</SwarmProvider>
		))

		// Wait for the initial API calls to resolve
		await vi.advanceTimersByTimeAsync(0)

		// Initial state
		const leaderCount = await findByTestId("leader-count")
		expect(leaderCount.textContent).toBe("2")
	})

	it("should poll for updates", async () => {
		vi.mocked(api.getLeaderboard).mockResolvedValue({
			leaders: [{ id: "node1", score: 1.0, values: [], nickname: "nn1", participation: 1 }],
			total: 1,
		})
		vi.mocked(api.getGossip).mockResolvedValue({ messages: [] })
		vi.mocked(api.getRoundAndStage).mockResolvedValue({ round: 1, stage: 1 })

		render(() => (
			<SwarmProvider>
				<div />
			</SwarmProvider>
		))

		// Initial calls
		expect(api.getLeaderboard).toHaveBeenCalledTimes(1)
		expect(api.getGossip).toHaveBeenCalledTimes(1)
		expect(api.getRoundAndStage).toHaveBeenCalledTimes(1)

		// Advance time to trigger polls
		await vi.advanceTimersByTimeAsync(10_000)

		// Wait for and verify additional calls
		expect(api.getLeaderboard).toHaveBeenCalledTimes(2)
		expect(api.getGossip).toHaveBeenCalledTimes(2)
		expect(api.getRoundAndStage).toHaveBeenCalledTimes(2)
	})

	it("should update gossip messages", async () => {
		vi.mocked(api.getGossip).mockResolvedValue({
			messages: [
				{ id: "msg1", message: "test1", node: "node1" },
				{ id: "msg2", message: "test2", node: "node2" },
			],
		})
		vi.mocked(api.getLeaderboard).mockResolvedValue({
			leaders: [],
			total: 0,
		})
		vi.mocked(api.getRoundAndStage).mockResolvedValue({ round: 1, stage: 1 })

		const TestComponent = () => {
			const ctx = useSwarm()
			return (
				<div>
					<div data-testid="gossip-count">{ctx.gossipMessages().length}</div>
					<div data-testid="current-round">{ctx.currentRound()}</div>
				</div>
			)
		}

		const { findByTestId } = render(() => (
			<SwarmProvider>
				<TestComponent />
			</SwarmProvider>
		))

		// Wait for initial API calls to resolve
		await vi.advanceTimersByTimeAsync(0)

		// Check both the round and gossip count
		const currentRound = await findByTestId("current-round")
		const gossipCount = await findByTestId("gossip-count")

		expect(currentRound.textContent).toBe("1")
		expect(gossipCount.textContent).toBe("2")
	})

	it("should merge leaderboard messages", async () => {
		vi.mocked(api.getLeaderboard)
			.mockResolvedValueOnce({
				leaders: [
					{ id: "nodea", values: [{ x: 0, y: 1 }], score: 1, nickname: "nn1", participation: 1 },
					{ id: "nodeb", values: [{ x: 0, y: 1 }], score: 1, nickname: "nn2", participation: 0.5 },
				],
				total: 2,
			})
			.mockResolvedValueOnce({
				leaders: [
					{ id: "nodec", values: [{ x: 0, y: 2 }], score: 3, nickname: "nn3", participation: 1 },
					{ id: "nodea", values: [{ x: 0, y: 2 }], score: 2, nickname: "nn1", participation: 0.5 },
					{ id: "nodeb", values: [{ x: 0, y: 2 }], score: 2, nickname: "nn2", participation: 0.5 },
				],
				total: 3,
			})
		vi.mocked(api.getGossip).mockResolvedValue({ messages: [] })
		vi.mocked(api.getRoundAndStage).mockResolvedValue({ round: 1, stage: 1 })

		const TestComponent = () => {
			const ctx = useSwarm()
			return (
				<div>
					<div data-testid="leader-0">
						<span class="text-gensyn-green">[0]</span>&nbsp;
						<span>
							{ctx.leaders()?.leaders[0]?.id} [{ctx.leaders()?.leaders[0]?.score}]
						</span>
					</div>
					<div data-testid="leader-1">
						<span class="text-gensyn-green">[1]</span>&nbsp;
						<span>
							{ctx.leaders()?.leaders[1]?.id} [{ctx.leaders()?.leaders[1]?.score}]
						</span>
					</div>
					<div data-testid="leader-2">
						<span class="text-gensyn-green">[2]</span>&nbsp;
						<span>
							{ctx.leaders()?.leaders[2]?.id} [{ctx.leaders()?.leaders[2]?.score}]
						</span>
					</div>
					<div data-testid="nodea-values">
						{ctx
							.leaders()
							?.leaders.find((l) => l.id === "nodea")
							?.values.map((v) => `(${v.x}, ${v.y})`)
							.join(" ")}
					</div>
				</div>
			)
		}

		const { findByTestId } = render(() => (
			<SwarmProvider>
				<TestComponent />
			</SwarmProvider>
		))

		// Wait for initial API calls to resolve
		await vi.advanceTimersByTimeAsync(0)

		// Helper function to account for the &nbsp; in the text content
		const normalizedText = (n: HTMLElement) => (n ? n.textContent?.replace(/\u00A0/g, " ").trim() : "")

		// Check initial state
		let first = await findByTestId("leader-0")
		expect(normalizedText(first)).toEqual("[0] nodea [1]")

		let second = await findByTestId("leader-1")
		expect(normalizedText(second)).toEqual("[1] nodeb [1]")

		// Advance time to trigger polling
		await vi.advanceTimersByTimeAsync(10_000)

		// Check updated state
		first = await findByTestId("leader-0")
		expect(normalizedText(first)).toEqual("[0] nodec [3]")

		second = await findByTestId("leader-1")
		expect(normalizedText(second)).toEqual("[1] nodea [2]")

		let third = await findByTestId("leader-2")
		expect(normalizedText(third)).toEqual("[2] nodeb [2]")

		// Verify values array is maintained
		const nodeaValues = await findByTestId("nodea-values")
		expect(nodeaValues.textContent).toBe("(0, 1) (10, 2)")

		expect(api.getLeaderboard).toHaveBeenCalledTimes(2)
	})

	describe("mergeLeaderboardData", () => {
		type TestConfig = {
			xVal: number
			response?: LeaderboardResponse
			accumulator?: LeaderboardResponse
			wantOut: LeaderboardResponse
		}

		it.each([
			[
				"returns the accumulator if no response",
				{
					xVal: 42,
					response: undefined,
					accumulator: {
						leaders: [],
						total: 0,
					},
					wantOut: {
						leaders: [],
						total: 0,
					},
				},
			],
			[
				"returns the response with new values if no accumulator",
				{
					xVal: 42,
					response: {
						leaders: [
							{ id: "node-a", score: 1.0, values: [], nickname: "nn1", participation: 1 },
							{ id: "node-b", score: 0.5, values: [], nickname: "nn2", participation: 0.5 },
						],
						total: 2,
					},
					accumulator: undefined,
					wantOut: {
						leaders: [
							{ id: "node-a", score: 1.0, values: [{ x: 42, y: 1.0 }], nickname: "nn1", participation: 1 },
							{ id: "node-b", score: 0.5, values: [{ x: 42, y: 0.5 }], nickname: "nn2", participation: 0.5 },
						],
						total: 2,
					},
				},
			],
			[
				"merges the latest response with the accumulator",
				{
					xVal: 42,
					response: {
						leaders: [
							{ id: "node-a", score: 1.0, values: [], nickname: "nn1", participation: 1 },
							{ id: "node-b", score: 0.5, values: [], nickname: "nn2", participation: 0.5 },
						],
						total: 2,
					},
					accumulator: {
						leaders: [
							{ id: "node-a", score: 0.9, values: [{ x: 41, y: 0.9 }], nickname: "nn1", participation: 0.9 },
							{ id: "node-c", score: 0.8, values: [{ x: 41, y: 0.8 }], nickname: "nn3", participation: 0.8 },
						],
						total: 2,
					},
					wantOut: {
						leaders: [
							{
								id: "node-a",
								score: 1.0,
								values: [
									{ x: 41, y: 0.9 },
									{ x: 42, y: 1.0 },
								],
								nickname: "nn1",
								participation: 0.9,
							},
							{ id: "node-b", score: 0.5, values: [{ x: 42, y: 0.5 }], nickname: "nn2", participation: 0.5 },
						],
						total: 2,
					},
				},
			],
		])("%s", (_: string, tc: TestConfig) => {
			const gotOut = mergeLeaderboardData(tc.xVal, tc.response, tc.accumulator)
			expect(gotOut).toEqual(tc.wantOut)
		})
	})
})
