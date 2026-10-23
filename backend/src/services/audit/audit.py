from typing import Any, Callable, Dict, Optional, Union
import zipfile
import duckdb
import io

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

from src.database.session_manager.duckdb_session import DuckDBSession

from src.parsers.sintegra_parser import SintegraParser
from src.parsers.sped_parser import SpedParser
from src.parsers.xml_parser import XmlParser


class Audit:

    def __init__(
        self,
        zip_files: bytes,
        fiscal_file_bytes: Union[str, bytes],
        fiscal_files_bytes_2: Optional[Union[str, bytes]] = None,
        is_sped: bool = True,
    ):
        self._zip_files = zip_files
        self._fiscal_file_bytes = fiscal_file_bytes
        self._fiscal_files_bytes_2 = fiscal_files_bytes_2
        self._is_sped = is_sped
        
        self.ddl_scripts: list[str] = []
        self._xml_batch: list[tuple] = []
        self._fiscal_batch: list[tuple] = []

    def _calculate_metrics(self, execute_sql: Callable[[str, Optional[tuple]], duckdb.DuckDBPyConnection]) -> Dict[str, Any]:
        xml_metrics = execute_sql(XML_METRICS, None).fetchall()

        query_metrics = SPED_METRICS if self._is_sped else SINTEGRA_METRICS
        fiscal_archive_metrics = execute_sql(query_metrics, None).fetchall()

        return {
            "xml_metrics": xml_metrics,
            "fiscal_archive_metrics": fiscal_archive_metrics,
        }

    def _audit_query(self, execute_sql: Callable[[str, Optional[Any]], duckdb.DuckDBPyConnection]) -> Dict[str, Any]:
        metrics = self._calculate_metrics(execute_sql)

        audit_query = AUDIT_SPED_QUERY if self._is_sped else AUDIT_SINTEGRA_QUERY
        df_divergencias = execute_sql(audit_query, None).df()

        return {
            "metricas": metrics,
            "dataframe": df_divergencias.to_dict(orient="records"),
        }
    
    def _parse_xml_zip(self) -> None:
        with zipfile.ZipFile(io.BytesIO(self._zip_files)) as zf:
            for file_info in zf.infolist():
                if file_info.filename.lower().endswith(".xml") and not file_info.is_dir():
                    with zf.open(file_info) as xml_file:
                        xml_bytes = xml_file.read()
                        
                        parsed_record = XmlParser.parse_xml(xml_bytes)
                        if parsed_record:
                            self._xml_batch.append(parsed_record)

        self.ddl_scripts.append(CREATE_TEMP_TABLE_XML)

    def _parse_sped(self) -> None:
        SpedParser.parse_sped_content(self._fiscal_file_bytes, self._fiscal_batch)
        if self._fiscal_files_bytes_2:
            SpedParser.parse_sped_content(self._fiscal_files_bytes_2, self._fiscal_batch)
            
        self.ddl_scripts.append(CREATE_TEMP_TABLE_SPED)

    def _parse_sintegra(self) -> None:
        SintegraParser.parse_sintegra(self._fiscal_file_bytes, self._fiscal_batch)
        self.ddl_scripts.append(CREATE_TEMP_TABLE_SINTEGRA)

    def run_audit(self) -> Dict[str, Any]:
        if not self._zip_files:
            raise ValueError("Arquivo ZIP de XMLs não fornecido ou vazio.")

        self._parse_xml_zip()
        self._parse_sped() if self._is_sped else self._parse_sintegra()

        with DuckDBSession(self.ddl_scripts) as db:
            if self._xml_batch:
                db.executemany_sql(INSERT_XML, self._xml_batch)

            if self._fiscal_batch:
                insert_fiscal_archive = INSERT_SPED if self._is_sped else INSERT_SINTEGRA
                db.executemany_sql(insert_fiscal_archive, self._fiscal_batch)

            result = self._audit_query(db.execute_sql)

        self._xml_batch.clear()
        self._fiscal_batch.clear()

        return result