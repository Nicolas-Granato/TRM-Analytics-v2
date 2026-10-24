from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ExportExcelRequest(BaseModel):
    enterprise_name: str = Field(
        default="EMPRESA_DESCONHECIDA", 
        description="Nome da empresa auditada para constar no cabeçalho da planilha"
    )
    items: List[Dict[str, Any]] = Field(
        ..., 
        description="Lista de dicionários/JSONs contendo as linhas de divergências do cache do React"
    )
