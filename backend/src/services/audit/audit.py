from typing import Optional, Callable, Any, Dict
import zipfile
import duckdb
import io

from src.database.queries import (
    AUDIT_SINTEGRA_QUERY, 
    AUDIT_SPED_QUERY, 
    INSERT_SINTEGRA,
    INSERT_SPED,
    INSERT_XML,
    SINTEGRA_METRICS, 
    SPED_METRICS, 
    XML_METRICS
)

from src.parsers.sintegra_parser import SintegraParser
from src.parsers.sped_parser import SpedParser
from src.parsers.xml_parser import XmlParser


class Audit:

    def __init__(
        self,
        _zip_files: bytes,
        _fiscal_file_bytes: str,
        _fiscal_files_bytes_2: Optional[str],
        _execute_sql: Callable[[str, Optional[tuple]], duckdb.DuckDBPyConnection],
        _is_sped: bool = True
    ):  
        self._zip_files = _zip_files
        self._fiscal_file_bytes = _fiscal_file_bytes
        self._fiscal_files_bytes_2 = _fiscal_files_bytes_2
        self._execute_sql = _execute_sql
        self._is_sped = _is_sped
        self._xml_batch: list[tuple] = []
        self._fiscal_batch: list[tuple] = []

    def _calculate_metrics(self) -> Dict[str, Any]:
        xml_metrics = self._execute_sql(XML_METRICS, None).fetchall()

        query_metrics = SPED_METRICS if self._is_sped else SINTEGRA_METRICS
        fiscal_archive_metrics = self._execute_sql(query_metrics, None).fetchall()

        return {
            "xml_metrics": xml_metrics,
            "fiscal_archive_metrics": fiscal_archive_metrics
        }

    def _process_xml_zip(self):
        with zipfile.ZipFile(io.BytesIO(self._zip_files)) as zf:
            for file_info in zf.infolist():
                if file_info.filename.lower().endswith(".xml") and not file_info.is_dir():
                    with zf.open(file_info) as xml_file:
                        xml_bytes = xml_file.read()
                        XmlParser.parse_xml(xml_bytes, self._xml_batch)
                if len(self._xml_batch) >= 2000:
                    self._execute_sql(INSERT_XML, self._xml_batch)
                    self._xml_batch.clear()
        if len(self._fiscal_batch):
            self._execute_sql(INSERT_XML, self._xml_batch)

    def _process_sped(self):
        SpedParser.parse_sped_content(self._fiscal_file_bytes, self._fiscal_batch)
        if self._fiscal_files_bytes_2:
            SpedParser.parse_sped_content(self._fiscal_files_bytes_2, self._fiscal_batch)

        self._execute_sql(INSERT_SPED, self._fiscal_batch) 

    def _process_sintegra(self):
        SintegraParser.parse_sintegra(self._fiscal_file_bytes, self._fiscal_batch)

        self._execute_sql(INSERT_SINTEGRA, self, self._fiscal_batch)

    def _audit_query(self) -> Dict[str, Any]:
        metrics = self._calculate_metrics()

        audit_query = AUDIT_SPED_QUERY if self._is_sped else AUDIT_SINTEGRA_QUERY
        
        df_divergencias = self._execute_sql(audit_query, None).df()

        return {
            "metricas": metrics,
            "dataframe": df_divergencias.to_dict(orient="records")
        }

    def run_audit(self) -> Dict[str,Any]:
        if not self._zip_files:
            raise FileExistsError("Arquivos xmls não encontrados.")

        self._process_xml_zip()

        if self._is_sped:
            self._process_sped()

        else: 
            self._process_sintegra
            
        return self._audit_query()