import { render, waitFor, fireEvent } from "@solidjs/testing-library"
import Swarm from "./Swarm"
import { SwarmProvider } from "./SwarmContext"
import { vi, afterEach, beforeEach, describe, expect, it } from "vitest"
import api from "./swarm.api"

vi.mock("./swarm.api", () => ({
	default: {
		getGossip: vi.fn(),
		getLeaderboard: vi.fn(),
		getRoundAndStage: vi.fn(),
	},
}))

describe("Swarm", () => {
	beforeEach(() => {
		vi.useFakeTimers()
		vi.resetAllMocks()
		vi.clearAllMocks()
	})

	afterEach(() => {
		vi.useRealTimers()
	})

	it("should render gossip messages", async () => {
		const firstRes = {
			messages: [
				{ id: "nodea_1_1", message: "foo1", node: "nodea" },
				{ id: "nodeb_1_1", message: "bar1", node: "nodeb" },
			],
		}
		const secondRes = {
			messages: [
				{ id: "nodea_1_1", message: "foo1", node: "nodea" },
				{ id: "nodea_1_2", message: "foo2", node: "nodea" },
				{ id: "nodeb_1_1", message: "bar1", node: "nodeb" },
				{ id: "nodeb_1_2", message: "bar2", node: "nodeb" },
			],
		}

		const getLeaderboardSpy = vi.spyOn(api, "getLeaderboard")
		const getGossipSpy = vi.spyOn(api, "getGossip")

		getGossipSpy.mockResolvedValueOnce(firstRes).mockResolvedValueOnce(secondRes)
		getLeaderboardSpy.mockResolvedValue({
			leaders: [{ id: "not-used", values: [{ x: 0, y: 0 }], score: 0, nickname: "nn", participation: 0 }],
			total: 1,
		})

		const result = render(() => (
			<SwarmProvider>
				<Swarm />
			</SwarmProvider>
		))

		await vi.advanceTimersByTimeAsync(0)

		// On mount we expect the APIs to have resolved.
		expect(getGossipSpy).toHaveBeenCalledTimes(1)

		await waitFor(() => {
			expect(result.queryAllByText("foo1")).toHaveLength(1)
			expect(result.queryAllByText("bar1")).toHaveLength(1)
		})

		vi.advanceTimersByTime(10_000)

		expect(getGossipSpy).toHaveBeenCalledTimes(2)

		// Results are de-duplicated.
		await waitFor(() => {
			expect(result.queryAllByText("foo1")).toHaveLength(1)
			expect(result.queryAllByText("foo2")).toHaveLength(1)
			expect(result.queryAllByText("bar1")).toHaveLength(1)
			expect(result.queryAllByText("bar2")).toHaveLength(1)
		})
	})

	it("should show modal when no leaders are present", async () => {
		const getLeaderboardSpy = vi.spyOn(api, "getLeaderboard")
		const getGossipSpy = vi.spyOn(api, "getGossip")
		const getRoundAndStageSpy = vi.spyOn(api, "getRoundAndStage")

		// Mock all API calls to resolve immediately
		getGossipSpy.mockResolvedValue({ messages: [] })
		getLeaderboardSpy.mockResolvedValue({ leaders: [], total: 0 })
		getRoundAndStageSpy.mockResolvedValue({ round: 1, stage: 1 })

		const result = render(() => (
			<SwarmProvider>
				<Swarm />
			</SwarmProvider>
		))

		// On mount we expect the APIs to have resolved
		expect(getLeaderboardSpy).toHaveBeenCalledTimes(1)
		expect(getGossipSpy).toHaveBeenCalledTimes(1)
		expect(getRoundAndStageSpy).toHaveBeenCalledTimes(1)

		// Wait for the modal to appear
		await waitFor(() => {
			const modal = result.getByTestId("swarm-modal")
			expect(modal).toBeTruthy()
		})
	})

	it("should handle search functionality", async () => {
		const getLeaderboardSpy = vi.spyOn(api, "getLeaderboard")
		const getGossipSpy = vi.spyOn(api, "getGossip")
		const getRoundAndStageSpy = vi.spyOn(api, "getRoundAndStage")

		getGossipSpy.mockResolvedValue({ messages: [] })
		getLeaderboardSpy.mockResolvedValue({
			leaders: [
				{ id: "node1", values: [{ x: 0, y: 2 }], score: 2, nickname: "nn1", participation: 2 },
				{ id: "node2", values: [{ x: 0, y: 1 }], score: 1, nickname: "nn2", participation: 1 },
			],
			total: 2,
		})
		getRoundAndStageSpy.mockResolvedValue({ round: 1, stage: 1 })

		const result = render(() => (
			<SwarmProvider>
				<Swarm />
			</SwarmProvider>
		))

		expect(getLeaderboardSpy).toHaveBeenCalledTimes(1)
		expect(getGossipSpy).toHaveBeenCalledTimes(1)
		expect(getRoundAndStageSpy).toHaveBeenCalledTimes(1)

		// Wait for the modal to disappear since leaders array is not empty
		await waitFor(() => {
			const modal = result.queryByTestId("swarm-modal")
			expect(modal).toBeNull()
		})

		const searchInput = result.getByPlaceholderText("ENTER YOUR NODE ADDRESS")
		fireEvent.input(searchInput, { target: { value: "node1" } })
		fireEvent.click(result.getByText("Search"))

		const normalizedText = (n: HTMLElement) => (n ? n.textContent?.replace(/\u00A0/g, " ").trim() : "")
		await waitFor(() => {
			const searchResults = result.getByTestId("leaderboard-search-results")
			expect(normalizedText(searchResults)).toContain("[0] node1 [2]")
		})
	})

	it("should display round and stage information", async () => {
		const getLeaderboardSpy = vi.spyOn(api, "getLeaderboard")
		const getGossipSpy = vi.spyOn(api, "getGossip")
		const getRoundAndStageSpy = vi.spyOn(api, "getRoundAndStage")

		getGossipSpy.mockResolvedValue({ messages: [] })
		getLeaderboardSpy.mockResolvedValue({
			leaders: [{ id: "node1", values: [{ x: 0, y: 1 }], score: 1, nickname: "nn1", participation: 1 }],
			total: 1,
		})
		getRoundAndStageSpy.mockResolvedValue({ round: 5, stage: 3 })

		const result = render(() => (
			<SwarmProvider>
				<Swarm />
			</SwarmProvider>
		))

		await waitFor(() => {
			const header = result.getByText("leaderboard : Round 5, stage 3")
			expect(header).toBeTruthy()
		})
	})

	it("should handle gossip message updates", async () => {
		const getLeaderboardSpy = vi.spyOn(api, "getLeaderboard")
		const getGossipSpy = vi.spyOn(api, "getGossip")
		const getRoundAndStageSpy = vi.spyOn(api, "getRoundAndStage")

		getLeaderboardSpy.mockResolvedValue({
			leaders: [{ id: "node1", values: [{ x: 0, y: 1 }], score: 1, nickname: "nn1", participation: 1 }],
			total: 1,
		})
		getRoundAndStageSpy.mockResolvedValue({ round: 1, stage: 1 })

		// Initial messages
		getGossipSpy.mockResolvedValueOnce({
			messages: [{ id: "msg1", message: "Initial message", node: "node1" }],
		})

		// Updated messages
		getGossipSpy.mockResolvedValueOnce({
			messages: [
				{ id: "msg1", message: "Initial message", node: "node1" },
				{ id: "msg2", message: "New message", node: "node2" },
			],
		})

		const result = render(() => (
			<SwarmProvider>
				<Swarm />
			</SwarmProvider>
		))

		await waitFor(() => {
			const initialMessage = result.getByText("Initial message")
			expect(initialMessage).toBeTruthy()
		})

		vi.advanceTimersByTime(10_000)

		await waitFor(() => {
			const newMessage = result.getByText("New message")
			expect(newMessage).toBeTruthy()
		})
	})
})
