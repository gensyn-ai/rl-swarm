import { z } from "zod"
import { createPublicClient, http } from "viem"
import { Chain } from "viem"

// Reader warning:
// The types in this file are a mess and need to be refactored.

// sepoliaChain is used for testnet deployment.
const sepoliaChain: Chain = {
	id: 11155111,
	name: "Sepolia",
	nativeCurrency: {
		decimals: 18,
		name: "Sepolia Ether",
		symbol: "ETH",
	},
	rpcUrls: {
		default: { http: ["https://rpc.sepolia.org"] },
	},
	blockExplorers: {
		default: { name: "Etherscan", url: "https://sepolia.etherscan.io" },
	},
	testnet: true,
}

// anvilChain is used for local development.
const anvilChain: Chain = {
	id: 31337,
	name: "Anvil",
	nativeCurrency: {
		decimals: 18,
		name: "Ether",
		symbol: "ETH",
	},
	rpcUrls: {
		default: { http: ["http://127.0.0.1:8545"] },
	},
	blockExplorers: {
		default: { name: "", url: "" },
	},
	testnet: true,
}

const rewardsResponseSchema = z.object({
	leaders: z.array(
		z.object({
			id: z.string(),
			nickname: z.string(),
			values: z.array(z.object({ x: z.number(), y: z.number() })),
			score: z.number(), // Poor name but minimizing changes. This is the cumulative reward.
		}),
	),
	total: z.number(),
})
export type RewardsResponse = z.infer<typeof rewardsResponseSchema>

const leaderboardResponseSchema = z.object({
	leaders: z.array(
		z.object({
			id: z.string(),
			nickname: z.string(),
			values: z.array(z.object({ x: z.number(), y: z.number() })),
			score: z.number(), // Poor name but minimizing changes. This is the cumulative reward.
			participation: z.number(),
		}),
	),
	total: z.number(),
})

export type LeaderboardResponse = z.infer<typeof leaderboardResponseSchema>

type GossipRequest = {
	since: number
}

const gossipResponseSchema = z.object({
	messages: z.array(
		z.object({
			id: z.string(),
			message: z.string(),
			node: z.string(),
		}),
	),
})
export type GossipResponse = z.infer<typeof gossipResponseSchema>

export type RoundAndStageResponse = {
	round: number
	stage: number
}

export type VoterLeaderboardResponse = {
	leaders: Array<{
		id: string
		score: number
	}>
}

type Leader = LeaderboardResponse["leaders"][number]
type Reward = RewardsResponse["leaders"][number]

class SwarmContract {
	client: ReturnType<typeof createPublicClient>
	address: `0x${string}`

	constructor(providerUrl: string, address: string, environment: "local" | "testnet" | "mainnet") {
		let chain: Chain = anvilChain
		switch (environment) {
			case "testnet":
				chain = sepoliaChain
				break
		}

		this.client = createPublicClient({
			chain: chain,
			transport: http(providerUrl),
		})

		this.address = address as `0x${string}`
	}

	public async getLeaderboard(): Promise<VoterLeaderboardResponse> {
		const [voters, voteCounts] = await this.client.readContract({
			address: this.address,
			abi: [
				{
					inputs: [{ type: "uint256" }, { type: "uint256" }],
					name: "voterLeaderboard",
					outputs: [{ type: "address[]" }, { type: "uint256[]" }],
					stateMutability: "view",
					type: "function",
				},
			],
			functionName: "voterLeaderboard",
			args: [0n, 100n], // Smart contract only supports 100 leaders at a time.
		})

		return {
			leaders: voters.map((voter, index) => ({
				id: voter,
				score: Number(voteCounts[index]),
			})),
		}
	}

	public async getVoterCount(peerId: string): Promise<number> {
		const eoa = await this.getEoa(peerId)

		const count = await this.client.readContract({
			address: this.address,
			abi: [
				{
					inputs: [{ type: "address" }],
					name: "getVoterVoteCount",
					outputs: [{ type: "uint256" }],
					stateMutability: "view",
					type: "function",
				},
			],
			functionName: "getVoterVoteCount",
			args: [eoa],
		})

		return Number(count)
	}

	/**
	 * Get the peer IDs for a list of EOAs.
	 *
	 * @param eoas - The list of EOAs to get the peer IDs for.
	 * @returns The peer IDs for the EOAs.
	 */
	public async getPeerIds(eoas: readonly `0x${string}`[]): Promise<Record<`0x${string}`, string>> {
		const peerIds = await this.client.readContract({
			address: this.address,
			abi: [
				{
					inputs: [{ type: "address[]" }],
					name: "getPeerId",
					outputs: [{ type: "string[]" }],
					stateMutability: "view",
					type: "function",
				},
			],
			functionName: "getPeerId",
			args: [eoas],
		})

		const output: Record<`0x${string}`, string> = {}
		eoas.forEach((eoa, index) => {
			output[eoa] = peerIds[index]
		})

		return output
	}

