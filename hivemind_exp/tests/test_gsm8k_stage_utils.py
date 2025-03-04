from enum import Enum
import itertools
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import time

import hivemind
import pytest
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import GRPOConfig
from hivemind.dht import DHT
from hivemind.utils import get_dht_time

from datasets import Dataset

from hivemind_exp.gsm8k.stage_utils import (
    HivemindNode,
    merge_stage1_question,
    merge_stage2_question,
    get_stage2_samples,
    get_stage3_samples,
    gsm8k_stage_data,
    merged_prev_stage_datasets,
    rewards_key,
)
from hivemind_exp.tests.fake_data import (
    CK,
    QUESTION,
    RSK,
    SAMPLES,
    STAGE_2_OUTPUTS,
    STAGE_2_MERGED,
    samples_with_uuid,
)
from hivemind_exp.trainer.hivemind_grpo_trainer import (
    HivemindGRPOTrainer,
    get_dht_value,
)
from hivemind_exp.dht_utils import outputs_key
from hivemind_exp.utils import SingleStageData

TEST_MODEL_NAME = "trl-internal-testing/tiny-Qwen2ForCausalLM-2.5"


def get_model_config(tmp_path):
    model = AutoModelForCausalLM.from_pretrained(TEST_MODEL_NAME)
    config = GRPOConfig(
        output_dir=tmp_path,
        learning_rate=5e-7,
        lr_scheduler_type="cosine",
        max_steps=1,
    )
    return model, config


def wrap_datasets_fn(stage: SingleStageData, check):
    orig = stage.datasets_fn

    def wrapped(r, s):
        value = orig(r, s)
        check(value[0])
        return value

    stage.datasets_fn = wrapped


def check_dataset(prefix: str, min_count: int, dataset: Dataset):
    c = 0
    for feature in dataset.features:
        if feature.startswith(prefix):
            c += 1
    assert c >= min_count


def create_dht_and_trainer(tmp_path, node, min_peers=1, initial_peers=[]):
    dht = hivemind.DHT(start=True, initial_peers=initial_peers, cache_nearest=min_peers)
    model, config = get_model_config(tmp_path)
    tokenizer = AutoTokenizer.from_pretrained(TEST_MODEL_NAME)

    # Always check stage merging.

    def check_merged_stage1_dataset(dataset: Dataset):
        # print(f"Merged stage 1 for: {node.uuid}", dataset)
        check_dataset("agent_answers", min_peers, dataset)

    def check_merged_stage2_dataset(dataset: Dataset):
        # print(f"Merged stage 2 for: {node.uuid}", dataset)
        check_dataset("agent_opinion", min_peers, dataset)

    stage_data = gsm8k_stage_data(dht, node, SAMPLES, SAMPLES)
    stage_data.max_rounds = 1
    stage_data.stages[0].datasets_fn = lambda r, s: (SAMPLES, SAMPLES)  # type: ignore
    wrap_datasets_fn(stage_data.stages[1], check_merged_stage1_dataset)
    wrap_datasets_fn(stage_data.stages[2], check_merged_stage2_dataset)

    trainer = HivemindGRPOTrainer(
        dht=dht,
        node=node,
        model=model,
        tokenizer=tokenizer,
        config=config,
        stage_data=stage_data,
    )
    return dht, trainer


def store_dummy_rewards(dht: DHT, uuids, r, s):
    for uuid in uuids:
        dht.store(
            key=rewards_key(r, s),
            subkey=uuid,
            value=[99],
            expiration_time=get_dht_time() + 60,
        )


class StorageMode(Enum):
    DHT = 1
    NODE = 2
    BOTH = 3


def store_stage_outputs(
    dht: DHT, node: HivemindNode, r, s, value: dict, storage_mode=StorageMode.BOTH
):
    if storage_mode in (StorageMode.DHT, StorageMode.BOTH):
        dht.store(
            key=outputs_key(node.uuid, r, s),
            subkey=QUESTION,
            value=(0, value),
            expiration_time=get_dht_time() + 120,
        )
    if storage_mode in (StorageMode.NODE, StorageMode.BOTH):
        node.put_stage_outputs(r, s, QUESTION, (0, value))


STAGE_2_SAMPLES = [
    STAGE_2_OUTPUTS[CK],
    STAGE_2_OUTPUTS["0"],
]

STAGE_2_MERGED_OPINIONS = STAGE_2_MERGED["agent_opinion"]


