import re
from datetime import datetime
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
        
        mes_ano = ""
        if payload.items and len(payload.items) > 0:
            first_item = payload.items[0]
            item_dict = first_item if isinstance(first_item, dict) else first_item.dict()
            date_str = (
                item_dict.get("xml_emission_date") 
                or item_dict.get("sped_emission_date") 
                or item_dict.get("sintegra_emission_date")
            )
            if date_str and len(str(date_str)) >= 7:
                parts = str(date_str).split("-")
                if len(parts) >= 2:
                    mes_ano = f"{parts[1]}_{parts[0]}"

        if not mes_ano:
            mes_ano = datetime.now().strftime("%m_%Y")

        raw_company = (payload.enterprise_name or "EMPRESA_DESCONHECIDA").strip().upper()
        clean_company = re.sub(r"[^\w\s-]", "", raw_company)
        safe_company_name = re.sub(r"[-\s]+", "_", clean_company).strip("_") or "EMPRESA_DESCONHECIDA"

        filename = f"relatorio_{mes_ano}_{safe_company_name}.xlsx"
        
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Access-Control-Expose-Headers': 'Content-Disposition'
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