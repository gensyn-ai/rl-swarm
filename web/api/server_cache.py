import hashlib
import itertools
from datetime import datetime

from hivemind_exp.dht_utils import *
from . import gossip_utils
from hivemind_exp.name_utils import get_name_from_peer_id
from .gossip_utils import stage1_message, stage2_message, stage3_message


class Cache:
    def __init__(self, dht, manager, logger):
        self.dht = dht
        self.manager = manager
        self.logger = logger

        self.lock = manager.Lock()
        self.reset()

    def reset(self):
        self.leaderboard = self.manager.dict()
        self.rewards_history = self.manager.dict()
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
            self.logger.info(">>> all_entries length: %d", len(all_entries))

            current_history = []
            with self.lock:
                for entry in all_entries:
                    latestScore = entry["score"]
                    id = entry["id"]
                    nn = entry["nickname"]

                    past_scores = self.rewards_history.get(id, [])
                    next_scores = past_scores + [{"x": int(datetime.now().timestamp()), "y": latestScore}][-100:]
                    self.logger.info(">>> id: %s, past_scores length: %d, next_scores length: %d", id, len(past_scores), len(next_scores))
                    self.rewards_history[id] = next_scores
                    current_history.append({
                        "id": id,
                        "nickname": nn,
                        "values": next_scores,
                    })

            with self.lock:
                self.leaderboard = {
                    "leaders": all_entries,
                    "total": len(raw) if raw else 0,
                    "rewardsHistory": current_history,
                }
        except Exception as e:
            self.logger.warning("could not get leaderboard data: %s", e)

    def _get_gossip(self):
        STAGE_GOSSIP_LIMIT = 20  # Most recent.
        STAGE_MESSAGE_FNS = [
            stage1_message, stage2_message, stage3_message
        ]

        round_gossip = []
        start_time = datetime.now()
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
                # Check if we've exceeded 10 seconds
                # Adding this as a stop gap to make sure the gossip collection doesn't stop other data from being polled.
                if (datetime.now() - start_time).total_seconds() > 10:
                    self.logger.warning(">>> gossip collection timed out after 10s")
                    break

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
        finally:
            elapsed = (datetime.now() - start_time).total_seconds()
            self.logger.info(">>> completed gossip with %d messages in %.2fs", len(round_gossip), elapsed)

        with self.lock:
            self.gossips = {
                "messages": [msg for _, msg in sorted(round_gossip, reverse=True)]
                or [],
            }
