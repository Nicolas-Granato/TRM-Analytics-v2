from typing import Optional, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status

from src.controllers.audit_controller import AuditController

router = APIRouter()

@router.post(
    "/run",
    status_code=status.HTTP_200_OK,
    response_model=dict[str, Any],
    summary="Executa a auditoria fiscal",
    description="Recebe o arquivo .ZIP com os XMLs e os arquivos fiscais (SPED/Sintegra) para processamento em memória."
)
async def run_audit(
    zip_files: UploadFile = File(
        ...,
        description="Arquivo .ZIP contendo as notas fiscais em formato XML."
    ),
    fiscal_file: UploadFile = File(
        ...,
        description="Arquivo fiscal principal (SPED Fiscal ou Sintegra)."
    ),
    fiscal_file_2: Optional[UploadFile] = File(
        default=None,
        description="Arquivo fiscal SPED Cofins, sendo opcional para o cruzamento."
    ),
    is_sped: bool = Form(
        default=True,
        description="O front-end passará True para auditoria SPED e False para Sintegra."
    )
):
    try:
        controller = AuditController()

        result = await controller.execute_audit_pipeline(
            zip_files=zip_files,
            fiscal_file=fiscal_file,
            fiscal_file_2=fiscal_file_2,
            is_sped=is_sped
        )

        return result

    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno no processamento da auditoria: {str(e)}"
        )