@pytest.mark.parametrize(
    "merge_fn,sample_fn,stage,samples,group_field,get_expected_fn",
    [
        (
            merge_stage1_question,
            get_stage2_samples,
            0,
            SAMPLES,
            "agent_answers",
            lambda: ("The meaning of life is to sleep.", "The meaning of life is 42."),
        ),
        (
            merge_stage2_question,
            get_stage3_samples,
            1,
            STAGE_2_SAMPLES,
            "agent_opinion",
            lambda: (STAGE_2_MERGED_OPINIONS["0"], STAGE_2_MERGED_OPINIONS[CK]),
        ),
    ],
)
def test_merged_prev_stage_datasets(
    merge_fn, sample_fn, stage, samples, group_field, get_expected_fn
):
    dht = hivemind.DHT(start=True)
    coord = HivemindNode.coordinator("test")
    node = HivemindNode("test")

    def merge_coord():
        return merged_prev_stage_datasets(dht, coord, 0, stage + 1, merge_fn, sample_fn)

    def merge_node():
        return merged_prev_stage_datasets(dht, node, 0, stage + 1, merge_fn, sample_fn)

    ## Nothing stored!
    with pytest.raises(Exception):
        _ = merge_coord()

    # Training loop saves to both.
    coord_samples = samples_with_uuid(CK, samples, group_field)
    store_stage_outputs(dht, coord, 0, stage, coord_samples[0], StorageMode.DHT)
    store_stage_outputs(
        dht, coord, 0, stage, coord_samples[1], StorageMode.NODE
    )  # Takes precedence.

    node_samples = samples_with_uuid(node.uuid, samples, group_field)
    store_stage_outputs(
        dht, node, 0, stage, node_samples[0], StorageMode.NODE
    )  # Local only.

    ## Rewards not visible on DHT!
    coord_expected, node_expected = get_expected_fn()
    cf, nf = merge_coord()[0][0], merge_node()[0][0]

    # Local.
    assert cf[f"{group_field}_{CK}"] == coord_expected
    assert f"{group_field}_{node.uuid}" not in cf

    # Local.
    assert f"{group_field}_{CK}" not in nf
    assert nf[f"{group_field}_{node.uuid}"] == node_expected

    ## Check merged outputs with visible rewards!
    store_dummy_rewards(dht, [coord.uuid, node.uuid], 0, stage)
    cf, nf = merge_coord()[0][0], merge_node()[0][0]

    # Local.
    assert cf[f"{group_field}_{CK}"] == coord_expected
    assert f"{group_field}_{node.uuid}" not in cf

    # Local + DHT.
    assert nf[f"{group_field}_{CK}"] == node_expected
    assert nf[f"{group_field}_{node.uuid}"] == node_expected


def test_gsm8k_stage_data(tmp_path):
    coord = HivemindNode.coordinator("test")
    nodes = [HivemindNode("test") for _ in range(3)]

    dht_trainers = [create_dht_and_trainer(Path(tmp_path) / "C", coord, min_peers=2)]
    dht0 = dht_trainers[0][0]
    for i, node in enumerate(nodes):
        dht_trainers.append(
            create_dht_and_trainer(
                Path(tmp_path) / str(i),
                node,
                min_peers=2,
                initial_peers=dht0.get_visible_maddrs(),
            )
        )

    for dht, _ in dht_trainers:
        _ = dht.get_visible_maddrs(latest=True)

    with ThreadPoolExecutor() as executor:
        for dht, trainer in dht_trainers:
            executor.submit(trainer.train)

    rs = get_dht_value(dht0, key=RSK, latest=True)
    assert rs == (0, 2)  # 1 round, 3 stages

    def check_outputs(outputs: dict[str, tuple] | None, output_checks={}):
        assert outputs
        qo = outputs[QUESTION][1]
        assert qo["question"] == QUESTION
        assert qo["answer"] == "42"
        for k, check in output_checks.items():
            assert k in qo
            assert check(qo[k])

    for r, s in itertools.product(range(1), range(3)):
        match s:
            case 0:
                checks = {}
            case 1:
                # Only one before merging.
                checks = {"agent_opinion": lambda c: len(c) == 1}
            case 2:
                checks = {"final_agent_decision": lambda c: len(c) == 1}
            case _:
                checks = {}

        for i in range(len(nodes)):
            check_outputs(
                get_dht_value(dht0, key=outputs_key(nodes[i].uuid, r, s), latest=True),
                checks,
            )

        rewards = get_dht_value(dht0, key=rewards_key(r, s), latest=True)
        assert rewards
        assert rewards.keys() == set([CK] + [node.uuid for node in nodes])


def test_gsm8k_delayed_join(tmp_path):
    node0 = HivemindNode.coordinator("test")
    node1 = HivemindNode("test")

    dht0, trainer0 = create_dht_and_trainer(Path(tmp_path) / "0", node0)
    dht1, trainer1 = create_dht_and_trainer(
        Path(tmp_path) / "1",
        node1,
        initial_peers=dht0.get_visible_maddrs(),
    )
    _ = dht0.get_visible_maddrs(latest=True)
    _ = dht1.get_visible_maddrs(latest=True)

    def delayed_train():
        while trainer0.node.stage_num == 0:
            time.sleep(0.5)

        trainer1.train()

    with ThreadPoolExecutor() as executor:
        executor.submit(trainer0.train)
        executor.submit(delayed_train)

    rs = get_dht_value(dht0, key=RSK, latest=True)
    assert rs == (0, 2)  # 1 round, 3 stages

    for r, s in itertools.product(range(1), range(3)):
        outputs0 = get_dht_value(dht1, key=outputs_key(node0.uuid, r, s), latest=True)
        assert outputs0

        if s > 0:
            outputs1 = get_dht_value(
                dht0, key=outputs_key(node1.uuid, r, s), latest=True
            )
            assert outputs1
