import { render, waitFor } from '@solidjs/testing-library'
import Swarm, { mergeLeaderboardData } from './Swarm'
import { vi, afterEach, beforeEach, describe, expect, it } from 'vitest'
import * as swarmApi from './swarm.api'

vi.mock('./swarm.api', () => ({
    getGossip: vi.fn(),
    getLeaderboard: vi.fn(),
}))

describe('mergeLeaderboardData', () => {
    type TestConfig = {
        xVal: number;
        response?: swarmApi.LeaderboardResponse;
        accumulator?: swarmApi.LeaderboardResponse;
        wantOut: swarmApi.LeaderboardResponse;
    };

    it.each([
        [
            'returns the accumulator if no response',
            {
                xVal: 42,
                response: undefined,
                accumulator: {
                    leaders: []
                },
                wantOut: {
                    leaders: []
                },
            },
        ],
        [
            'returns the response with new values if no accumulator',
            {
                xVal: 42,
                response: {
                    leaders: [
                        { id: 'node-a', score: 1.0, values: [] },
                        { id: 'node-b', score: 0.5, values: [] },
                    ],
                },
                accumulator: undefined,
                wantOut: {
                    leaders: [
                        { id: 'node-a', score: 1.0, values: [{ x: 42, y: 1.0 }] },
                        { id: 'node-b', score: 0.5, values: [{ x: 42, y: 0.5 }] },
                    ],
                },
            },
        ],
        [
            'merges the latest response with the accumulator',
            {
                xVal: 42,
                response: {
                    leaders: [
                        { id: 'node-a', score: 1.0, values: [] },
                        { id: 'node-b', score: 0.5, values: [] },
                    ]
                },
                accumulator: {
                    leaders: [
                        { id: 'node-a', score: 0.9, values: [{ x: 41, y: 0.9 }] },
                        { id: 'node-c', score: 0.8, values: [{ x: 41, y: 0.8 }]},
                    ]
                },
                wantOut: {
                    leaders: [
                        { id: 'node-a', score: 1.0, values: [{ x: 41, y: 0.9}, { x: 42, y: 1.0 }] },
                        {id: 'node-b', score: 0.5, values: [{ x: 42, y: 0.5 }] },
                    ],
                },
            },
        ],
    ])('%s', (_: string, tc: TestConfig) => {
        const gotOut = mergeLeaderboardData(tc.xVal, tc.response, tc.accumulator);
        expect(gotOut).toEqual(tc.wantOut)
    });
});

describe('Swarm', () => {
    beforeEach(() => {
        vi.useFakeTimers()
        vi.resetAllMocks()
        vi.clearAllMocks()
    })

    afterEach(() => {
        vi.useRealTimers()
    })

    it('should merge leaderboard messages', async () => {
        const getLeaderboardSpy = vi.spyOn(swarmApi, 'getLeaderboard')
        const getGossipSpy = vi.spyOn(swarmApi, 'getGossip')

        getGossipSpy.mockResolvedValue({ currentRound: -1, currentStage: -1, messages: [] })
        getLeaderboardSpy.mockResolvedValueOnce({
            leaders: [
                { id: 'nodea', values: [{ x: 0, y: 1}], score: 1 },
                { id: 'nodeb', values: [{ x: 0, y: 1}], score: 1 },
            ]
        }).mockResolvedValueOnce({
            leaders: [
                { id: 'nodec', values: [{ x: 0, y: 2}], score: 3 },
                { id: 'nodea', values: [{ x: 0, y: 2}], score: 2 },
                { id: 'nodeb', values: [{ x: 0, y: 2}], score: 2 },
            ]
        })

        const result = render(() => <Swarm />)

        expect(getLeaderboardSpy).toHaveBeenCalledTimes(1)

        // Helper function to account for the &nbsp; in the text content
        const normalizedText = (n: HTMLElement) => n ? n.textContent?.replace(/\u00A0/g, ' ').trim() : ""

        let first = await result.findByTestId('leader-0')
        expect(normalizedText(first)).toEqual('[0] nodea [1]')

        let second = await result.findByTestId('leader-1')
        expect(normalizedText(second)).toEqual('[1] nodeb [1]')

        vi.advanceTimersByTime(10_000)
        expect(getLeaderboardSpy).toHaveBeenCalledTimes(2)
    })

    it('should render gossip messages', async () => {
        const firstRes = {
            currentRound: 1,
            currentStage: 1,
            messages: [
                { id: 'nodea_1_1', message: 'foo1', node: 'nodea' },
                { id: 'nodeb_1_1', message: 'bar1', node: 'nodeb' },
            ],
        }
        const secondRes = {
            currentRound: 1,
            currentStage: 1,
            messages: [
                { id: 'nodea_1_1', message: 'foo1', node: 'nodea' },
                { id: 'nodea_1_2', message: 'foo2', node: 'nodea' },
                { id: 'nodeb_1_1', message: 'bar1', node: 'nodeb' },
                { id: 'nodeb_1_2', message: 'bar2', node: 'nodeb' },
            ],
        }

        const getLeaderboardSpy = vi.spyOn(swarmApi, 'getLeaderboard')
        const getGossipSpy = vi.spyOn(swarmApi, 'getGossip')

        getGossipSpy.mockResolvedValueOnce(firstRes).mockResolvedValueOnce(secondRes)
        getLeaderboardSpy.mockResolvedValue({ leaders: [{ id: 'not-used', values: [{x: 0, y:0}], score: 0 }] })

        const result = render(() => <Swarm />)

        // On mount we expect the APIs to have resolved.
        expect(getGossipSpy).toHaveBeenCalledTimes(1)
        expect(getGossipSpy).toHaveBeenCalledWith({ since: 0 })

        await waitFor(() => {
            expect(result.queryAllByText('foo1')).toHaveLength(1)
            expect(result.queryAllByText('bar1')).toHaveLength(1)
        })

        expect(getGossipSpy).toHaveBeenCalledTimes(2)
        expect(getGossipSpy).toHaveBeenCalledWith({ since: 1 })
        
        // Results are de-duplicated.
        await waitFor(() => {
            expect(result.queryAllByText('foo1')).toHaveLength(1)
            expect(result.queryAllByText('foo2')).toHaveLength(1)
            expect(result.queryAllByText('bar1')).toHaveLength(1)
            expect(result.queryAllByText('bar2')).toHaveLength(1)
        })

        expect(getLeaderboardSpy).toHaveBeenCalledTimes(1)
    })
})