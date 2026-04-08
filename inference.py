from __future__ import annotations

import json
import os

import requests
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY")
ENV_URL = os.getenv("ENV_URL", "http://localhost:7860").rstrip("/")

MAX_STEPS = 15
SUCCESS_SCORE_THRESHOLD = 0.5

TASK_NAMES = {
    1: "User Service Migration",
    2: "Order Service Migration",
    3: "Analytics Service Migration",
}
BENCHMARK = "schemashift"


def log_start(task: str, env: str, model: str):
    print(f"[START]", flush=True)
    print(f"task={task}", flush=True)
    print(f"env={env}", flush=True)
    print(f"model={model}", flush=True)
    print(f"[/START]", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error=None):
    print(f"[STEP]", flush=True)
    print(f"step={step}", flush=True)
    print(f"action={action}", flush=True)
    print(f"reward={reward}", flush=True)
    print(f"done={done}", flush=True)
    print(f"error={error}", flush=True)
    print(f"[/STEP]", flush=True)


def log_end(success: bool, steps: int, score: float, rewards: list):
    print(f"[END]", flush=True)
    print(f"success={success}", flush=True)
    print(f"steps={steps}", flush=True)
    print(f"score={score}", flush=True)
    print(f"rewards={rewards}", flush=True)
    print(f"[/END]", flush=True)


def _build_prompt(obs: dict) -> str:
    pending_calls = [
        {"call_index": index, "v1_call": obs["v1_calls"][index]}
        for index in obs["pending_indices"]
    ]
    previous_results = [
        {
            "index": result["call_index"],
            "score": result["score"],
            "feedback": result["feedback"],
        }
        for result in obs["call_results"]
        if result["completed"]
    ]
    return f"""You are an API migration agent. Rewrite ONE v1 API call to v2 format.

Migration Guide:
{obs["migration_guide"]}

All v1 calls:
{json.dumps(pending_calls, indent=2)}

Pending call indices: {obs["pending_indices"]}

Previous results:
{json.dumps(previous_results, indent=2)}

Choose exactly one pending call_index from the list above and rewrite that call.
The call_index must be one of: {obs["pending_indices"]}
Respond with ONLY valid JSON, no explanation, no markdown:
{{
  "call_index": <int>,
  "rewritten_call": {{
    "method": "<GET|POST|PUT|DELETE|PATCH>",
    "endpoint": "<full path e.g. /v2/users/42>",
    "headers": {{"<key>": "<value>"}},
    "params": {{"<key>": "<value>"}},
    "body": {{}}
  }}
}}"""


def _clean_model_output(raw: str) -> str:
    return raw.replace("```json", "").replace("```JSON", "").replace("```", "").strip()


def _normalize_action(action: dict, pending_indices: list[int]) -> dict:
    normalized = dict(action)
    call_index = normalized.get("call_index")

    if call_index in pending_indices:
        return normalized

    if isinstance(call_index, int) and 0 <= call_index < len(pending_indices):
        normalized["call_index"] = pending_indices[call_index]

    return normalized


def _request_model_action(prompt: str) -> dict:
    if not API_KEY:
        raise RuntimeError("Missing HF_TOKEN or OPENAI_API_KEY.")

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=500,
    )
    raw = (response.choices[0].message.content or "").strip()
    clean = _clean_model_output(raw)
    return json.loads(clean)


def _post_json(path: str, payload: dict) -> dict:
    response = requests.post(f"{ENV_URL}{path}", json=payload, timeout=30)
    response.raise_for_status()
    return response.json()


def run_task(task_id: int) -> None:
    task_name = TASK_NAMES[task_id]
    rewards = []
    steps_taken = 0
    score = 0.0
    obs = None
    reset_error = None

    try:
        obs = _post_json("/reset", {"task_id": task_id})
    except Exception as exc:
        reset_error = f"reset failed: {exc}"

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    if reset_error:
        log_step(step=0, action="reset_error", reward=0.0, done=False, error=reset_error)
        log_end(success=False, steps=steps_taken, score=score, rewards=rewards)
        print(f"\nTask {task_id} final score: {score:.4f}\n", flush=True)
        return

    for step in range(1, MAX_STEPS + 1):
        if obs["done"]:
            break

        prompt = _build_prompt(obs)

        try:
            action = _request_model_action(prompt)
            action = _normalize_action(action, obs["pending_indices"])
        except json.JSONDecodeError:
            log_step(
                step=step,
                action="parse_error",
                reward=0.0,
                done=False,
                error="JSON parse failed",
            )
            continue
        except Exception as exc:
            log_step(
                step=step,
                action="model_error",
                reward=0.0,
                done=False,
                error=f"LLM request failed: {exc}",
            )
            break

        try:
            result = _post_json("/step", action)
        except Exception as exc:
            log_step(
                step=step,
                action=json.dumps(action, sort_keys=True),
                reward=0.0,
                done=False,
                error=f"step request failed: {exc}",
            )
            break

        reward = result["reward"]["value"]
        done = result["done"]
        obs = result["observation"]

        rewards.append(reward)
        steps_taken = step

        log_step(
            step=step,
            action=json.dumps(action, sort_keys=True),
            reward=reward,
            done=done,
            error=None,
        )

        if done:
            break

    max_total_reward = 1.0
    score = sum(rewards) / max_total_reward if max_total_reward > 0 else 0.0
    score = min(max(score, 0.0), 1.0)
    success = score >= SUCCESS_SCORE_THRESHOLD

    log_end(success=success, steps=steps_taken, score=score, rewards=rewards)
    print(f"\nTask {task_id} final score: {score:.4f}\n", flush=True)


def main() -> None:
    for task_id in [1, 2, 3]:
        try:
            run_task(task_id)
        except Exception as exc:
            log_start(task=TASK_NAMES[task_id], env=BENCHMARK, model=MODEL_NAME)
            log_step(
                step=0,
                action="task_error",
                reward=0.0,
                done=False,
                error=f"Unexpected task failure: {exc}",
            )
            log_end(success=False, steps=0, score=0.0, rewards=[])
            print(f"\nTask {task_id} final score: 0.0000\n", flush=True)


if __name__ == "__main__":
    main()
