from copy import deepcopy
from hivemind_exp.utils import COORDINATOR_KEY
from hivemind_exp.dht_utils import ROUND_STAGE_NUMBER_KEY

CK = COORDINATOR_KEY
RSK = ROUND_STAGE_NUMBER_KEY

QUESTION = "What is the meaning of life?"

SAMPLES = [
    {
        "question": QUESTION,
        "answer": "42",
        "prompt": [
            {"content": "You are a pirate.", "role": "system"},
            {"content": QUESTION, "role": "user"},
        ],
        "agent_answers": {
            CK: "The meaning of life is 42.",
        },
    },
    {
        "question": QUESTION,
        "answer": "sleep",
        "prompt": [
            {"content": "You are a cat.", "role": "system"},
            {"content": QUESTION, "role": "user"},
        ],
        "agent_answers": {
            "0": "The meaning of life is to sleep.",
        },
    },
]


def samples_with_uuid(new_uuid, orig_samples=SAMPLES, field="agent_answers"):
    orig_uuids = (CK, "0", "1", "2")

    def replace(orig, value):
        if field in value:
            answers = value[field]
            if orig != new_uuid and orig in answers:
                answers[new_uuid] = answers[orig]
                del answers[orig]

    samples = deepcopy(orig_samples)
    for sample in samples:
        for orig in orig_uuids:
            replace(orig, sample)

    return samples


STAGE_1_OUTPUTS = {
    CK: {
        "question": "Carl is taking a class where the whole grade is based on four tests that are graded out of 100. He got an 80, a 75 and a 90 on his first three tests. If he wants an 85 average for the class, what is the minimum grade he needs to get on his last test?",
        "answer": "95",
        "agent_answers": {
            CK: "To determine the minimum grade Carl needs on his last test to achieve an 85 average, we'll follow these steps:\n\n1. First, calculate the total score Carl needs to average 85 across all four tests.\n2. Sum up the scores of the first three tests.\n3. Subtract the sum from the total score needed to find out the required score on the fourth test.\n\nLet's do the math:\n\n1. Total score needed with an 85 average:\n\\[ \\text{Total score needed} = 85 \\times 4 \\]\n\n2. Sum of the scores of the first three tests:\n\\[ \\text{Sum of scores} = 80 + 75 + 90 \\]\n\n3. Subtract the sum from the total score needed:\n\\[ \\text{Required score on the fourth test} = \\text{Total score needed} - \\text{Sum of scores} \\]\n\nNow, let's calculate the values:\n\n\\[ \\text{Total score needed} = 85 \\times 4 = 340 \\]\n\n\\[ \\text{Sum of scores} = 80 + 75 + 90 = 245 \\]\n\n\\[ \\text{Required score on the fourth test} = 340 - 245 = 95 \\]\n\nTherefore, the minimum grade Carl needs to get on his last test to achieve an 85 average is **95**.\n\n<answer>\n95\n</answer>"
        },
    },
    "0": {
        "question": "Carl is taking a class where the whole grade is based on four tests that are graded out of 100. He got an 80, a 75 and a 90 on his first three tests. If he wants an 85 average for the class, what is the minimum grade he needs to get on his last test?",
        "answer": "95",
        "agent_answers": {
            "0": "<think>\nCarl's first three test scores are 80, 75, and 90, adding up to a total of 245. To achieve an 85 average for the class, his four test scores must total 4 times 85, which is 340. Therefore, the minimum grade he needs on his last test is 340 - 245 = 95.\n</think>\n\n<answer>\n95\n</answer>\n\n95",
        },
    },
    "1": {
        "question": "Carl is taking a class where the whole grade is based on four tests that are graded out of 100. He got an 80, a 75 and a 90 on his first three tests. If he wants an 85 average for the class, what is the minimum grade he needs to get on his last test?",
        "answer": "95",
        "agent_answers": {
            "1": "<think>\nTo find out the minimum grade Carl needs on his last test to achieve an average of 85, we first calculate the total score he needs for all four tests. Since the average of four tests is 85, the total score needed is \\(4 \\times 85 = 340\\) points.\n\nNext, we sum up the scores of the first three tests: \\(80 + 75 + 90 = 245\\).\n\nNow, we subtract the sum of the first three tests from the total score needed to find the minimum score Carl needs on his last test: \\(340 - 245 = 95\\).\n</think>\n\n<answer>\n95\n</answer>",
        },
    },
    "2": {
        "question": "Carl is taking a class where the whole grade is based on four tests that are graded out of 100. He got an 80, a 75 and a 90 on his first three tests. If he wants an 85 average for the class, what is the minimum grade he needs to get on his last test?",
        "answer": "95",
        "agent_answers": {
            "2": "No answer received...",
        },
    },
}

