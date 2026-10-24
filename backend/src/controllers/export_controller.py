import io
import pandas as pd
from typing import List, Dict, Any
from src.services.export.export_excel import ExcelExport

class ExportController:

    def generate_excel_bytes(self, items: List[Dict[str, Any]], enterprise_name: str) -> io.BytesIO:
        if not items or len(items) == 0:
            raise ValueError("A lista de divergências no cache está vazia. Nenhum dado para exportar.")

        df_results = pd.DataFrame(items)

        exporter = ExcelExport(enterprise_name=enterprise_name)
        return exporter.export_dataframe_to_bytes(df_results)
    