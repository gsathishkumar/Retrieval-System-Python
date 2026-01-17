from fastapi import Request
from sqlalchemy.ext.asyncio import async_sessionmaker

async def get_db_session(request: Request):
    # Retrieve the engine stored in app.state during lifespan
    engine = request.app.state.db_engine
    
    # Create a session factory (can also be initialized once in lifespan and stored in state)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        yield session  # Provide the session to the route