STAGE_1_MERGED = {
    "question": "Carl is taking a class where the whole grade is based on four tests that are graded out of 100. He got an 80, a 75 and a 90 on his first three tests. If he wants an 85 average for the class, what is the minimum grade he needs to get on his last test?",
    "answer": "95",
    "agent_answers": {
        CK: "To determine the minimum grade Carl needs on his last test to achieve an 85 average, we'll follow these steps:\n\n1. First, calculate the total score Carl needs to average 85 across all four tests.\n2. Sum up the scores of the first three tests.\n3. Subtract the sum from the total score needed to find out the required score on the fourth test.\n\nLet's do the math:\n\n1. Total score needed with an 85 average:\n\\[ \\text{Total score needed} = 85 \\times 4 \\]\n\n2. Sum of the scores of the first three tests:\n\\[ \\text{Sum of scores} = 80 + 75 + 90 \\]\n\n3. Subtract the sum from the total score needed:\n\\[ \\text{Required score on the fourth test} = \\text{Total score needed} - \\text{Sum of scores} \\]\n\nNow, let's calculate the values:\n\n\\[ \\text{Total score needed} = 85 \\times 4 = 340 \\]\n\n\\[ \\text{Sum of scores} = 80 + 75 + 90 = 245 \\]\n\n\\[ \\text{Required score on the fourth test} = 340 - 245 = 95 \\]\n\nTherefore, the minimum grade Carl needs to get on his last test to achieve an 85 average is **95**.\n\n<answer>\n95\n</answer>",
        "0": "<think>\nCarl's first three test scores are 80, 75, and 90, adding up to a total of 245. To achieve an 85 average for the class, his four test scores must total 4 times 85, which is 340. Therefore, the minimum grade he needs on his last test is 340 - 245 = 95.\n</think>\n\n<answer>\n95\n</answer>\n\n95",
        "1": "<think>\nTo find out the minimum grade Carl needs on his last test to achieve an average of 85, we first calculate the total score he needs for all four tests. Since the average of four tests is 85, the total score needed is \\(4 \\times 85 = 340\\) points.\n\nNext, we sum up the scores of the first three tests: \\(80 + 75 + 90 = 245\\).\n\nNow, we subtract the sum of the first three tests from the total score needed to find the minimum score Carl needs on his last test: \\(340 - 245 = 95\\).\n</think>\n\n<answer>\n95\n</answer>",
        "2": "No answer received...",
    },
}

