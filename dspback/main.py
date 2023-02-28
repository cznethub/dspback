import asyncio
import logging

import uvicorn as uvicorn

from dspback.api import app as app_fastapi
from dspback.scheduler import app as app_rocketry


class Server(uvicorn.Server):
    def handle_exit(self, sig: int, frame) -> None:
        app_rocketry.session.shut_down()
        return super().handle_exit(sig, frame)


async def main():
    "Run Rocketry and FastAPI"
    server = Server(config=uvicorn.Config(app_fastapi, workers=1, loop="asyncio", host="0.0.0.0", port=5002))

    api = asyncio.create_task(server.serve())
    sched = asyncio.create_task(app_rocketry.serve())

    await asyncio.wait([sched, api])


if __name__ == "__main__":
    # Print Rocketry's logs to terminal
    logger = logging.getLogger("rocketry.task")
    logger.addHandler(logging.StreamHandler())

    # Run both applications
    asyncio.run(main())
