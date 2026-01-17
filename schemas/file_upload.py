from pathlib import Path
from typing import Annotated

from fastapi import File, UploadFile
from pydantic import BaseModel, Field, field_validator, model_validator

from app_settings import settings

ALLOWED_TYPES = settings.file.allowed_file_types
MAX_FILE_SIZE = settings.file.max_file_size_in_kb
UPLOAD_DIR = Path(settings.file.upload_path)

class FileUploadSchema(BaseModel):
    # Field to accept the file itself
    input_file: Annotated[UploadFile, File(...)]
    uploaded_by: Annotated[str, 
                         Field(
                            min_length=5, 
                            max_length=20, 
                            default="admin", 
                            description="Uploaded by")
                        ]
    model_config = {"extra": "allow"}
    
    @field_validator('input_file')
    @classmethod
    def file_mandatory(cls, file: UploadFile) -> UploadFile:
        if file.size == 0:
            raise ValueError('File is missing')
        return file

    @model_validator(mode='after')
    def check_file_type_validation(self):
        if self.input_file.content_type not in ALLOWED_TYPES:
            raise ValueError(f'File Type not supported. Only {ALLOWED_TYPES} allowed.')

        if self.input_file.size > MAX_FILE_SIZE:
            raise ValueError(f"Max file size allowed : {MAX_FILE_SIZE} bytes.")

        file_path = UPLOAD_DIR / self.input_file.filename

        if Path(file_path).exists():
            raise ValueError(f"File [{self.input_file.filename}] uploaded already.")
        
        return self