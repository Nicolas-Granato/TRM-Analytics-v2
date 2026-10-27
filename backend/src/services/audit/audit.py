import io
import re
import zipfile
import duckdb
import pandas as pd
from typing import Any, Callable, Optional

from src.database.scripts.audit_queries import (
    AUDIT_SINTEGRA_QUERY,
    AUDIT_SPED_QUERY,
)
from src.database.scripts.insert_queries import (
    INSERT_SINTEGRA,
    INSERT_SPED,
    INSERT_XML,
)
from src.database.scripts.metrics_queries import (
    SINTEGRA_METRICS,
    SPED_METRICS,
    XML_METRICS,
)
from src.database.scripts.tables_queries import (
    CREATE_TEMP_TABLE_SINTEGRA,
    CREATE_TEMP_TABLE_SPED,
    CREATE_TEMP_TABLE_XML,
)
from src.database.scripts.delete_query import (
    DELETE_XML_BY_ACCESS_KEY
)
from src.database.session_manager.duckdb_session import DuckDBSession
from src.parsers.sintegra_parser import SintegraParser
from src.parsers.sped_parser import SpedParser
from src.parsers.xml_parser import XmlParser


class AuditPipelineService:

    CANCEL_EVENTS = {"canc"}

    def __init__(
        self,
        zip_files: bytes,
        zip_files_2: Optional[bytes] = None,
        fiscal_file_bytes: bytes = b"",
        fiscal_files_bytes_2: Optional[bytes] = None,
        is_sped: bool = True,
    ):
        self._zip_files = zip_files
        self._zip_files_2 = zip_files_2
        self._fiscal_file_bytes = fiscal_file_bytes
        self._fiscal_files_bytes_2 = fiscal_files_bytes_2
        self._is_sped = is_sped
        
        self.ddl_scripts: list[str] = []
        self._xml_batch: list[tuple] = []
        self._event_canc: list[tuple] = []
        self._fiscal_batch: list[tuple] = []

        self._cnpj_issuer: Optional[str] = None

    def _calculate_metrics(self, execute_sql: Callable[[str, Optional[tuple]], duckdb.DuckDBPyConnection]) -> dict[str, Any]:
        xml_row = execute_sql(XML_METRICS, None).fetchone()

        if self._is_sped:
            sped_row = execute_sql(SPED_METRICS, None).fetchone()
                
            return {
                "xml_metrics": {
                    "total_count": xml_row[0] if xml_row else 0,
                    "total_value": xml_row[1] if xml_row else 0
                },
                "fiscal_archive_metrics": {
                    "total_count": sped_row[0] if sped_row else 0,
                    "total_value": sped_row[1] if sped_row else 0
                }
            }
        
        sintegra_row = execute_sql(SINTEGRA_METRICS, None).fetchone()
                
        return {
            "xml_metrics": {
                "total_count": xml_row[0] if xml_row else 0,
                "total_value": xml_row[1] if xml_row else 0
            },
            "fiscal_archive_metrics": {
                "total_count": 0,
                "total_value": sintegra_row[0] if sintegra_row else 0 
            }
        }

    def _audit_query(self, execute_sql: Callable[[str, Optional[Any]], duckdb.DuckDBPyConnection]) -> dict[str, Any]:
        metrics = self._calculate_metrics(execute_sql)
        audit_query = AUDIT_SPED_QUERY if self._is_sped else AUDIT_SINTEGRA_QUERY
        
        df_divergencias: pd.DataFrame = execute_sql(audit_query, None).df()
        df_divergencias = df_divergencias.astype(object).fillna("")

        return {
            "metricas": metrics,
            "dataframe": df_divergencias.to_dict(orient="records")
        }

    def _parse_xml_zip(self, zip_files: bytes) -> None:
        if not zip_files:
            return

        with zipfile.ZipFile(io.BytesIO(zip_files)) as zf:
            for file_info in zf.infolist():
                filename_lower = file_info.filename.lower()
                
                if any(event in filename_lower for event in self.CANCEL_EVENTS):
                    numeros = re.findall(r"\d{44}", file_info.filename)
                    if numeros:
                        self._event_canc.append((numeros[0],))
                    continue

                if filename_lower.endswith(".xml") and not file_info.is_dir():
                    with zf.open(file_info) as xml_file:
                        xml_bytes = xml_file.read()
                        XmlParser.parse_xml(xml_bytes, self._xml_batch, self._cnpj_issuer)
    
    def _parse_xml(self) -> None:
        self._parse_xml_zip(self._zip_files)

        if self._zip_files_2:
            self._parse_xml_zip(self._zip_files_2)

        self.ddl_scripts.append(CREATE_TEMP_TABLE_XML)

    def _parse_sped(self) -> None:
        sped_text = self._fiscal_file_bytes.decode("latin-1") if isinstance(self._fiscal_file_bytes, bytes) else self._fiscal_file_bytes
        SpedParser.parse_sped_content(sped_text, self._fiscal_batch)
        self._cnpj_issuer = SpedParser.get_cnpj()
        
        if self._fiscal_files_bytes_2:
            sped_text_2 = self._fiscal_files_bytes_2.decode("latin-1") if isinstance(self._fiscal_files_bytes_2, bytes) else self._fiscal_files_bytes_2
            SpedParser.parse_sped_content(sped_text_2, self._fiscal_batch)
            
        self.ddl_scripts.append(CREATE_TEMP_TABLE_SPED)

    def _parse_sintegra(self) -> None:
        sintegra_text = self._fiscal_file_bytes.decode("latin-1") if isinstance(self._fiscal_file_bytes, bytes) else self._fiscal_file_bytes
        SintegraParser.parse_sintegra(sintegra_text, self._fiscal_batch)
        self._cnpj_issuer = SintegraParser.get_cnpj()
        
        self.ddl_scripts.append(CREATE_TEMP_TABLE_SINTEGRA)

    def run_audit(self) -> dict[str, Any]:
        if self._is_sped:
            self._parse_sped()
        else:
            self._parse_sintegra()

        self._parse_xml()

        with DuckDBSession(self.ddl_scripts) as db:
            if len(self._xml_batch):
                db.executemany_sql(INSERT_XML, self._xml_batch)

            if len(self._fiscal_batch):
                insert_fiscal_archive = INSERT_SPED if self._is_sped else INSERT_SINTEGRA
                db.executemany_sql(insert_fiscal_archive, self._fiscal_batch)

            if len(self._event_canc):
                db.executemany_sql(DELETE_XML_BY_ACCESS_KEY, self._event_canc)

            result = self._audit_query(db.execute_sql)

        self._xml_batch.clear()
        self._fiscal_batch.clear()
        self._event_canc.clear()

        return result