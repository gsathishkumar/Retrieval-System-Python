import asyncio
from asyncio import Future
from concurrent.futures import Executor

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from models.file_info import FileInfo, FileStatus

from .process_worker import process_file


async def check_file_info_exists_in_db(file_name: str, session: AsyncSession):
  statement = select(FileInfo).where( FileInfo.file_name == file_name)
  results = await session.execute(statement)
  return results.scalars().all()


async def add_file_info_in_db(file_name: str, uploaded_by: str, session: AsyncSession):
  try:
    file_info_dict = {
      'file_name' : file_name,
      'file_status' : FileStatus.READY_TO_PROCESS,
      'file_uploaded_by': uploaded_by
    }
    file_info = FileInfo(**file_info_dict)
    session.add(file_info)
    await session.commit()
    await session.refresh(file_info)
    return file_info
  except SQLAlchemyError as e:
    await session.rollback()
    raise e


async def bulk_update_async(session: AsyncSession, data: list[dict]):
  await session.run_sync(
      lambda sync_session: sync_session.bulk_update_mappings(FileInfo, data)
  )
  await session.commit()


async def update_inprogress_status_and_execute_tasks(session: AsyncSession, executor: Executor, files: list[FileInfo]) -> list[Future]:
  update_data : list[dict] = []
  async_tasks : list[Future] = []
  for file in files:
    update_data.append({'file_id': file.file_id, 'file_status' : FileStatus.IN_PROGRESS});
    async_tasks.append(executor_task(executor, process_file, file.file_name))
  
  await bulk_update_async(session, update_data) # Update the file_status as IN_PROGRESS
  futures = await asyncio.gather(*async_tasks, return_exceptions=True)
  return futures


async def read_unprocessed_and_failed_records_from_db(session: AsyncSession) -> list[FileInfo] : 
  statement = select(FileInfo).where(
    FileInfo.file_status.in_([
        FileStatus.READY_TO_PROCESS, FileStatus.FAILED
    ])
  )
  results = await session.execute(statement)
  return results.scalars().all()


async def update_status_as_completed_or_failed(futures: list[Future], session: AsyncSession, files: list[FileInfo]) -> list[dict] :
  update_data : list[dict] = []
  for idx, task_result in enumerate(futures):
    if isinstance(task_result, Exception):
        update_data.append({
          'file_id': files[idx].file_id, 
          'file_status' : FileStatus.FAILED, 
          'file_err_msg': f'{str(task_result)}'
          });
    else:
        update_data.append({
          'file_id': files[idx].file_id, 
          'file_status' : FileStatus.COMPLETED,
          'file_err_msg': ''
          });
  else:
    await bulk_update_async(session, update_data) # Update the file_status as FAILED OR COMPLETED
  return update_data


async def executor_task(executor: Executor, fn, *args):
  loop = asyncio.get_running_loop()
  return await loop.run_in_executor(executor, fn, *args)