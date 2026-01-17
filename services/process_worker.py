import asyncio
from pathlib import Path

import pandas as pd
import pdfplumber
from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from app_settings import settings
from models.chunks import ChunkInfo, DataFormat

DATABASE_URL = "postgresql+asyncpg://{}:{}@{}:{}/{}".format(
        settings.db.user,
        settings.db.password,
        settings.db.host,
        settings.db.port,
        settings.db.name
    )

def process_file(file_name: str):
  return asyncio.run(_async_worker(file_name))

async def _async_worker(file_name: str):
  UPLOAD_DIR = Path(settings.file.upload_path)
  file_path = UPLOAD_DIR / file_name
  if not file_path.exists():
    raise FileNotFoundError(f"File does not exist: {file_name}")
  
  try:
    chunks:list[dict] = extract_text_and_tables(file_path)
    vectors_list = get_vectors_as_list(chunks)
    chunks_with_embedding = [{**dic, "embedding": vector} for vector, dic in zip(vectors_list, chunks)]

    # log_chunks_for_debugging(file_name, chunks)
    engine = create_async_engine(DATABASE_URL, pool_pre_ping=True, future=True)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with SessionLocal() as session:
      await bulk_insert_async(session, chunks_with_embedding)
  except Exception as exc:
    print(exc)
    raise exc
  finally:
      await engine.dispose() # Dispose the engine

  return chunks


async def bulk_insert_async(session: AsyncSession, data: list[dict]):
  await session.run_sync(
      lambda sync_session: sync_session.bulk_insert_mappings(ChunkInfo, data)
  )
  await session.commit()

def extract_text_and_tables(file_path) -> list[dict]:
  results = []
  print(f'Extracting text and table from pdf {Path(file_path).name}')
  with pdfplumber.open(file_path) as pdf:
    for page_no, page in enumerate(pdf.pages, start=1):
      # --- Extract tables ---
      tables = page.find_tables()
      table_bboxes = [table.bbox for table in tables]

      for i, table in enumerate(tables, start=1):
        data = table.extract()
        df = pd.DataFrame(data[1:], columns=data[0])
        results.append({
          "file_name" : Path(file_path).name,
          "page_no": page_no,
          "content_type": DataFormat.TABLE,
          "content": df.to_markdown(index=False) # Converting DataFrame to text
        })

      # --- Remove table areas from text ---
      filtered_page = page
      for bbox in table_bboxes:
        filtered_page = filtered_page.outside_bbox(bbox)

      # --- Extract paragraph text and Merge Multiple lines under the paragraph as one chunk---
      text = filtered_page.extract_text()
      if text:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        for para in paragraphs:
          lines = [line.strip() for line in para.split("\n") if line.strip()]
          n = 10 # No of line to be merged as one chunk
          chunks = [lines[i:i + n] for i in range(0, len(lines), n)] # Single chunk contain more than 1 line of text
          for chunk in chunks:
            results.append({
              "file_name" : Path(file_path).name,
              "page_no": page_no,
              "content_type": DataFormat.TEXT,
              "content": " ".join(chunk)
            })
  print(f'Completed extracting text and table from pdf {Path(file_path).name}')
  return results

def log_chunks_for_debugging(file_name:str, chunks:list[dict]):
  print(f'***************  File Name[{file_name}] ***************')
  for idx, item in enumerate(chunks):
    print(f'>>>>>>>>>>>>>>Page[{item['page_no']}], Chunk-{idx}, Format[{item['content_type']}] <<<<<<<<<<<<<<<<<<<<<<<<')
    print('\n'.join(item['content']) if item['content_type'] == 'text' else item['content'])

def get_vectors_as_list(chunks = list[dict]) -> list :
  try:
    print('Connecting gemini via Genai-Client SDK --> ')
    client = genai.Client(api_key=settings.gemini_api_key)
    response = client.models.embed_content(
        model='gemini-embedding-001',
        contents= [dic["content"] for dic in chunks],
        config=types.EmbedContentConfig(output_dimensionality=1024)
    )
    print('Completed retrieving embeddings--> ')
    vectors_list = [embedding_content.values for embedding_content in response.embeddings]
    return vectors_list # Returns list of Vectors Array
  except Exception as e:
    print('-'*40, '\n' , e)
    client.close()