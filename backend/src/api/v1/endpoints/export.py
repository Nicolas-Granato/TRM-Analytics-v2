from fastapi import APIRouter, HTTPException, Response, status
from src.schemas.export_schema import ExportExcelRequest
from src.controllers.export_controller import ExportController

router = APIRouter()

@router.post(
    "/excel",
    status_code=status.HTTP_200_OK,
    summary="Exporta as divergências em cache para Excel (.xlsx)",
    description="Recebe o JSON de divergências armazenado no cache do Front-end e retorna o arquivo .xlsx estilizado em bytes para download."
)
async def export_excel_endpoint(payload: ExportExcelRequest):
    try:
        controller = ExportController()
        
        excel_buffer = controller.generate_excel_bytes(
            items=payload.items,
            enterprise_name=payload.enterprise_name
        )
        
        safe_enterprise_name = payload.enterprise_name.replace(" ", "_").upper()
        filename = f"Relatorio_Auditoria_{safe_enterprise_name}.xlsx"
        
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }

        return Response(
            content=excel_buffer.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )

    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao gerar o arquivo Excel: {str(e)}"
        )