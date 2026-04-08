import argparse
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.environment import SchemaShiftEnv
from app.models import Action, Observation, ResetRequest, StateResponse, StepResponse


app = FastAPI(title="SchemaShift", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

env = SchemaShiftEnv()
env.reset(task_id=1)


@app.get("/")
def root():
    return {
        "name": "SchemaShift",
        "version": "1.0.0",
        "description": "API migration RL environment",
        "tasks": [1, 2, 3],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reset", response_model=Observation)
def reset(request: Optional[ResetRequest] = None):
    try:
        payload = request or ResetRequest()
        return env.reset(task_id=payload.task_id)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail="Invalid task_id") from exc


@app.post("/step", response_model=StepResponse)
def step(action: Action):
    return env.step(action)


@app.get("/state", response_model=StateResponse)
def state():
    return env.state()


def run_server() -> None:
    parser = argparse.ArgumentParser(description="Run the SchemaShift environment server.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
