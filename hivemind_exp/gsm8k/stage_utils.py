from collections import defaultdict
import logging
import time
from hivemind_exp.dht_utils import (
    DHT,
    HivemindNode,
    get_dht_value,
    get_outputs,
    rewards_key,
)
import hivemind_exp.gsm8k.stage1_rewards as stage1_rewards
import hivemind_exp.gsm8k.stage2_rewards as stage2_rewards
import hivemind_exp.gsm8k.stage3_rewards as stage3_rewards
from hivemind_exp.gsm8k.generate_prompts import get_stage2_samples, get_stage3_samples
from hivemind_exp.gsm8k.stage_merger import (
    Any,
    merge_stage1_question,
    merge_stage2_question,
)
from hivemind_exp.utils import SingleStageData, StageData

logger = logging.getLogger(__name__)

def merged_prev_stage_datasets(
    dht: DHT,
    node: HivemindNode,
    r: int,
    s: int,
    merge_fn,
    samples_fn,
    wait_interval=1,
    wait_timeout=5,
):
    merged_qs = []

    # Retrieves and merges last stage samples locally and from DHT.
    def get_prev_rewards():
        return get_dht_value(dht, key=rewards_key(r, s - 1), latest=True, beam_size=1000)

    prev_rewards: dict[str, Any] | None = get_prev_rewards()
    start_time = time.monotonic()
    while not prev_rewards and time.monotonic() - start_time < wait_timeout:
        logger.info(
            f"[{node.uuid}] Can't retrieve round {r} stage {s - 1} rewards; trying again in {wait_interval}s "
        )
        time.sleep(wait_interval)
        prev_rewards = get_prev_rewards()

    # Add the current node's local samples first.
    prev_outputs: dict[str, list] = defaultdict(list)
    try:
        prev_node_outputs = get_outputs(
            dht, node.uuid, r, s - 1, node.get_stage_outputs
        )
        for _, outputs in prev_node_outputs.values():
            prev_outputs[node.uuid].append(outputs)
    except ValueError:
        # Joined after the round has started.
        logger.info(
            f"[{node.uuid}] Could not retrieve local outputs for round {r} stage {s - 1}"
        )

    # Add other nodes' samples iff rewards are available.
    if prev_rewards:
        node_uuids = prev_rewards.keys()
        for node_uuid in node_uuids:
            if node_uuid == node.uuid:
                continue
            try:
                prev_node_outputs = get_outputs(dht, node_uuid, r, s - 1)
                for _, outputs in prev_node_outputs.values():
                    prev_outputs[node_uuid].append(outputs)
            except ValueError:
                # Skip this node's answers for the current round and stage.
                logger.info(
                    f"[{node.uuid}] Found rewards published for node: {node_uuid} but no outputs!"
                )

    #  Merge all samples.
    q_to_keyed_outputs: dict[str, dict[str, Any]] = defaultdict(dict)
    for node_uuid, all_outputs in prev_outputs.items():
        for outputs in all_outputs:
            q_to_keyed_outputs[outputs["question"]][node_uuid] = outputs

    for outputs in q_to_keyed_outputs.values():
        merged = merge_fn(outputs)
        merged_qs.append(merged)

    return samples_fn(merged_qs)


def gsm8k_stage_data(
    dht: DHT, node: HivemindNode, initial_train_dataset, initial_test_dataset
):
    def cumulative_reward_0(**kwargs):
        return stage1_rewards.hivemind_cumulative_reward(node, **kwargs)

    def cumulative_reward_1(**kwargs):
        return stage2_rewards.hivemind_cumulative_reward(node, **kwargs)

    def cumulative_reward_2(**kwargs):
        return stage3_rewards.hivemind_cumulative_reward(node, **kwargs)

    def stage2_datasets_fn(r, s):
        return merged_prev_stage_datasets(
            dht, node, r, s, merge_stage1_question, get_stage2_samples
        )

    def stage3_datasets_fn(r, s):
        return merged_prev_stage_datasets(
            dht, node, r, s, merge_stage2_question, get_stage3_samples
        )

    return StageData(
        stages=[
            SingleStageData(
                name="0",
                reward_funcs=[
                    stage1_rewards.xmlcount_reward_func,
                    stage1_rewards.soft_format_reward_func,
                    stage1_rewards.strict_format_reward_func,
                    stage1_rewards.int_reward_func,
                    stage1_rewards.correctness_reward_func,
                    cumulative_reward_0,
                ],
                datasets_fn=lambda r, s: (initial_train_dataset, initial_test_dataset),  # type: ignore
            ),
            SingleStageData(
                name="1",
                reward_funcs=[
                    stage2_rewards.proper_id_reward_func,
                    stage2_rewards.correctness_reward_func,
                    stage2_rewards.strict_format_reward_func,
                    stage2_rewards.soft_format_reward_func,
                    stage2_rewards.xmlcount_reward_func,
                    cumulative_reward_1,
                ],
                datasets_fn=stage2_datasets_fn,  # type: ignore
            ),
            SingleStageData(
                name="2",
                reward_funcs=[
                    stage3_rewards.consensus_reward_func,
                    stage3_rewards.concensus_correctness_reward_func,
                    stage3_rewards.question_recreation_reward_func,
                    stage3_rewards.final_correctness_reward_func,
                    stage3_rewards.strict_format_reward_func,
                    stage3_rewards.soft_format_reward_func,
                    stage3_rewards.xmlcount_reward_func,
                    cumulative_reward_2,
                ],
                datasets_fn=stage3_datasets_fn,  # type: ignore
            ),
        ],
    )
