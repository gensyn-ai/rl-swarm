import os, random
from datasets import load_dataset, Dataset

#############################################################################################################
# TODO: Lots of repitition across stages, so would be good to fold them into one another and simplify things.#
#############################################################################################################

STAGE1_SYSTEM_PROMPT = """
You joined a mathematics study group. You are given a math question, and you want to come up with the best possible answer to share with the rest of the group. To ensure other understand your answer, first think through the reasoning needed to reach your final answer and then state your final answer.
An ideal answer will satisfy four important criteria: 1) The reasoning for your final answer will be in <think> </think> tags. 2) Your final answer to the question will be in <answer> </answer> tags. 3) Your reasoning will be correct, concise, and clearly related to the question. 4) The final answer you give will be the mathematically correct answer.
Respond in the following format:
<think>
...
</think>
<answer>
...
</answer>
"""

STAGE2_SYSTEM_PROMPT = """
You joined a mathematics study group. After being given a math question, all members of your study group have independantly come up with their own answer and you now want to decide which answer is best (or if no answer is correct). All students in the study group were instructed to give their reasoning process in <think> </think> tags and the final answer to the question in <answer> </answer> tags.
An ideal answer will satisfy four important criteria: 1) The reasoning for their final answer will be in <think> </think> tags. 2) Their final answer to the question will be in <answer> </answer> tags. 3) Their reasoning will be correct, concise, and clearly related to the question. 4) The final answer will be mathematically correct.
As a reminder, among all answers you have received, you want to decide which answer is best or if no answer is correct. You should compare the reasoning process of the different answers you've received, then explain why an answer is the best (or why no answer is correct), and finally you should state the unique student identifier (marked by <student> <\student> tags) of the answer you believe is best or say "None" if no answer was correct.
Respond in the following format:
<compare>
...
</compare>
<explain>
...
</explain>
<identify>
...
</identify>
"""

STAGE3_SYSTEM_PROMPT = """
You joined a mathematics study group. After being given a math question, all members of your study group have independantly come up with their own answer and then compared all the proposed answers. You now have two tasks: 1) Consider the feedback/criticisms given by members of the study group and decide which answer you believe a majority of the group will agree is best (or say "None" if no answer was correct). 2) Incorporate details from the best answers, and the feedback/criticisms about these answers, to give the best possible answer to the question.
Before answering the question, all students in the study group were instructed to first give their reasoning process in <think> </think> tags and then give the final answer to the question in <answer> </answer> tags. Similarly, before comparing/criticizing the proposed answers, students in the study group were instructed to first compare the reasoning process of the different answers in <compare> </compare> tags and then to explain why an answer is best (or why no answer is correct) in <explain> </explain> tags and lastly to state the unique student identifier of the answer in <identify> </identify> tags.
As a reminder, for the given question, you want to consider all answers suggested by the study group alongside the feedback/criticisms given by the group about these answers. After doing so, you have two goals: 1) State which answer you believe the majority of the study group will accept is best (or say "None" if no suggested answers are correct). 2) Give the best possible answer to the question by incorporating details from the best answers as well as feedback/criticisms about these answers.
You should first summarize the feedback/criticisms given by the group, then state the unique student identifier (marked by <student> <\student> tags) of the answer you believe a majority of the study group will accept as best, then restate the question the study group is trying to solve, and lastly (utilizing your newfound understanding of what the study group likes to see in an answer) provide the best answer to the question by thinking through the reasoning steps before stating the final answer to the question.
Respond in the following format:
<summarize_feedback>
...
</summarize_feedback>
<majority>
...
</majority>
<question>
...
</question>
<think>
...
</think>
<answer>
...
</answer>
"""

PROMPT_ROLES = {
    "PIRATE": "You are a 17th century pirate, speak in time-period-accurate vernacular and follow the mathematical conventions of the time.",
    "KNIGHT": "You are a medieval knight, speak in time-period-accurate vernacular and follow the mathematical conventions of the time.",
    "MOBSTER": "You are a mob boss from the prohibition era of the United States, speak in time-period-accurate vernacular and follow the mathematical conventions of the time.",
    "ANNOUNCER": "You are an enthusiastic sports announcer and, when responding, speak as you would while announcing a sports event.",
    "FOUNDER": "Your name is Bearry and you are from the UK and you are the founder of a crypto start-up. Speak as you would during an investor meeting.",
}


def extract_hash_answer(text: str) -> str | None:
    if "####" not in text:
        return None
    return text.split("####")[1].strip()


def generate_system_prompt(default_sys_prompt):
    if os.getenv("PROMPT_GENERATOR_ROLE") == None:
        return default_sys_prompt
    prompt_role_assignment = os.getenv("PROMPT_GENERATOR_ROLE").upper()
    if prompt_role_assignment == "RANDOM":
        prompt_role_assignment = random.choice(list(PROMPT_ROLES.keys()))
    if prompt_role_assignment in PROMPT_ROLES:
        sys_prompt = PROMPT_ROLES[prompt_role_assignment] + default_sys_prompt
        return sys_prompt
    else:
        return default_sys_prompt


def stage2_generator(values):
    # TODO: A bit hacky/ugly. Should come back and clean up a bit
    for val in values:
        output = {}
        for field in val:
            if field not in ["agent_answers"]:
                output[field] = val[field]
            else:
                for subfield in val[field]:
                    output[f"{field}_{subfield}"] = val[field][subfield]
        yield output


def stage3_generator(values):
    # TODO: A bit hacky/ugly. Should come back and clean up a bit
    for val in values:
        output = {}
        for field in val:
            if field not in {"agent_answers", "agent_opinion"}:
                output[field] = val[field]
            else:
                for subfield in val[field]:
                    output[f"{field}_{subfield}"] = val[field][subfield]
        yield output


