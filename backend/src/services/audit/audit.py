from typing import Optional, Callable, Any, Dict
import duckdb

from src.database.queries import (
    AUDIT_SINTEGRA_QUERY, 
    AUDIT_SPED_QUERY, 
    SINTEGRA_METRICS, 
    SPED_METRICS, 
    XML_METRICS
)


class Audit:

    def __init__(
        self,
        execute_sql: Callable[[str, Optional[tuple]], duckdb.DuckDBPyConnection],
        is_sped: bool = True
    ):  
        self._execute_sql = execute_sql
        self._is_sped = is_sped

    def _calculate_metrics(self) -> Dict[str, Any]:
        xml_metrics = self._execute_sql(XML_METRICS, None).fetchall()

        query_metrics = SPED_METRICS if self._is_sped else SINTEGRA_METRICS
        fiscal_archive_metrics = self._execute_sql(query_metrics, None).fetchall()

        return {
            "xml_metrics": xml_metrics,
            "fiscal_archive_metrics": fiscal_archive_metrics
        }

    def run_audit(self) -> Dict[str, Any]:
        metrics = self._calculate_metrics()

        audit_query = AUDIT_SPED_QUERY if self._is_sped else AUDIT_SINTEGRA_QUERY
        
        df_divergencias = self._execute_sql(audit_query, None).df()

        return {
            "metricas": metrics,
            "dataframe": df_divergencias.to_dict(orient="records")
        }
    