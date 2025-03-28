import { z } from "zod"
import { createPublicClient, http } from "viem"
import { Chain } from "viem"

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

const leaderboardResponseSchema = z.object({
	leaders: z.array(
		z.object({
			id: z.string(),
			values: z.array(z.object({ x: z.number(), y: z.number() })),
			score: z.number(),
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
					outputs: [
						{ type: "address[]" },
						{ type: "uint256[]" }
					],
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

	/**
	 * Get the peer IDs for a list of EOAs.
	 * 
	 * @param eoas - The list of EOAs to get the peer IDs for.
	 * @returns The peer IDs for the EOAs.
	 */
	public async getPeerIds(eoas: readonly `0x${string}`[]): Promise<readonly string[]> {
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

		return peerIds
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
}

type SwarmApiConfig = {
	providerUrl: string
	contractAddress: string
	environment: "local" | "testnet" | "mainnet"
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

	public async getLeaderboard(): Promise<LeaderboardResponse> {
		try {
			const voterLeaderboard = await this.swarmContract.getLeaderboard()
			const peerIds = await this.swarmContract.getPeerIds(voterLeaderboard.leaders.map((leader) => leader.id as `0x${string}`))

			// TODO: Use the voterLeaderboard, peerIds, and DHT leaderboard data to create a new leaderboard.
			// TODO: Cache the peerIDs and only request them when they aren't in the cache.
			console.log(`>>> voterLeaderboard: ${JSON.stringify(voterLeaderboard)}`)
			console.log(`>>> peerIds: ${peerIds}`)

			const res = await fetch(`/api/leaderboard`)
			if (!res.ok) {
				throw new Error(`Failed to fetch leaderboard: ${res.statusText}`)
			}

			const json = await res.json()
			const result = leaderboardResponseSchema.parse(json)

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
}

const api = new SwarmApi({
	providerUrl: import.meta.env.VITE_PROVIDER_URL,
	contractAddress: import.meta.env.VITE_CONTRACT_ADDRESS,
	environment: import.meta.env.VITE_ENVIRONMENT,
})

export default api
