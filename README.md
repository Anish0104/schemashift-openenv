# SchemaShift

## What SchemaShift Is

SchemaShift is an OpenEnv-style reinforcement learning environment for API migration. An agent receives a migration guide plus a batch of legacy `v1` API calls, then learns to rewrite them into the correct `v2` request shape one call at a time. Each step is graded deterministically across method, endpoint, headers, and payload so agents can earn partial credit while improving over an episode.

This makes SchemaShift useful for training and benchmarking software-engineering agents on a realistic transformation problem. The three built-in tasks scale from straightforward path and field renames to more complex auth changes, nested payload restructuring, pagination rewrites, enum normalization, and timestamp conversions.

## Tasks

| Task | Difficulty | Calls | Key Challenges |
| --- | --- | --- | --- |
| User Service Migration | Easy | 3 | Move IDs into paths, rename endpoints, rename body fields |
| Order Service Migration | Medium | 5 | Convert API-key auth to Bearer auth, move IDs into paths, build nested create-order payloads |
| Analytics Service Migration | Hard | 6 | Replace pagination scheme, rename enum values, convert timestamps, move fields between params and body |

## Action Space

Agents submit one rewrite at a time using a `call_index` plus a complete `rewritten_call` object:

```json
{
  "call_index": 1,
  "rewritten_call": {
    "method": "POST",
    "endpoint": "/v2/users",
    "headers": {
      "X-API-Key": "key_abc123",
      "Content-Type": "application/json"
    },
    "params": {},
    "body": {
      "full_name": "Alice Johnson",
      "email_address": "alice@example.com",
      "phone_number": "555-1234"
    }
  }
}
```

## Observation Space

Each observation includes the full state needed for a migration episode:

- `task_id`
- `task_name`
- `description`
- `migration_guide`
- `v1_calls`
- `call_results`
- `pending_indices`
- `current_score`
- `step_count`
- `max_steps`
- `done`

## Reward Function

Each submitted rewrite is graded with deterministic partial credit:

- Method weight: `0.20`
- Endpoint weight: `0.35`
- Headers weight: `0.20`
- Payload weight: `0.25`

Method grading is exact. Endpoints receive full credit for an exact match and partial credit for version-prefix mistakes or truncated-but-related paths. Headers score by matching required headers and values, with penalties for forbidden headers. Payload grading merges expected body and params, supports recursive partial credit for nested objects, and applies penalties for forbidden body fields or query parameters.

Episode reward is the change in average score across all calls, with a `+0.1` completion bonus for a perfect episode and a `-0.1` penalty if the step limit is reached before all calls are attempted.

## Setup — Docker

```bash
docker build -t schemashift .
docker run -p 7860:7860 schemashift
```

## Setup — Local

Use Python 3.11 locally to match the Docker image and the pinned dependency set.

```bash
pip install -r requirements.txt
uvicorn app.main:app --port 7860
```

## Running Inference

```bash
export API_BASE_URL=https://api.groq.com/openai/v1
export MODEL_NAME=llama-3.3-70b-versatile
export HF_TOKEN=your_groq_api_key
export ENV_URL=http://localhost:7860
python inference.py
```

## Environment Variables

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `API_BASE_URL` | No | `https://api.groq.com/openai/v1` | OpenAI-compatible chat completion base URL |
| `MODEL_NAME` | No | `llama-3.3-70b-versatile` | Model used by `inference.py` |
| `HF_TOKEN` | Recommended | None | Primary API key used for the OpenAI client |
| `OPENAI_API_KEY` | Fallback | None | Used only if `HF_TOKEN` is unset |
| `ENV_URL` | No | `http://localhost:7860` | Base URL for the running SchemaShift environment |

## Baseline Scores

- Task 1 (easy): `~0.85`
- Task 2 (medium): `~0.65`
- Task 3 (hard): `~0.40`
