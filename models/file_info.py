from enum import Enum

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class FileStatus(Enum):
    READY_TO_PROCESS = "ready_to_process"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = 'failed'

class FileInfo(Base):
    __tablename__ = "file_info"

    file_id : Mapped[int] = mapped_column(Integer, primary_key=True)
    file_name: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    file_status: Mapped[FileStatus]
    file_uploaded_by: Mapped[str] = mapped_column(String(20))
    file_err_msg: Mapped[str] = mapped_column(String, nullable=True, default="")