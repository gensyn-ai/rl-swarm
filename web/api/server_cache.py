import hashlib
import itertools
from hivemind_exp.dht_utils import *
import sys
import time


class Cache:
    def __init__(self, dht, manager):
        self.dht = dht
        self.manager = manager

        self.lock = manager.Lock()

        self.leaderboard = manager.dict()
        self.gossips = manager.dict()

        self.current_round = manager.Value("i", -1)
        self.current_stage = manager.Value("i", -1)

        self.last_polled = manager.Value("d", -1.0)

    def get_leaderboard(self):
        return dict(self.leaderboard)

    def get_gossips(self):
        return dict(self.gossips)

    def get_last_polled(self):
        return self.get_last_polled

    def poll_dht(self):
        try:
            self._get_round_and_stage()
            self._get_leaderboard()
            self._get_gossip()
        except Exception as e:
            print(f"failed polling dht", e, file=sys.stderr)

        with self.lock:
            self.last_polled = time.time()

    def _get_round_and_stage(self):
        try:
            r, s = get_round_and_stage(self.dht)
            print(f"got round/stage {r}/{s}")
            with self.lock:
                self.current_round = r
                self.current_stage = s
        except ValueError as e:
            print(
                "could not get current round or stage; default to -1",
                e,
                file=sys.stderr,
            )

    def _get_leaderboard(self):
        try:
            raw = get_dht_value(
                self.dht,
                key=leaderboard_key(self.current_round, self.current_stage),
                latest=True,
            )
            out = [
                {
                    "id": str(t[0]),
                    "score": t[1],
                    "values": [],
                }
                for t in (raw or [])
            ]

            with self.lock:
                self.leaderboard = {"leaders": out}
        except Exception as e:
            print("could not get leaderboard data", e, file=sys.stderr)

    def _get_gossip(self):
        STAGE_GOSSIP_LIMIT = 20  # Most recent.
        round_gossip = []
        try:
            # Basically a proxy for the reachable peer group.
            curr_rewards: dict[str, Any] | None = get_dht_value(
                self.dht,
                key=rewards_key(self.current_round, self.current_stage),
                latest=True,
            )
            if not curr_rewards:
                raise ValueError("missing curr_rewards")

            nodes = curr_rewards.keys()
            start_round = 0 if self.current_round < 20 else self.current_round - 20

            for round_num, stage, node_uuid in itertools.product(
                range(start_round, self.current_round + 1),
                range(0, self.current_stage + 1),
                nodes,
            ):
                key = outputs_key(node_uuid, round_num, stage)
                if outputs := get_dht_value(self.dht, key=key, latest=False):
                    sorted_outputs = sorted(
                        list(outputs.items()), key=lambda t: t[1][0]
                    )
                    for question, (ts, outputs) in sorted_outputs[-STAGE_GOSSIP_LIMIT:]:
                        id = hashlib.md5(
                            f"{node_uuid}_{round_num}_{stage}_{question}".encode()
                        ).hexdigest()
                        round_gossip.append(
                            (
                                ts,
                                {
                                    "id": id,
                                    "message": f"{question}...Answer: {outputs['answer']}",
                                    "node": node_uuid,
                                },
                            )
                        )
        except Exception as e:
            print(e, "default current_round to -1", file=sys.stderr)

        with self.lock:
            self.gossips = {
                "messages": [msg for _, msg in sorted(round_gossip, reverse=True)]
                or [],
                "currentRound": self.current_round,
                "currentStage": self.current_stage,
            }