STAGE_2_OUTPUTS = {
    CK: {
        "question": "Carl is taking a class where the whole grade is based on four tests that are graded out of 100. He got an 80, a 75 and a 90 on his first three tests. If he wants an 85 average for the class, what is the minimum grade he needs to get on his last test?",
        "answer": "95",
        "stage2_prompt": "The question we were given is: Carl is taking a class where the whole grade is based on four tests that are graded out of 100. He got an 80, a 75 and a 90 on his first three tests. If he wants an 85 average for the class, what is the minimum grade he needs to get on his last test?  \n\nThe following answers to this question were suggested: \n<student>Student #0</student> said \nTo find the minimum grade Carl needs on his last test to achieve an 85 average, we first calculate the total points he needs to achieve this average over four tests. The formula to calculate the total points needed for an average is:\n\n\\[ \\text{Total Points Needed} = \\text{Average} \\times \\text{Number of Tests} \\]\n\nSubstituting the given values:\n\n\\[ \\text{Total Points Needed} = 85 \\times 4 = 340 \\]\n\nNow, we need to sum up the points he has from his first three tests:\n\n\\[ \\text{Total Points from First Three Tests} = 80 + 75 + 90 = 245 \\]\n\nTo find the points he needs on his last test, we subtract the points from his first three tests from the total points needed:\n\n\\[ \\text{Points Needed on Last Test} = \\text{Total Points Needed} - \\text{Total Points from First Three Tests} \\]\n\n\\[ \\text{Points Needed on Last Test} = 340 - 245 = 95 \\]\n\nTherefore, Carl needs to score at least 95 on his last test to achieve an 85 average for the class.\n\n<answer>\n95\n</answer>\n\n\n<student>Student #1</student> said \nthink: Let's calculate the total possible points Carl could have scored:\n\n80 + 75 + 90 + x = 345\n\nWhere x is the score he needs on his last test.\n\nThen, we need to figure out how many points he needs to average 85:\n\n85 * 4 = 340\n\nNow we subtract the total points he has from the points he needs to find out how many points he needs on his last test:\n\n345 - 340 = 5\n\nSo, Carl needs at least a 95 on his last test to average 85 for the class.\n\n<answer>\n95\n</answer>\n\n\n",
        "agent_opinion": {
            CK: "<compare>\nStudent #0 states that the minimum grade Carl needs is 95, but the reasoning provided is not clear and is not directly related to the question asked. Student #1 provides detailed reasoning and a correct final answer. Student #2 also provides a clear and concise reasoning process, leading to the same final answer as Student #1. Student #3 also follows a valid reasoning process, also leading to the same final answer.\n</compare>\n<explain>\nThe key comparison highlights the lack of clarity and direct relevance to the question in the reasoning provided by Student #0, alongside Student #2 and Student #3, which provide correct and detailed answers. Student #1, however, clearly follows the process to calculate the minimum grade needed and arrives at the same correct answer as the others.\n</explain>\n<identify>\nStudent #1\n</identify>\n\nNone"
        },
    },
    "0": {
        "question": "Carl is taking a class where the whole grade is based on four tests that are graded out of 100. He got an 80, a 75 and a 90 on his first three tests. If he wants an 85 average for the class, what is the minimum grade he needs to get on his last test?",
        "answer": "95",
        "stage2_prompt": "The question we were given is: Carl is taking a class where the whole grade is based on four tests that are graded out of 100. He got an 80, a 75 and a 90 on his first three tests. If he wants an 85 average for the class, what is the minimum grade he needs to get on his last test?  \n\nThe following answers to this question were suggested: \n<student>Student #0</student> said \nTo find the minimum grade Carl needs on his last test to achieve an 85 average, we first calculate the total points he needs to achieve this average over four tests. The formula to calculate the total points needed for an average is:\n\n\\[ \\text{Total Points Needed} = \\text{Average} \\times \\text{Number of Tests} \\]\n\nSubstituting the given values:\n\n\\[ \\text{Total Points Needed} = 85 \\times 4 = 340 \\]\n\nNow, we need to sum up the points he has from his first three tests:\n\n\\[ \\text{Total Points from First Three Tests} = 80 + 75 + 90 = 245 \\]\n\nTo find the points he needs on his last test, we subtract the points from his first three tests from the total points needed:\n\n\\[ \\text{Points Needed on Last Test} = \\text{Total Points Needed} - \\text{Total Points from First Three Tests} \\]\n\n\\[ \\text{Points Needed on Last Test} = 340 - 245 = 95 \\]\n\nTherefore, Carl needs to score at least 95 on his last test to achieve an 85 average for the class.\n\n<answer>\n95\n</answer>\n\n\n<student>Student #1</student> said \nthink: Let's calculate the total possible points Carl could have scored:\n\n80 + 75 + 90 + x = 345\n\nWhere x is the score he needs on his last test.\n\nThen, we need to figure out how many points he needs to average 85:\n\n85 * 4 = 340\n\nNow we subtract the total points he has from the points he needs to find out how many points he needs on his last test:\n\n345 - 340 = 5\n\nSo, Carl needs at least a 95 on his last test to average 85 for the class.\n\n<answer>\n95\n</answer>\n\n\n",
        "agent_opinion": {
            "0": "<compare>\nStudent #0 and Student #1 both correctly calculated the total points required to achieve an 85 average and determined that Carl needs at least a 95 on his last test. \nThe difference is that Student #0 expressed the total points needed as 85 * 4 = 340, while Student #1 clearly stated that 85 * 4 = 345 and kept the number of tests consistent. This difference is irrelevant to the correctness of the calculation and can be disregarded.\nBoth answers are concise and directly related to the question.\n</compare>\n\n<explain>\nBoth Student #0 and Student #1 correctly calculated the total points Carl needs to achieve an 85 average for the class. They arrived at the answer of 95 without any errors.\n</explain>\n\n<identify>\nEither Student #0 or Student #1 is correct. Since neither answer is incorrect, the decision decides based on other specific criteria that would not be decided by comparing correctness alone.\n</identify>\n\n<identify>\nNone\n</identify>\n\nNone of the answers provided is incorrect. Both Student #0 and Student #1 correctly calculated the total points Carl needs to achieve an 85 average and determined that he needs at least a 95 on his last test.",
        },
    },
}

