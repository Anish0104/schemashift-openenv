from __future__ import annotations

from typing import List

from app.graders import grade_call, grade_episode
from app.models import Action, CallResult, Observation, Reward, StateResponse, StepResponse
from app.tasks.task1 import TASK1
from app.tasks.task2 import TASK2
from app.tasks.task3 import TASK3


TASK_REGISTRY = {1: TASK1, 2: TASK2, 3: TASK3}


class SchemaShiftEnv:
    def __init__(self) -> None:
        self.task_id = 1
        self.task_data = None
        self.call_results: List[CallResult] = []
        self.step_count = 0
        self.done = False
        self._prev_score = 0.0

    def reset(self, task_id: int = 1) -> Observation:
        self.task_data = TASK_REGISTRY[task_id]
        self.task_id = task_id
        self.step_count = 0
        self.done = False
        self._prev_score = 0.0
        self.call_results = [
            CallResult(call_index=index, v1_call=call)
            for index, call in enumerate(self.task_data["v1_calls"])
        ]
        return self._build_observation()

    def step(self, action: Action) -> StepResponse:
        if self.done:
            return StepResponse(
                observation=self._build_observation(),
                reward=Reward(
                    value=0.0,
                    breakdown={},
                    message="Episode already finished.",
                ),
                done=True,
                info={"warning": "step called after done"},
            )

        idx = action.call_index
        if idx < 0 or idx >= len(self.call_results):
            return StepResponse(
                observation=self._build_observation(),
                reward=Reward(
                    value=-0.05,
                    breakdown={},
                    message="Invalid call_index.",
                ),
                done=False,
                info={"error": "invalid call_index"},
            )

        if self.call_results[idx].completed:
            return StepResponse(
                observation=self._build_observation(),
                reward=Reward(
                    value=-0.05,
                    breakdown={},
                    message=f"Call {idx} already completed.",
                ),
                done=False,
                info={"warning": "already completed"},
            )

        expected = self.task_data["expected_calls"][idx]
        config = self.task_data["grading_config"]
        result = grade_call(action.rewritten_call, expected, config)

        self.call_results[idx].submitted_call = action.rewritten_call
        self.call_results[idx].score = result["total"]
        self.call_results[idx].feedback = result["feedback"]
        self.call_results[idx].completed = True

        self.step_count += 1

        new_score = grade_episode(self.call_results)
        step_reward = new_score - self._prev_score
        self._prev_score = new_score

        all_done = all(call_result.completed for call_result in self.call_results)
        step_limit_hit = self.step_count >= self.task_data["max_steps"]

        bonus = 0.0
        if all_done and new_score >= 1.0:
            bonus = 0.1
        if step_limit_hit and not all_done:
            bonus = -0.1

        final_reward = round(step_reward + bonus, 4)

        if all_done or step_limit_hit:
            self.done = True

        reward_breakdown = {
            key: value for key, value in result.items() if isinstance(value, (int, float))
        }

        return StepResponse(
            observation=self._build_observation(),
            reward=Reward(
                value=final_reward,
                breakdown=reward_breakdown,
                message=result["feedback"],
            ),
            done=self.done,
            info={
                "call_score": result["total"],
                "episode_score": new_score,
                "step": self.step_count,
            },
        )

    def state(self) -> StateResponse:
        return StateResponse(
            task_id=self.task_id,
            task_name=self.task_data["name"] if self.task_data else "none",
            step_count=self.step_count,
            current_score=grade_episode(self.call_results),
            pending_count=len([result for result in self.call_results if not result.completed]),
            total_calls=len(self.call_results),
            done=self.done,
        )

    def _build_observation(self) -> Observation:
        return Observation(
            task_id=self.task_id,
            task_name=self.task_data["name"],
            description=self.task_data["description"],
            migration_guide=self.task_data["migration_guide"],
            v1_calls=self.task_data["v1_calls"],
            call_results=self.call_results,
            pending_indices=[
                result.call_index for result in self.call_results if not result.completed
            ],
            current_score=grade_episode(self.call_results),
            step_count=self.step_count,
            max_steps=self.task_data["max_steps"],
            done=self.done,
        )