	public async uniqueVoters(): Promise<number> {
		const count = await this.client.readContract({
			address: this.address,
			abi: [
				{
					inputs: [],
					name: "uniqueVoters",
					outputs: [{ type: "uint256" }],
					stateMutability: "view",
					type: "function",
				},
			],
			functionName: "uniqueVoters",
		})

		return Number(count)
	}

	public async getRoundAndStage(): Promise<RoundAndStageResponse> {
		const [round, stage] = await Promise.all([
			this.client.readContract({
				address: this.address,
				abi: [
					{
						inputs: [],
						name: "currentRound",
						outputs: [{ type: "uint256" }],
						stateMutability: "view",
						type: "function",
					},
				],
				functionName: "currentRound",
			}),
			this.client.readContract({
				address: this.address,
				abi: [
					{
						inputs: [],
						name: "currentStage",
						outputs: [{ type: "uint256" }],
						stateMutability: "view",
						type: "function",
					},
				],
				functionName: "currentStage",
			}),
		])

		return {
			round: Number(round),
			stage: Number(stage),
		}
	}

	public async getEoa(peerId: string): Promise<`0x${string}`> {
		// function getEoa(string[] calldata peerIds) external view returns (address[] memory)
		const eoa = await this.client.readContract({
			address: this.address,
			abi: [
				{
					inputs: [{ type: "string[]" }],
					name: "getEoa",
					outputs: [{ type: "address[]" }],
					stateMutability: "view",
					type: "function",
				},
			],
			functionName: "getEoa",
			args: [[peerId]],
		})

		return eoa[0]
	}
}

type SwarmApiConfig = {
	providerUrl: string
	contractAddress: string
	environment: "local" | "testnet" | "mainnet"
}

export type RewardsHistory = {
	leaders: Array<{
		id: string
		values: Array<{ x: number; y: number }>
	}>
}

interface ISwarmApi {
	getRoundAndStage(): Promise<RoundAndStageResponse>
	getLeaderboard(): Promise<LeaderboardResponse>
	getGossip(req: GossipRequest): Promise<GossipResponse>
}

class SwarmApi implements ISwarmApi {
	private swarmContract: SwarmContract

	constructor(options: SwarmApiConfig) {
		this.swarmContract = new SwarmContract(options.providerUrl, options.contractAddress, options.environment)
	}

	public async getRoundAndStage(): Promise<RoundAndStageResponse> {
		try {
			return await this.swarmContract.getRoundAndStage()
		} catch (e) {
			console.error("error fetching round and stage details", e)
			throw new Error("could not get round and stage")
		}
	}

	public async getUniqueVotersCount(): Promise<number> {
		try {
			return await this.swarmContract.uniqueVoters()
		} catch (e) {
			console.error("error fetching unique voters count", e)
			throw new Error("could not get unique voters count")
		}
	}

	public async getRewards(): Promise<RewardsResponse> {
		try {
			const res = await fetch(`/api/leaderboard`)
			if (!res.ok) {
				throw new Error(`Failed to fetch rewards: ${res.statusText}`)
			}

			const json = await res.json()
			const result = rewardsResponseSchema.parse(json)

			result.leaders.forEach((leader) => {
				leader.score = parseFloat(leader.score.toFixed(2))
				if (leader.id.toLowerCase() === "gensyn") {
					leader.id = "INITIAL PEER"
				}
				leader.values = []
			})

			return result
		} catch (e) {
			if (e instanceof z.ZodError) {
				console.warn("zod error fetching rewards details. returning empty rewards response.", e)
				return {
					leaders: [],
					total: 0,
				}
			} else if (e instanceof Error) {
				console.error("error fetching rewards details", e)
				throw new Error(`could not get rewards: ${e.message}`)
			} else {
				throw new Error("could not get rewards")
			}
		}
	}

	public async getRewardsHistory(): Promise<RewardsHistory> {
		const rewardsHistorySchema = z.object({
			leaders: z.array(z.object({
				id: z.string(),
				values: z.array(z.object({ x: z.number(), y: z.number() })),
			})),
		})

		try {
			const res = await fetch("/api/rewards-history")
			if (!res.ok) {
				throw new Error(`Failed to fetch rewards history: ${res.statusText}`)
			}

			const json = await res.json()
			const result = rewardsHistorySchema.parse(json)

			return result
		} catch (e) {
			if (e instanceof z.ZodError) {
				console.warn("zod error fetching rewards history. returning empty rewards history response.", e)
				return {
					leaders: [],
				}
			} else if (e instanceof Error) {
				console.error("error fetching rewards history", e)
				throw new Error(`could not get rewards history: ${e.message}`)
			} else {
				throw new Error("could not get rewards history")
			}
		}
	}

