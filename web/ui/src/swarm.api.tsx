export type LeaderboardResponse = {
    leaders: {
        id: string,
        values: { x: number, y : number }[], // Not using this right now.
        score: number,
    }[],
}

type GossipRequest = {
    since: number,
}

export type GossipResponse = {
    messages: {
        id: string,
        message: string,
        node: string,
    }[],
    currentRound: number,
    currentStage: number,
}

export async function getLeaderboard(): Promise<LeaderboardResponse> {
    try {
        const res = await fetch('/api/leaderboard')
        const json = await res.json()

        if (res.status > 499) {
            console.error('5xx error fetching leaderboard details')
            throw new Error('could not get leaderboard: internal server error')
        }

        // Clear the `values` from the api response since we aren't using it.
        // The UI is accumulating the response scores into the values in the swarm component.
        const lbres = json as LeaderboardResponse
        lbres.leaders?.forEach((leader) => {
            leader.score = parseFloat(leader.score.toFixed(2))
            if (leader.id.toLowerCase() === "gensyn") {
                leader.id = "INITIAL PEER"
            }
            leader.values = []
        })

        return json
    } catch (e) {
        console.error('error fetching leaderboard details', e)
        if (e instanceof Error) {
            throw new Error(`could not get leaderboard: ${e.message}`)
        } else {
            throw new Error('could not get leaderboard')
        }
    }
}

export async function getGossip(req: GossipRequest): Promise<GossipResponse> {
    try {
        const res = await fetch(`/api/gossip?since_round=${req.since}`)
        const json = await res.json()

        if (res.status > 499) {
            console.error('5xx error fetching gossip')
            throw new Error('could not get gossip: internal server error')
        }

        const gres = json as GossipResponse
        gres.messages.forEach((message) => {
            if (message.node.toLocaleLowerCase() === "gensyn") {
                message.node = "INITIAL PEER"
            }
        })
        return json
    } catch (e) {
        console.error('error fetching gossip details', e)
        if (e instanceof Error) {
            throw new Error(`could not get gossip: ${e.message}`)
        } else {
            throw new Error('could not get gossip')
        }
    }
}