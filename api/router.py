from fastapi import APIRouter

from .routes.data_ingestion import file_upload, trigger_analysis
from .routes.query_processing import query_search

api_router = APIRouter()
api_router.include_router(file_upload.router)
api_router.include_router(trigger_analysis.router)
api_router.include_router(query_search.router)