STAGE_2_MERGED = {
    "question": "Carl is taking a class where the whole grade is based on four tests that are graded out of 100. He got an 80, a 75 and a 90 on his first three tests. If he wants an 85 average for the class, what is the minimum grade he needs to get on his last test?",
    "answer": "95",
    "stage2_prompt": "The question we were given is: Carl is taking a class where the whole grade is based on four tests that are graded out of 100. He got an 80, a 75 and a 90 on his first three tests. If he wants an 85 average for the class, what is the minimum grade he needs to get on his last test?  \n\nThe following answers to this question were suggested: \n<student>Student #0</student> said \nTo find the minimum grade Carl needs on his last test to achieve an 85 average, we first calculate the total points he needs to achieve this average over four tests. The formula to calculate the total points needed for an average is:\n\n\\[ \\text{Total Points Needed} = \\text{Average} \\times \\text{Number of Tests} \\]\n\nSubstituting the given values:\n\n\\[ \\text{Total Points Needed} = 85 \\times 4 = 340 \\]\n\nNow, we need to sum up the points he has from his first three tests:\n\n\\[ \\text{Total Points from First Three Tests} = 80 + 75 + 90 = 245 \\]\n\nTo find the points he needs on his last test, we subtract the points from his first three tests from the total points needed:\n\n\\[ \\text{Points Needed on Last Test} = \\text{Total Points Needed} - \\text{Total Points from First Three Tests} \\]\n\n\\[ \\text{Points Needed on Last Test} = 340 - 245 = 95 \\]\n\nTherefore, Carl needs to score at least 95 on his last test to achieve an 85 average for the class.\n\n<answer>\n95\n</answer>\n\n\n<student>Student #1</student> said \nthink: Let's calculate the total possible points Carl could have scored:\n\n80 + 75 + 90 + x = 345\n\nWhere x is the score he needs on his last test.\n\nThen, we need to figure out how many points he needs to average 85:\n\n85 * 4 = 340\n\nNow we subtract the total points he has from the points he needs to find out how many points he needs on his last test:\n\n345 - 340 = 5\n\nSo, Carl needs at least a 95 on his last test to average 85 for the class.\n\n<answer>\n95\n</answer>\n\n\n",
    "agent_opinion": {
        CK: "<compare>\nStudent #0 states that the minimum grade Carl needs is 95, but the reasoning provided is not clear and is not directly related to the question asked. Student #1 provides detailed reasoning and a correct final answer. Student #2 also provides a clear and concise reasoning process, leading to the same final answer as Student #1. Student #3 also follows a valid reasoning process, also leading to the same final answer.\n</compare>\n<explain>\nThe key comparison highlights the lack of clarity and direct relevance to the question in the reasoning provided by Student #0, alongside Student #2 and Student #3, which provide correct and detailed answers. Student #1, however, clearly follows the process to calculate the minimum grade needed and arrives at the same correct answer as the others.\n</explain>\n<identify>\nStudent #1\n</identify>\n\nNone",
        "0": "<compare>\nStudent #0 and Student #1 both correctly calculated the total points required to achieve an 85 average and determined that Carl needs at least a 95 on his last test. \nThe difference is that Student #0 expressed the total points needed as 85 * 4 = 340, while Student #1 clearly stated that 85 * 4 = 345 and kept the number of tests consistent. This difference is irrelevant to the correctness of the calculation and can be disregarded.\nBoth answers are concise and directly related to the question.\n</compare>\n\n<explain>\nBoth Student #0 and Student #1 correctly calculated the total points Carl needs to achieve an 85 average for the class. They arrived at the answer of 95 without any errors.\n</explain>\n\n<identify>\nEither Student #0 or Student #1 is correct. Since neither answer is incorrect, the decision decides based on other specific criteria that would not be decided by comparing correctness alone.\n</identify>\n\n<identify>\nNone\n</identify>\n\nNone of the answers provided is incorrect. Both Student #0 and Student #1 correctly calculated the total points Carl needs to achieve an 85 average and determined that he needs at least a 95 on his last test.",
    },
}

