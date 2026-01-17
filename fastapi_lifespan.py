import os
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine

from app_settings import settings


# lifespan logic
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the database engine
    url = "postgresql+asyncpg://{}:{}@{}:{}/{}".format(
        settings.db.user,
        settings.db.password,
        settings.db.host,
        settings.db.port,
        settings.db.name
    )
    print(f'URL >> {url}')
    engine = create_async_engine(url, echo=True)
    app.state.db_engine = engine
    print("Database engine initialized")

    # executor = ThreadPoolExecutor(max_workers=5)
    executor = ProcessPoolExecutor(max_workers=os.cpu_count())
    app.state.executor = executor
    print("Executor pool initialized...")

    yield  # The application runs here
    
    # Shutdown: Clean up the database engine
    await engine.dispose()
    print("Database engine closed")
    
    executor.shutdown(wait=True, cancel_futures=True)
    print("Executor Pool is shutting down.")