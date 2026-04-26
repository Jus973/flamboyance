"""Entry point for running benchmark as module."""

import asyncio
from benchmark.run_benchmark import main

if __name__ == "__main__":
    asyncio.run(main())