STAGE_3_OUTPUTS = {
    CK: {
        "question": "Carl is taking a class where the whole grade is based on four tests that are graded out of 100. He got an 80, a 75 and a 90 on his first three tests. If he wants an 85 average for the class, what is the minimum grade he needs to get on his last test?",
        "answer": "95",
        "stage3_prompt": "The question we were given is: Carl is taking a class where the whole grade is based on four tests that are graded out of 100. He got an 80, a 75 and a 90 on his first three tests. If he wants an 85 average for the class, what is the minimum grade he needs to get on his last test?  \n\nThe following answers to this question were suggested: \n<student>Student #0</student> said \nTo find the minimum grade Carl needs on his last test to achieve an 85 average, we first calculate the total points he needs to achieve this average over four tests. The formula to calculate the total points needed for an average is:\n\n\\[ \\text{Total Points Needed} = \\text{Average} \\times \\text{Number of Tests} \\]\n\nSubstituting the given values:\n\n\\[ \\text{Total Points Needed} = 85 \\times 4 = 340 \\]\n\nNow, we need to sum up the points he has from his first three tests:\n\n\\[ \\text{Total Points from First Three Tests} = 80 + 75 + 90 = 245 \\]\n\nTo find the points he needs on his last test, we subtract the points from his first three tests from the total points needed:\n\n\\[ \\text{Points Needed on Last Test} = \\text{Total Points Needed} - \\text{Total Points from First Three Tests} \\]\n\n\\[ \\text{Points Needed on Last Test} = 340 - 245 = 95 \\]\n\nTherefore, Carl needs to score at least 95 on his last test to achieve an 85 average for the class.\n\n<answer>\n95\n</answer>\n\n\n<student>Student #1</student> said \nthink: Let's calculate the total possible points Carl could have scored:\n\n80 + 75 + 90 + x = 345\n\nWhere x is the score he needs on his last test.\n\nThen, we need to figure out how many points he needs to average 85:\n\n85 * 4 = 340\n\nNow we subtract the total points he has from the points he needs to find out how many points he needs on his last test:\n\n345 - 340 = 5\n\nSo, Carl needs at least a 95 on his last test to average 85 for the class.\n\n<answer>\n95\n</answer>\n\n\n  \nAfter comparing these answers, the following feedback was given about which answer is best: \n<criticism>Criticism #0</criticism> was \nNo feedback received...\n\n\n<criticism>Criticism #1</criticism> was \n<compare>\nStudent #0 and Student #1 both correctly calculated the total points required to achieve an 85 average and determined that Carl needs at least a 95 on his last test. \nThe difference is that Student #0 expressed the total points needed as 85 * 4 = 340, while Student #1 clearly stated that 85 * 4 = 345 and kept the number of tests consistent. This difference is irrelevant to the correctness of the calculation and can be disregarded.\nBoth answers are concise and directly related to the question.\n</compare>\n\n<explain>\nBoth Student #0 and Student #1 correctly calculated the total points Carl needs to achieve an 85 average for the class. They arrived at the answer of 95 without any errors.\n</explain>\n\n<identify>\nEither Student #0 or Student #1 is correct. Since neither answer is incorrect, the decision decides based on other specific criteria that would not be decided by comparing correctness alone.\n</identify>\n\n<identify>\nNone\n</identify>\n\nNone of the answers provided is incorrect. Both Student #0 and Student #1 correctly calculated the total points Carl needs to achieve an 85 average and determined that he needs at least a 95 on his last test.\n\n\n",
        "final_agent_decision": {
            CK: "<summarize_feedback>\nStudent #0 states that the minimum grade Carl needs is 95, but the reasoning provided is not clear and is not directly related to the question asked. Student #1 provides detailed reasoning and a correct final answer. Student #2 also provides a clear and concise reasoning process, leading to the same final answer as Student #1. Student #3 also follows a valid reasoning process, also leading to the same final answer.\n</summarize_feedback>\n<majority>\nStudent #1\n</majority>\n<question>\nThe question is: Carl is taking a class where the whole grade is based on four tests that are graded out of 100. He got an 80, a 75 and a 90 on his first three tests. If he wants an 85 average for the class, what is the minimum grade he needs to get on his last test?\n</question>\n<think>\nTo solve this problem, we need to calculate the total points Carl needs to achieve an 85 average for the class. Here's the breakdown:\n\n1. Calculate the total points Carl needs to achieve an 85 average over four tests:\n\\[ \\text{Total Points Needed} = 85 \\times 4 = 340 \\]\n\n2. Calculate the total points Carl has from his first three tests:\n\\[ \\text{Total Points from First Three Tests} = 80 + 75 + 90 = 245 \\]\n\n3. Calculate the points Carl needs on his last test:\n\\[ \\text{Points Needed on Last Test} = \\text{Total Points Needed} - \\text{Total Points from First Three Tests} \\]\n\\[ \\text{Points Needed on Last Test} = 340 - 245 = 95 \\]\n\nTherefore, Carl needs to score at least 95 on his last test to achieve an 85 average for the class.\n</think>\n<answer>\n95\n</answer>"
        },
    }
}
