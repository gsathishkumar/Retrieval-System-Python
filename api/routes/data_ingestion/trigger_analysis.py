from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from db.dependencies import get_db_session
from services import data_ingestion_service as service

router = APIRouter(prefix="/data-ingest", tags=["File Operations"])

@router.get("/process-files", response_model=None)
async def process_files(request: Request, session: AsyncSession = Depends(get_db_session)):
  files = await service.read_unprocessed_and_failed_records_from_db(session)
  if not files:
    return {"message" : 'No Files available to process..'}
  futures = await service.update_inprogress_status_and_execute_tasks(session, request.app.state.executor, files)
  update_data = await service.update_status_as_completed_or_failed(futures,session, files)
  return {"message": 'Files Processed', 'details': update_data}