	public async getLeaderboard(): Promise<LeaderboardResponse> {
		try {
			// Leaderboard contains the information for the EOAs, which we can use to get the peer IDs.
			const voterLeaderboard = await this.swarmContract.getLeaderboard()
			const peerIdsByEoa = await this.swarmContract.getPeerIds(voterLeaderboard.leaders.map((leader) => leader.id as `0x${string}`))

			// With the eoa->id mapping, we now make an id->name mapping.
			const peerIdsToNames = await this.mapIdsToNames(Object.values(peerIdsByEoa))

			// TODO: Locally cache results so we don't 2x hit this API.
			const rewards = await this.getRewards()

			// Transform data just for lookup.
			// We want to map peer ID to cumulative reward.
			const dhtParticipantsById = new Map<string, Reward>()
			rewards.leaders.forEach((leader) => {
				dhtParticipantsById.set(leader.id, leader)
			})

			const data = voterLeaderboard.leaders.map((leader) => {
				const peerId = peerIdsByEoa[leader.id as `0x${string}`]
				const nickname = peerIdsToNames[peerId] || leader.id
				const cumulativeReward = Number(dhtParticipantsById.get(peerId)?.score.toFixed(2)) || 0

				const out: Leader = {
					id: leader.id, // EOA
					participation: leader.score, // Participation score
					values: [], // Unused here
					nickname: nickname,
					score: cumulativeReward,
				}

				return out
			})

			return {
				leaders: data,
				total: rewards.total,
			}
		} catch (e) {
			if (e instanceof z.ZodError) {
				console.warn("zod error fetching leaderboard details. returning empty leaderboard response.", e)
				return {
					leaders: [],
					total: 0,
				}
			} else if (e instanceof Error) {
				console.error("error fetching leaderboard details", e)
				throw new Error(`could not get leaderboard: ${e.message}`)
			} else {
				throw new Error("could not get leaderboard")
			}
		}
	}

	public async getPeerInfoFromName(name: string): Promise<Leader | null> {
		const nameToIdResponseSchema = z.object({
			id: z.string().nullable().optional(),
		})

		try {
			// 1) From the name, return the peer ID.
			const res = await fetch(`/api/name-to-id?name=${name}`)
			if (!res.ok) {
				throw new Error(`failed to fetch rewards from id: ${res.statusText}`)
			}

			const json = await res.json()
			const result = nameToIdResponseSchema.parse(json)

			if (!result.id) {
				console.warn(`Could not find peer with name ${name}`)
				return null
			}

			// 2) From the peer ID, get the EOA so we can get the vote count.
			const eoa = await this.swarmContract.getEoa(result.id)
			const voteCount = await this.swarmContract.getVoterCount(eoa)

			// 3) From the leaderboard, get the leader info and find the peer with the matching ID.
			const leaderboard = await this.getLeaderboard()
			const leader = leaderboard.leaders.find((leader) => leader.id === result.id)

			if (leader) {
				leader.participation = voteCount
			}

			// Ensure we return a valid Leader object
			if (!leader) {
				throw new Error("Could not find leader info")
			}

			return leader
		} catch (e) {
			if (e instanceof z.ZodError) {
				console.warn("zod error fetching peer info from name. returning empty leader response.", e)
				return null
			} else if (e instanceof Error) {
				console.error("error fetching peer info from name", e)
				throw new Error(`could not get peer info from name: ${e.message}`)
			} else {
				throw new Error("could not get peer info from name")
			}
		}
	}

	public async getGossip(req: GossipRequest): Promise<GossipResponse> {
		try {
			const res = await fetch(`/api/gossip?since_round=${req.since}`)

			if (!res.ok) {
				throw new Error(`failed to fetch gossip: ${res.statusText}`)
			}

			const json = await res.json()

			if (res.status > 499) {
				console.error("5xx error fetching gossip")
				throw new Error("could not get gossip: internal server error")
			}

			const gres = gossipResponseSchema.parse(json)

			gres.messages.forEach((message) => {
				if (message.node.toLowerCase() === "gensyn") {
					message.node = "INITIAL PEER"
				}
			})

			return gres
		} catch (e) {
			if (e instanceof z.ZodError) {
				console.warn("zod error fetching gossip details. returning empty gossip response.", e)
				return {
					messages: [],
				}
			} else if (e instanceof Error) {
				console.error("error fetching gossip details", e)
				throw new Error(`could not get gossip: ${e.message}`)
			} else {
				throw new Error("could not get gossip")
			}
		}
	}

	/**
	 * Maps a list of IDs to a list of names.
	 * @param ids - The list of IDs to map to names.
	 * @returns A record of IDs to names.
	 */
	private async mapIdsToNames(ids: string[]): Promise<Record<string, string>> {
		const idToNameResponseSchema = z.record(z.string())
		const response = await fetch("/api/id-to-name", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify(ids),
		})

		if (!response.ok) {
			throw new Error(`Failed to get names for IDs: ${response.statusText}`)
		}

		const json = await response.json()
		const result = idToNameResponseSchema.parse(json)
		return result
	}
}

const api = new SwarmApi({
	providerUrl: import.meta.env.VITE_PROVIDER_URL,
	contractAddress: import.meta.env.VITE_CONTRACT_ADDRESS,
	environment: import.meta.env.VITE_ENVIRONMENT,
})

export default api
