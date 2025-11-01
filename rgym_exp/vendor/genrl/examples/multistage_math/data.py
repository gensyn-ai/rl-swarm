import random
from typing import Any, Dict, List, Tuple

from datasets import Dataset, load_dataset

from rgym_exp.vendor.genrl.data import LocalMemoryTextDataManager
from rgym_exp.vendor.genrl.state import WorldState

# --- Constants (System Prompts) ---
STAGE0_SYSTEM_PROMPT = """
You joined a mathematics study group. You are given a math problem, and you want to come up with the best possible answer to share with the rest of the group. Think through the solution of the problem step by step and then state your final answer.
An ideal solution will satisfy three important criteria: 1) Your step by step reasoning is correct, concise, and clearly related to the problem. 2) The last line of your response should be of the form Answer: $Answer (without quotes) where $Answer is the answer to the problem. 3) The final answer you give will be the mathematically correct answer.
Remember to put your answer on its own line after \"Answer:\".
"""

STAGE1_SYSTEM_PROMPT = """
You are reviewing solutions to a given math problem that have been submitted by students in a study group. Your goal is to determine which solution is best amongst all the solutions you receive. If all solutions are equally good, choose the one that is most concise.
Before responding to the math problem all students in the study group were instructed to think through the solution of the problem step by step and then state their final answer on its own line after \"Answer:\".
Ideal solutions to the problem will satisfy three important criteria: 1) Their step by step reasoning is correct, concise, and clearly related to the problem. 2) The last line of the solution should be of the form Answer: $Answer (without quotes) where $Answer is the answer to the problem. 3) The final answer is mathematically correct answer.
Give a step by step comparison of the different solutions you received and explain why a specific solution is the best according to the three stated criteria (or why no answer is correct).
The last line of your response should be of the form Choice: $Choice (without quotes) where $Choice is the unique student number of the solution you believe was best or say "None" if no solution was correct.
Remember to put your final choice on its own line after \"Choice:\".
"""

STAGE2_SYSTEM_PROMPT = """
You are part of a mathematics study group. After receiving a math problem, all members of your study group independently came up with their own solution and then compared all the proposed solution. Treat the best solutions to the problem and the feedback/criticisms about them as additional information, then think through the solution of the problem step by step again and state the final answer.
Before responding to the math problem all students in the study group were instructed to state their final answer on its own line after \"Answer:\". Similarly, before comparing/criticizing the proposed solutions, all students were instructed to put their final choice on its own line after \"Choice:\".
An ideal solution will satisfy three important criteria: 1) Your step by step reasoning is correct, concise, and clearly related to the problem. 2) The last line of your response should be of the form Answer: $Answer (without quotes) where $Answer is the answer to the problem. 3) The final answer you give will be the mathematically correct answer.
Remember to put your answer on its own line after \"Answer:\".
"""

PROMPT_ROLES = {
    "PIRATE": "You are a 17th century pirate, speak in time-period-accurate vernacular and follow the mathematical conventions of the time.",
    "PROFESSOR": "Your name is Professor Archibaldexposition and you are a mathematics professor at a prestigious university. Speak with eloquent and precise language.",
    "CHILD": "You are a 5 year old child who is very good at math. You sometimes make spelling errors or use improper grammar.",
    "ALIEN": "You are an alien from a distant galaxy who is trying to understand human mathematics. You sometimes confuse human customs or units of measure.",
    "FOUNDER": "Your name is Bearry and you are from the UK and you are the founder of a crypto start-up. Speak as you would during an investor meeting.",
}