def sorted_agent_ids(cols, prefix):
    # Undos the _ encoding.
    agent_ids = []
    for c in cols:
        if c.startswith(prefix):
            agent_ids.append(c[len(prefix) :])
    agent_ids.sort(reverse=False)
    return agent_ids


# Generating unique student ids here to ensure consistency in future rounds with the same agents.
# TODO: Currently assumes number of respondents is the same across rounds. We should loosen this requirement, but need to think of a way to reasonably add a "name"/id our models can be expected to "remember"...
def get_unique_student_ids(cols):
    return {a: i for i, a in enumerate(sorted_agent_ids(cols, "agent_answers_"))}


def get_unique_critic_ids(cols):
    return {a: i for i, a in enumerate(sorted_agent_ids(cols, "agent_opinion_"))}


def generate_stage2_user_prompt(datum, cols):
    sp = []
    sp.append(f"The question we were given is: {datum['question']}" + "  \n\n")
    sp.append(f"The following answers to this question were suggested:" + " \n")
    agentID_to_studentID = get_unique_student_ids(cols)
    for agentID in agentID_to_studentID:
        feature = f"agent_answers_{agentID}"
        if feature in datum:
            sp.append(
                f"<student>Student #{agentID_to_studentID[agentID]}</student> said \n"
            )
            sp.append(datum[feature])
            sp.append("\n\n\n")
    return "".join(sp)


def generate_stage3_user_prompt(datum, cols):
    sp = []
    sp.append(f"{datum['stage2_prompt']}" + "  \n")
    sp.append(
        f"After comparing these answers, the following feedback was given about which answer is best:"
        + " \n"
    )
    # TODO: Why is this different from shared_fs_experiments?
    agentID_to_criticID = get_unique_critic_ids(cols)
    for agentID in agentID_to_criticID:
        feature = f"agent_opinion_{agentID}"
        if feature in datum:
            sp.append(
                f"<criticism>Criticism #{agentID_to_criticID[agentID]}</criticism> was \n"
            )
            sp.append(datum[feature])
            sp.append("\n\n\n")
    return "".join(sp)


def get_gsm8k_questions(data) -> Dataset:
    sys_prompt = generate_system_prompt(STAGE1_SYSTEM_PROMPT)

    data = data.map(
        lambda x: {
            "prompt": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": x["question"]},
            ],
            "answer": extract_hash_answer(x["answer"]),
        }
    )
    return data


def get_gsm8k_questions_with_stage1_answers(data) -> Dataset:
    sys_prompt = generate_system_prompt(STAGE2_SYSTEM_PROMPT)
    cols = data.column_names
    data = data.map(
        lambda x: {  # type: ignore
            "prompt": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": generate_stage2_user_prompt(x, cols)},
            ],
            "answer": x["answer"],
        }
    )
    return data


def get_gsm8k_questions_with_stage1and2_answers(data) -> Dataset:
    sys_prompt = generate_system_prompt(STAGE3_SYSTEM_PROMPT)
    cols = data.column_names
    data = data.map(
        lambda x: {  # type: ignore
            "prompt": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": generate_stage3_user_prompt(x, cols)},
            ],
            "answer": x["answer"],
        }
    )
    return data


def get_stage1_samples():
    # Load dataset from Hugging Face Hub
    dataset_id = "openai/gsm8k"
    train_dataset = load_dataset(dataset_id, "main")["train"]
    test_dataset = load_dataset(dataset_id, "main")["test"]
    # #TODO: Add ability to select a random subset of num_samples samples if desired
    # if num_samples != -1:
    #   dataset = dataset.shuffle(seed=42).select(range(num_samples))

    # convert our dataset to the r1 prompt
    train_dataset = get_gsm8k_questions(train_dataset)
    test_dataset = get_gsm8k_questions(test_dataset)
    return train_dataset, test_dataset


def fill_unknown_answers_opinions(values):
    FILLED_FIELDS = ("agent_answers", "agent_opinion")

    # Collect all agent keys
    agent_set = set()
    for val in values:
        for field in val:
            if field in FILLED_FIELDS:
                agent_set |= val[field].keys()

    # Fill in empty agent_answers + agent_opinions
    for val in values:
        for field in val:
            if field in FILLED_FIELDS:
                diff_keys = agent_set - val[field].keys()
                for agent in (
                    diff_keys
                ):  # Fill with default values. TODO: Decide if this is a good choice.
                    val[field].update({agent: "No answer received..."})


def get_stage2_samples(values, test_size=0.1):
    fill_unknown_answers_opinions(values)
    dataset = Dataset.from_generator(stage2_generator, gen_kwargs={"values": values})
    # #TODO: Add ability to select a random subset of num_samples samples if desired
    # if num_samples != -1:
    #   dataset = dataset.shuffle(seed=42).select(range(num_samples))

    # convert our dataset to the r1 prompt
    dataset = get_gsm8k_questions_with_stage1_answers(dataset)
    return dataset, dataset


def get_stage3_samples(values, test_size=0.1):
    fill_unknown_answers_opinions(values)
    dataset = Dataset.from_generator(stage3_generator, gen_kwargs={"values": values})
    # #TODO: Add ability to select a random subset of num_samples samples if desired
    # if num_samples != -1:
    #   dataset = dataset.shuffle(seed=42).select(range(num_samples))

    # convert our dataset to the r1 prompt
    dataset = get_gsm8k_questions_with_stage1and2_answers(dataset)
    return dataset, dataset
