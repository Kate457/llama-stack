# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.
import re

from llama_stack.apis.evals import *  # noqa: F403

# from llama_stack.distribution.registry.tasks.task import BaseTask

QUERY_TEMPLATE_MULTICHOICE = """
Answer the following multiple choice question and make the answer very simple. The last line of your response should be of the following format: 'Answer: $LETTER' (without quotes) where LETTER is one of ABCD.

{Question}

A) {A}
B) {B}
C) {C}
D) {D}
""".strip()

MULTILINGUAL_ANSWER_REGEXES = [
    r"Answer\s*:",
    r"Answer\s*:​​​​​​",  # Korean invisible character
    r"উত্তর\s*:",
    r"उत्तर\s*:",
    r"উত্তরঃ",
    r"উত্তর\s*:",
    r"Antwort\s*:",
    r"답변\s*:",
    r"정답\s*:",
    r"답\s*:",
    r"答案\s*：",
    r"答案\s*:",
    r"答\s*：",
    r"答\s*:",
    r"答复\s*：",
    r"答曰\s*：",
    r"الإجابة:",
    r"الجواب:",
    r"إجابة:",
    r"الإجابة النهائية:",
    r"الإجابة الصحيحة:",
    r"الإجابة الصحيحة هي:",
    r"الإجابة هي:",
    r"Respuesta\s*:",
    r"Risposta\s*:",
    r"答え\s*:",
    r"答え\s*：",
    r"回答\s*:",
    r"回答\s*：",
    r"解答\s*:",
    r"Jawaban\s*:",
    r"Réponse\s*:",
    r"Resposta\s*:",
    r"Jibu\s*:",
    r"Idahun\s*:",
    r"Ìdáhùn\s*:",
    r"Idáhùn\s*:",
    r"Àmọ̀nà\s*:",
    r"Àdáhùn\s*:",
    r"Ànúgọ\s*:",
    r"Àṣàyàn\s*:",
]

MULTILINGUAL_ANSWER_PATTERN_TEMPLATE = (
    r"(?i){}\s*([A-D]|[أ-د]|[অ]|[ব]|[ড]|[ঢ]|[Ａ]|[Ｂ]|[Ｃ]|[Ｄ])"
)


def normalize_response(response: str) -> str:
    """
    Normalize the response by removing markdown and LaTeX formatting that may prevent a match.
    """

    return (
        response.replace("**", "")
        .replace("$\\boxed{", "")
        .replace("}$", "")
        .replace("\\$", "")
        .replace("$\\text{", "")
        .replace("$", "")
        .replace("\\mathrm{", "")
        .replace("\\{", "")
        .replace("\\text", "")
        .replace("\\(", "")
        .replace("\\mathbf{", "")
        .replace("{", "")
        .replace("\\boxed", "")
    )


def normalize_extracted_answer(extracted_answer: str) -> str:
    return (
        # In arabic these are the letters used for A-D in multiple choice questions
        extracted_answer.replace("أ", " A")
        .replace("ب", " B")
        .replace("ج", " C")
        .replace("د", " D")
        # In Bengali these are the letters used for A-D in multiple choice questions
        .replace("অ", " A")
        .replace("ব", " B")
        .replace("ড", " C")
        .replace("ঢ", " D")
        # In Japanese these are the letters sometimes used for A-D in multiple choice questions
        .replace("Ａ", " A")
        .replace("Ｂ", " B")
        .replace("Ｃ", " C")
        .replace("Ｄ", " D")
        .strip()
    )


class MMLUTask(BaseTask[DictSample, ProcessedDictSample]):
    """
    MMLU Task.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def preprocess_sample(self, sample: ProcessedDictSample) -> ProcessedDictSample:
        content = QUERY_TEMPLATE_MULTICHOICE.format(**sample.data)
        preprocessed = {
            "messages": [
                {
                    "role": "user",
                    "content": content,
                }
            ],
        }
        processed_sample = ProcessedDictSample(
            data=sample.data,
            preprocessed=preprocessed,
        )
        return processed_sample

    def postprocess_sample(self, sample: ProcessedDictSample) -> ProcessedDictSample:
        if not sample.postprocessed:
            sample.postprocessed = {}
        sample.postprocessed["postprocessed"] = normalize_response(
            sample.prediction.completion_message
        )
        return sample

    def score_sample(self, sample: ProcessedDictSample) -> SingleEvalResult:
        postprocessed_output = sample.postprocessed["postprocessed"]
        expected_answer = sample.data["Answer"]

        extracted_answer = None
        for answer_regex in MULTILINGUAL_ANSWER_REGEXES:
            regex = MULTILINGUAL_ANSWER_PATTERN_TEMPLATE.format(answer_regex)
            match = re.search(regex, postprocessed_output)
            if match:
                extracted_answer = normalize_extracted_answer(match.group(1))
                break

        score = 1.0 if extracted_answer and extracted_answer == expected_answer else 0.0

        return SingleEvalResult(
            score_data={
                "score": score,
            },
        )

    def aggregate_results(self, eval_results: List[SingleEvalResult]) -> EvalResult:
        print("aggregate_results", eval_results)
        sum_score = sum([result.score_data["score"] for result in eval_results])

        return EvalResult(metrics={"score": str(sum_score / len(eval_results))})
