# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

import asyncio

from typing import List

from llama_models.llama3.api.datatypes import Message
from termcolor import cprint

from llama_stack.apis.safety import *  # noqa: F403


class SafetyException(Exception):  # noqa: N818
    def __init__(self, violation: SafetyViolation):
        self.violation = violation
        super().__init__(violation.user_message)


class ShieldRunnerMixin:
    def __init__(
        self,
        safety_api: Safety,
        input_shields: List[str] = None,
        output_shields: List[str] = None,
    ):
        self.safety_api = safety_api
        self.input_shields = input_shields
        self.output_shields = output_shields

    async def run_shields(self, messages: List[Message], shields: List[str]) -> None:
        responses = await asyncio.gather(
            *[
                self.safety_api.run_shield(
                    shield_type=shield_type,
                    messages=messages,
                )
                for shield_type in shields
            ]
        )

        for shield, r in zip(shields, responses):
            if r.violation:
                if shield.on_violation_action == OnViolationAction.RAISE:
                    raise SafetyException(r)
                elif shield.on_violation_action == OnViolationAction.WARN:
                    cprint(
                        f"[Warn]{shield.__class__.__name__} raised a warning",
                        color="red",
                    )
