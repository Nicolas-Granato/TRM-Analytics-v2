from typing import Optional, Dict, Any
from fastapi import UploadFile

from src.services.audit.audit import AuditPipelineService

class AuditController:
        
    async def execute_audit_pipeline(
        self, 
        zip_files: UploadFile,
        zip_files_2: Optional[UploadFile] = None,
        fiscal_file: UploadFile = None, 
        fiscal_file_2: Optional[UploadFile] = None, 
        is_sped: bool = True
    ) -> Dict[str, Any]:
        fiscal_archive_type = "SPED" if is_sped else "Sintegra"

        if not zip_files or not zip_files.filename:
            raise ValueError("O arquivo ZIP contendo os XMLs é obrigatório.")

        if not fiscal_file or not fiscal_file.filename:
            raise ValueError(f"O arquivo fiscal {fiscal_archive_type} é obrigatório.")

        zip_bytes = await zip_files.read()
        zip_bytes_2 = await zip_files_2.read() if zip_files_2 else None
        fiscal_bytes = await fiscal_file.read()
        fiscal_bytes_2 = await fiscal_file_2.read() if fiscal_file_2 else None

        if len(zip_bytes) == 0:
            raise ValueError("O arquivo ZIP fornecido está vazio.")

        if len(fiscal_bytes) == 0:
            raise ValueError("O arquivo fiscal fornecido está vazio.")

        pipeline = AuditPipelineService(
            zip_files=zip_bytes,
            zip_files_2=zip_bytes_2,
            fiscal_file_bytes=fiscal_bytes,
            fiscal_files_bytes_2=fiscal_bytes_2,
            is_sped=is_sped
        )

        return pipeline.run_audit()