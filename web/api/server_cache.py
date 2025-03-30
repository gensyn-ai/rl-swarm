import hashlib
import itertools
from datetime import datetime

from hivemind_exp.dht_utils import *
from . import gossip_utils
from hivemind_exp.name_utils import get_name_from_peer_id


class Cache:
    def __init__(self, dht, manager, logger):
        self.dht = dht
        self.manager = manager
        self.logger = logger

        self.lock = manager.Lock()
        self.reset()

    def reset(self):
        self.leaderboard = self.manager.dict()
        self.gossips = self.manager.dict()

        self.current_round = self.manager.Value("i", -1)
        self.current_stage = self.manager.Value("i", -1)

        self.last_polled = None

    def get_round_and_stage(self):
        return self.current_round.value, self.current_stage.value

    def get_leaderboard(self):
        return dict(self.leaderboard)

    def get_gossips(self, since_round = 0):
        return dict(self.gossips)

    def get_last_polled(self):
        return self.last_polled

    def poll_dht(self):
        try:
            self._get_round_and_stage()
            self._get_leaderboard()
            self._get_gossip()

            with self.lock:
                self.last_polled = datetime.now()
        except Exception as e:
            self.logger.error("cache failed to poll dht: %s", e)

    def _get_dht_value(self, **kwargs):
        return get_dht_value(self.dht, beam_size=100, **kwargs)

    def _get_round_and_stage(self):
        try:
            r, s = get_round_and_stage(self.dht)
            self.logger.info(f"cache polled round and stage: r={r}, s={s}")
            with self.lock:
                self.current_round.value = r
                self.current_stage.value = s
        except ValueError as e:
            self.logger.warning(
                "could not get current round or stage; default to -1: %s", e
            )

    def _get_leaderboard(self):
        try:
            raw = self._get_dht_value(
                key=leaderboard_key(self.current_round.value, self.current_stage.value),
                latest=True,
            )

            # Create entries for all participants
            all_entries = [
                {
                    "id": str(t[0]),
					"nickname": get_name_from_peer_id(t[0]),
                    "score": t[1],
                    "values": [],
                }
                for t in (raw or [])
            ]

            with self.lock:
                self.leaderboard = {
                    "leaders": all_entries,
                    "total": len(raw) if raw else 0,
                }
        except Exception as e:
            self.logger.warning("could not get leaderboard data: %s", e)

    def _get_gossip(self):
        STAGE_GOSSIP_LIMIT = 20  # Most recent.
        STAGE_MESSAGE_FNS = [
            stage1_message, stage2_message, stage3_message
        ]

        round_gossip = []
        try:
            # Basically a proxy for the reachable peer group.
            curr_rewards: dict[str, Any] | None = self._get_dht_value(
                key=rewards_key(self.current_round.value, self.current_stage.value)
            )
            if not curr_rewards:
                raise ValueError("missing curr_rewards")

            nodes = curr_rewards.keys()
            curr_round = self.current_round.value
            curr_stage = self.current_stage.value
            start_round = (
                0 if curr_round < 20 else curr_round - 20
            )

            for round_num, stage, node_key in itertools.product(
                range(start_round, curr_round + 1),
                range(0, 3),
                nodes,
            ):
                if round_num > curr_round or (round_num == curr_round and stage > curr_stage):
                    break

                key = outputs_key(node_key, round_num, stage)
                if outputs := self._get_dht_value(key=key):
                    sorted_outputs = sorted(
                        list(outputs.items()), key=lambda t: t[1][0]
                    )
                    for question, (ts, outputs) in sorted_outputs[-STAGE_GOSSIP_LIMIT:]:
                        gossip_id = hashlib.md5(
                            f"{node_key}_{round_num}_{stage}_{question}".encode()
                        ).hexdigest()
                        if stage < len(STAGE_MESSAGE_FNS):
                            message = STAGE_MESSAGE_FNS[stage](node_key, question, ts, outputs)
                        else:
                            message = (
                                f"Cannot render output for unknown stage {stage}"
                            )
                        round_gossip.append(
                            (
                                ts,
                                {
                                    "id": gossip_id,
                                    "message": message,
                                    "node": node_key,
                                },
                            )
                        )
        except Exception as e:
            self.logger.warning("could not get gossip: %s", e)

        with self.lock:
            self.gossips = {
                "messages": [msg for _, msg in sorted(round_gossip, reverse=True)]
                or [],
            }
