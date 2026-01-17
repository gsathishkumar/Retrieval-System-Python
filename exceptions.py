from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={
            "error": "ValueError", 
            "detail": str(exc)
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_msgs = [ (item['loc'], item['msg']) for item in exc.errors()]
    return JSONResponse(
        status_code=422,
        content={
            "error": "ValidationError", 
            "details": error_msgs
        }
    )