import argparse

import uvicorn
from app.main import app


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the SchemaShift environment server.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    uvicorn.run(
        "server.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