class MSMDataManager(LocalMemoryTextDataManager):
    """Data Manager for Multi-Stage Math Games."""

    def __init__(
        self,
        train_dataset: str | None,
        evaluation_dataset: str | None = None,
        num_train_samples: int | None = 5,
        num_evaluation_samples: int | None = None,
        seed: int | None = None,
        batch_item_id_column: str | None = "question",
        prompt_generator_role: str | None = None,
    ):
        if "gsm8k" in train_dataset.lower():
            column_name_map = {"question": "question", "answer": "answer"}
            column_preprocessing_map = {"answer": self.extract_hash_answer}
            kwargs = {"subsets": "main"}
            self.data_id = "gsm8k"
        elif "dapo" in train_dataset.lower():
            column_name_map = {"question": "prompt", "answer": "solution"}
            column_preprocessing_map = None
            kwargs = {"subsets": "en"}
            self.data_id = "dapo"
        elif "big-math-rl" in train_dataset.lower():
            column_name_map = {"question": "prompt", "answer": "solution"}
            column_preprocessing_map = None  # TODO: Come in and add a latex answer extraction+normalizer function
            kwargs = {"subsets": "all"}
            self.data_id = "big-math-rl"
        else:
            raise ValueError(
                "You have specified a dataset that is not recognized by this default data manager for the multi-stage-math game. Please use GSM8K, DAPO-Math, or Big-Math-RL datasets from hugging face."
            )

        super().__init__(
            train_dataset=train_dataset,
            evaluation_dataset=evaluation_dataset,
            num_train_samples=num_train_samples,
            num_evaluation_samples=num_evaluation_samples,
            column_name_map=column_name_map,
            column_preprocessing_map=column_preprocessing_map,
            seed=seed,
            batch_item_id_column=batch_item_id_column,
            **kwargs,
        )

        self.prompt_generator_role = prompt_generator_role
        self.STAGE0_SYSTEM_PROMPT = STAGE0_SYSTEM_PROMPT
        self.STAGE1_SYSTEM_PROMPT = STAGE1_SYSTEM_PROMPT
        self.STAGE2_SYSTEM_PROMPT = STAGE2_SYSTEM_PROMPT
        self.PROMPT_ROLES = PROMPT_ROLES

    def initialize(self):
        # NOTE: Placeholder for any specific initialization logic needed by the manager
        #       For example, pre-loading datasets if they are static and large
        print(
            f"Multi-Stage Math Data Manager initialized with: datasets={self.datasets}, num_samples={self.num_samples}, seed={self.seed}, role={self.prompt_generator_role}"
        )
        pass

    # --- Helper Methods ---
    def extract_hash_answer(self, text: str) -> str | None:
        if "####" not in text:
            return None
        return text.split("####")[1].strip()

    def generate_system_prompt(self, default_sys_prompt: str) -> str:
        if self.prompt_generator_role is None:
            return default_sys_prompt
        prompt_role_assignment = self.prompt_generator_role.upper()
        if prompt_role_assignment == "RANDOM":
            prompt_role_assignment = random.choice(list(self.PROMPT_ROLES.keys()))
        if prompt_role_assignment in self.PROMPT_ROLES:
            sys_prompt = self.PROMPT_ROLES[prompt_role_assignment] + default_sys_prompt
            return sys_prompt
        else:
            return default_sys_prompt

    def state_to_system_prompt(self, stage: int) -> str:
        if stage == 0:
            return self.generate_system_prompt(self.STAGE0_SYSTEM_PROMPT)
        elif stage == 1:
            return self.generate_system_prompt(self.STAGE1_SYSTEM_PROMPT)
        else:
            return self.generate_system_prompt(self.STAGE2_SYSTEM_PROMPT)

    def state_to_user_prompt(self, state: WorldState, stage: int) -> str:
        if stage == 0:
            return state.environment_states[
                "question"
            ]  # User prompt is just the math question in this case
        else:
            return self.append_to_last_stage_prompt(state, stage)

    def state_to_answer(self, state: WorldState) -> str:
        return state.environment_states["answer"]

    def append_to_last_stage_prompt(self, state: WorldState, stage: int) -> str:
        sp = []
        if stage == 1:
            sp.append(
                f"The given math problem is: {state.environment_states['question']}"
                + "  \n\n"
            )
            sp.append(
                "The following solutions were suggested for this problem:" + " \n"
            )
            for idx, opponent_response in enumerate(
                state.opponent_states
            ):  # NOTE: Assumes opponent states are already being stored as a list of generated strings from the opponent
                sp.append(f"--> Student #{idx} said: {opponent_response}\n\n")
            sp.append(
                'Remember to choose an appropriate "Student #" (or say None), explain your choice, put your final choice on its own line after "Choice:".\n\n'
            )
        elif stage == 2:
            sp.append(
                f"{self.state_to_user_prompt(state.environment_states['prior_stage_input_states'], stage=1)}"
                + "  \n"
            )
            sp.append(
                "After comparing these solutions, the following feedback was given about which answer is best:"
                + " \n"
            )
            for idx, opponent_response in enumerate(
                state.opponent_states
            ):  # NOTE: Assumes opponent states are already being stored as a list of generated strings from the opponent
                sp.append(f"--> Criticism #{idx} was: {opponent_response}\n\n")
            sp.append(
                'Remember to think through your solution step by step and put your answer on its own line after "Answer:".\n\n'
            )
        else:
            raise ValueError(
                f"Unsupported stage for append_to_last_stage_prompt: {stage}"
            )
        return "".join(sp)

    # --- Required Methods ---
    def flatten_states(
        self, flattened_input: Dict[str, List[Any]], state: List[Any], stage: int
    ) -> Dict[str, List[Any]]:
        if flattened_input == {}:
            flattened_input = {"system_prompt": [], "user_prompt": [], "answer": []}
        flattened_input["system_prompt"].append(self.state_to_system_prompt(stage))
        flattened_input["user_prompt"].append(self.state_to_user_prompt(state, stage))
        flattened_input["answer"].append(self.state_to_answer(state))
        return flattened_input

    def prepare_environment(
        self,
        node_states: WorldState,
        swarm_states: Dict[Any, Any],
        stage: int,
        agent: Any,
        batch_id: Any,
    ) -> Any:
        return node_states.environment_states

    def prepare_opponent(
        self,
        node_states: List[Any],
        swarm_states: Dict[Any, Any],
        stage: int,
        agent: Any,
        batch_id: Any,
    ) -> Any:
        return self.filter_swarm_states(swarm_states=swarm_states, batch_id=batch_id)

    def prepare_personal(
        self,
        node_states: List[Any],
        swarm_states: Dict[Any, Any],
        stage: int,
        agent: Any,
        batch_id: Any,
    ) -> Any:
        return None
