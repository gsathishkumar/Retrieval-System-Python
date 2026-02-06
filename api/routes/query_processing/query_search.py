
from fastapi import APIRouter, Depends
from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app_settings import settings
from db.dependencies import get_db_session

from models.chunks import ChunkInfo
from sqlalchemy import select

router = APIRouter(prefix="/query-processing", tags=["Search Operations"])


@router.get("/search-text", response_model=None)
async def search_text(input_query: str,
                               session: AsyncSession = Depends(get_db_session)):  # Pydantic request body via Form
  print('Connecting gemini via Genai-Client SDK --> ')
  client = genai.Client(api_key=settings.gemini_api_key)
  response = client.models.embed_content(
      model='gemini-embedding-001',
      contents= input_query,
      config=types.EmbedContentConfig(output_dimensionality=1024)
  )
  vectors_list = [embedding_content.values for embedding_content in response.embeddings]
  print('Completed retrieving embeddings--> ')

  query_vector = vectors_list[0]
  stmt = (
      select(ChunkInfo.chunk_id, ChunkInfo.file_name, ChunkInfo.page_no, ChunkInfo.content_type, ChunkInfo.content)
      .order_by(ChunkInfo.embedding.cosine_distance(query_vector))
      .limit(20)
  )
  result = await session.execute(stmt)
  response = []
  for row in result.all():
    response.append(
      {
          "chunk_id" : f'chunk_{row.chunk_id:02d}',
          "file_name" : row.file_name,
          "page_no": row.page_no,
          "content_type": row.content_type,
          "content": row.content
      }
    )

  return {'query' : input_query, 'result': response}

