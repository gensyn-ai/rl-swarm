import logging
import time
from typing import Any

from hivemind.dht import DHT
from hivemind.utils import get_dht_time
from trl import GRPOConfig, GRPOTrainer

from hivemind_exp.utils import HivemindNode, StageData
from hivemind_exp.dht_utils import (
    ROUND_STAGE_NUMBER_KEY,
    get_dht_value,
    get_round_and_stage,
    leaderboard_key,
    node_outputs_key,
    rewards_key,
)

logger = logging.getLogger(__name__)


class HivemindGRPOTrainer:
    """
    Subclass of GRPOTrainer that implements multi-stage GRPO by publishing
    intermediate results to a connected Hivemind DHT.
    """

    class PublishingGRPOTrainer(GRPOTrainer):
        def __init__(
            self,
            node: HivemindNode,
            dht: DHT,
            tokenizer,
            **kwargs,
        ):
            self.node = node
            self.dht = dht
            self.stage_rewards = 0.0
            super().__init__(processing_class=tokenizer, **kwargs)

        def publish_leaderboard(self):
            r, s = self.node.round_num, self.node.stage_num
            curr_rewards: dict[str, Any] | None = get_dht_value(
                self.dht, key=rewards_key(r, s), latest=True
            )
            if curr_rewards:
                # Sorted list of (node_uuid, reward) pairs.
                leaderboard = list(
                    sorted(curr_rewards.items(), key=lambda t: (t[1], t[0]), reverse=True)
                )
                self.dht.store(
                    key=leaderboard_key(r, s),
                    value=leaderboard,
                    expiration_time=get_dht_time() + self.node.out_expiration,
                )
            else:
                logger.info(f"[{self.node.uuid}] Can't retrieve round {r} stage {s - 1} rewards")

        def compute_loss(self, model, inputs, *args, **kwargs):
            loss = super().compute_loss(model, inputs, *args, **kwargs)
            # Reward function must save node.outputs + node.rewards!
            # This is only here to publish to the DHT at the right time.
            question = self.node.outputs["question"]
            value = (time.time(), self.node.outputs)
            self.dht.store(
                key=node_outputs_key(self.node),
                subkey=question,
                value=value,
                expiration_time=get_dht_time() + self.node.out_expiration,
            )
            self.node.put_stage_outputs(
                self.node.round_num, self.node.stage_num, question, value
            )

            # Just the latest.
            self.stage_rewards += sum(self.node.rewards)
            self.dht.store(
                key=rewards_key(self.node.round_num, self.node.stage_num),
                subkey=self.node.uuid,
                value=self.stage_rewards,
                expiration_time=get_dht_time() + self.node.out_expiration,
            )
            if self.node.is_coordinator():
                self.publish_leaderboard()

            return loss

    def __init__(
        self,
        node: HivemindNode,
        dht: DHT,
        stage_data: StageData,
        config: GRPOConfig,
        model,
        tokenizer,
        **kwargs,
    ):
        # The single coordinator is responsible for incrementing round + stage numbers.
        # TODO(lou): Allow ability to choose different coordinators?
        self.node = node
        self.dht = dht

        self.stage_data = stage_data

        self.config = config
        self.model = model
        self.tokenizer = tokenizer
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

    def _log_tag(self):
        node_uuid = self.node.uuid
        if self.node.is_coordinator():
            return f"[C-{node_uuid}]"
        return f"[F-{node_uuid}]"

    def wait_for(self, result_fn=lambda: None, interval=10, timeout=30):
        start_time = time.monotonic()
        while time.monotonic() - start_time < timeout:
            result = result_fn()
            if result is None:
                time.sleep(interval)
            else:
                break

        return result

    def train_stages(self, round_num, start_stage, is_coordinator):
        # TODO: Needs checkpoint loading

        tag = self._log_tag()

        self.node.round_num = round_num
        for i, stage in enumerate(self.stage_data.stages[start_stage:]):
            stage_num = start_stage + i
            self.node.stage_num = stage_num

            if is_coordinator:
                self.dht.store(
                    key=ROUND_STAGE_NUMBER_KEY,
                    value=(self.node.round_num, stage_num),
                    expiration_time=get_dht_time() + self.node.out_expiration,
                )

            logger.info(f"{tag} Training round: {round_num} stage: {stage_num}")
            train_dataset, test_dataset = stage.datasets_fn(round_num, stage_num)
            kwargs = {
                "model": self.model,
                "args": self.config,
                "reward_funcs": stage.reward_funcs,
                "train_dataset": train_dataset,
                "eval_dataset": test_dataset,
            }
            trainer = HivemindGRPOTrainer.PublishingGRPOTrainer(
                self.node, self.dht, self.tokenizer, **kwargs
            )
            self.train_and_save(trainer, train_dataset)
            logger.info(f"{tag} Finished training round: {round_num} stage: {stage_num}")

        self.node.clear_stage_cache()

    def train_and_save(self, trainer, train_dataset):
        tag = self._log_tag()
        train_result = trainer.train()

        # Log and save metrics
        metrics = train_result.metrics
        metrics["train_samples"] = len(train_dataset)
        trainer.log_metrics("train", metrics)
        trainer.save_metrics("train", metrics)
        trainer.save_state()

        logger.info(f"{tag} Saving model")
        trainer.model.config.use_cache = True
        trainer.save_model(self.config.output_dir)
        logger.info(f"{tag} Model saved to {self.config.output_dir}")
        self.config.distributed_state.wait_for_everyone()  # wait for all processes to load

        self.tokenizer.save_pretrained(self.config.output_dir)
        logger.info(f"{tag} Tokenizer saved to {self.config.output_dir}")

        # Save everything else on main process
        if trainer.accelerator.is_main_process:
            trainer.create_model_card(
                {"tags": ["rl", "grpo", "tutorial", "philschmid"]}
            )

    def coordinator_train(self):
        tag = self._log_tag()

        round_num = 0
        start_time = time.monotonic()
        while (
            round_num < self.stage_data.max_rounds
            and time.monotonic() - start_time < self.stage_data.train_timeout
        ):
            logger.info(f"{tag} Starting new round: {round_num}")

            _ = self.dht.get_visible_maddrs(latest=True)
            self.train_stages(round_num, 0, is_coordinator=True)

            round_num += 1
            if round_num == self.stage_data.max_rounds:
                return

        logger.info(f"{self._log_tag()} Training timed out!")

    def follower_train(self, check_interval=1):
        tag = self._log_tag()

        done_rounds = set()
        start_time = time.monotonic()
        fetch_log_time, finish_log_time = start_time, start_time
        while time.monotonic() - start_time < self.stage_data.train_timeout:
            curr_time = time.monotonic()
            _ = self.dht.get_visible_maddrs(latest=True)

            # Retrieve current round and stage.
            try:
                round_num, stage = get_round_and_stage(self.dht)
            except:
                if curr_time - fetch_log_time > 5:
                    logger.info(f"{tag} Could not fetch round and stage. Skipping.")
                    fetch_log_time = curr_time

                time.sleep(check_interval)
                continue

            if round_num not in done_rounds:
                logger.info(
                    f"{tag} Joining round: {round_num} starting at stage: {stage}"
                )
                self.train_stages(round_num, stage, is_coordinator=False)
                done_rounds.add(round_num)
            else:
                if curr_time - finish_log_time > 5:
                    logger.info(f"{tag} Already finished round: {round_num}. Skipping.")
                    finish_log_time = curr_time

            if round_num == self.stage_data.max_rounds - 1:
                return

        logger.info(f"{self._log_tag()} Training timed out!")

    def train(self):
        try:
            if self.node.is_coordinator():
                self.coordinator_train()
            else:
                self.follower_train()

        except:
            import traceback

            traceback.print_exc()
