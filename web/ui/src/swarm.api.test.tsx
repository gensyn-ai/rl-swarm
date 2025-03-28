import { describe, it, expect, vi, beforeEach } from "vitest"
import api from "./swarm.api"

// Need to hoist this since vi.mock is itself hoisted.
const mockClient = vi.hoisted(() => ({
	readContract: vi.fn(),
}))

vi.mock("viem", () => ({
	createPublicClient: vi.fn().mockReturnValue(mockClient),
	http: vi.fn(),
}))

describe("getRewards", () => {
	beforeEach(() => {
		vi.clearAllMocks()
	})

	it("should fetch all leaders", async () => {
		vi.stubGlobal(
			"fetch",
			vi.fn(() =>
				Promise.resolve({
					ok: true,
					status: 200,
					json: () =>
						Promise.resolve({
							leaders: new Array(20).fill(undefined).map((_, i) => ({
								id: `node-${i}`,
								score: 20 - i,
								values: [{ x: 0, y: 20 - i }],
							})),
							total: 20,
						}),
				}),
			),
		)

		const result = await api.getRewards()
		expect(result.leaders).toHaveLength(20)

		vi.stubGlobal(
			"fetch",
			vi.fn(() =>
				Promise.resolve({
					ok: true,
					status: 200,
					json: () =>
						Promise.resolve({
							leaders: new Array(5).fill(undefined).map((_, i) => ({
								id: `node-${i}`,
								score: 20 - i,
								values: [{ x: 0, y: 20 - i }],
							})),
							total: 5,
						}),
				}),
			),
		)

		const resultShort = await api.getRewards()
		expect(resultShort.leaders).toHaveLength(5)
	})

	it("should handle fetch errors", async () => {
		vi.stubGlobal(
			"fetch",
			vi.fn(() =>
				Promise.resolve({
					ok: false,
					status: 500,
					statusText: "Internal Server Error",
				}),
			),
		)

		await expect(api.getRewards()).rejects.toThrow("could not get rewards: Failed to fetch rewards: Internal Server Error")
	})
})

describe("getRoundAndStage", () => {
	beforeEach(() => {
		vi.clearAllMocks()
	})

	it("should fetch round and stage", async () => {
		// Mock each readContract call separately
		vi.mocked(mockClient.readContract)
			.mockResolvedValueOnce(1n) // First call returns round
			.mockResolvedValueOnce(2n) // Second call returns stage

		const result = await api.getRoundAndStage()
		expect(result).toEqual({
			round: 1,
			stage: 2,
		})
	})

	it("should handle contract read errors", async () => {
		vi.mocked(mockClient.readContract).mockRejectedValue(new Error("Contract read failed"))

		await expect(api.getRoundAndStage()).rejects.toThrow("could not get round and stage")
	})
})

describe("getGossip", () => {
	beforeEach(() => {
		vi.clearAllMocks()
	})

	it("should fetch gossip messages", async () => {
		vi.stubGlobal(
			"fetch",
			vi.fn(() =>
				Promise.resolve({
					ok: true,
					status: 200,
					json: () =>
						Promise.resolve({
							messages: [
								{ id: "msg1", message: "test message", node: "node1" },
								{ id: "msg2", message: "another message", node: "node2" },
							],
						}),
				}),
			),
		)

		const result = await api.getGossip({ since: 1 })
		expect(result.messages).toHaveLength(2)
		expect(result.messages[0].message).toBe("test message")
	})

	it("should handle 5xx errors", async () => {
		vi.stubGlobal(
			"fetch",
			vi.fn(() =>
				Promise.resolve({
					ok: true,
					status: 500,
					json: () => Promise.resolve({ messages: [] }),
				}),
			),
		)

		await expect(api.getGossip({ since: 1 })).rejects.toThrow("could not get gossip: internal server error")
	})

	it("should handle fetch errors", async () => {
		vi.stubGlobal(
			"fetch",
			vi.fn(() =>
				Promise.resolve({
					ok: false,
					status: 400,
					statusText: "Bad Request",
				}),
			),
		)

		await expect(api.getGossip({ since: 1 })).rejects.toThrow("could not get gossip: failed to fetch gossip: Bad Request")
	})

	it("should handle invalid response data", async () => {
		vi.stubGlobal(
			"fetch",
			vi.fn(() =>
				Promise.resolve({
					ok: true,
					status: 200,
					json: () =>
						Promise.resolve({
							invalid: "data",
						}),
				}),
			),
		)

		const result = await api.getGossip({ since: 1 })
		expect(result.messages).toEqual([])
	})

	it("should transform 'gensyn' node to 'INITIAL PEER'", async () => {
		vi.stubGlobal(
			"fetch",
			vi.fn(() =>
				Promise.resolve({
					ok: true,
					status: 200,
					json: () =>
						Promise.resolve({
							messages: [
								{ id: "msg1", message: "test message", node: "gensyn" },
								{ id: "msg2", message: "another message", node: "Gensyn" },
							],
						}),
				}),
			),
		)

		const result = await api.getGossip({ since: 1 })
		expect(result.messages[0].node).toBe("INITIAL PEER")
		expect(result.messages[1].node).toBe("INITIAL PEER")
	})
})
