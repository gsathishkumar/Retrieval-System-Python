from enum import Enum
from typing import List

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class DataFormat(Enum):
    TEXT = "text"
    TABLE = "table"

class ChunkInfo(Base):
    __tablename__ = "chunk_info"

    chunk_id : Mapped[int] = mapped_column(Integer, primary_key=True)
    file_name: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    page_no: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(String)
    content_type: Mapped[DataFormat]
    embedding: Mapped[List[float]] = mapped_column(VECTOR(1024), nullable=True)