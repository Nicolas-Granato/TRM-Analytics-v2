import io
import time
import zipfile
import duckdb
import pandas as pd
from typing import Any, Callable, Dict, Optional
from loguru import logger

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


class AuditPipelineService:

    def __init__(
        self,
        zip_files: bytes,
        fiscal_file_bytes: bytes,
        fiscal_files_bytes_2: Optional[bytes] = None,
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
                "total_value": xml_row[1] if xml_row else 0
            },
            "fiscal_archive_metrics": {
                "total_value": sintegra_row[0] if sintegra_row else 0 
            }
        }

    def _audit_query(self, execute_sql: Callable[[str, Optional[Any]], duckdb.DuckDBPyConnection]) -> Dict[str, Any]:
        metrics = self._calculate_metrics(execute_sql)
        audit_query = AUDIT_SPED_QUERY if self._is_sped else AUDIT_SINTEGRA_QUERY
        
        df_divergencias: pd.DataFrame = execute_sql(audit_query, None).df()
        
        df_divergencias = df_divergencias.astype(object).fillna("")

        return {
            "metricas": metrics,
            "dataframe": df_divergencias.to_dict(orient="records")
        }
    
    def _parse_xml_zip(self) -> None:
        start_time = time.perf_counter()
        xml_count = 0
        
        with zipfile.ZipFile(io.BytesIO(self._zip_files)) as zf:
            for file_info in zf.infolist():
                if file_info.filename.lower().endswith(".xml") and not file_info.is_dir():
                    xml_count += 1
                    with zf.open(file_info) as xml_file:
                        xml_bytes = xml_file.read()
                        XmlParser.parse_xml(xml_bytes, self._xml_batch)

        logger.info("📦 Processados {} XMLs do arquivo ZIP em {:.2f}s", xml_count, time.perf_counter() - start_time)
        self.ddl_scripts.append(CREATE_TEMP_TABLE_XML)

    def _parse_sped(self) -> None:
        start_time = time.perf_counter()
        
        # Converte bytes para string se necessário
        sped_text = self._fiscal_file_bytes.decode("latin-1") if isinstance(self._fiscal_file_bytes, bytes) else self._fiscal_file_bytes
        SpedParser.parse_sped_content(sped_text, self._fiscal_batch)
        
        if self._fiscal_files_bytes_2:
            sped_text_2 = self._fiscal_files_bytes_2.decode("latin-1") if isinstance(self._fiscal_files_bytes_2, bytes) else self._fiscal_files_bytes_2
            SpedParser.parse_sped_content(sped_text_2, self._fiscal_batch)
            
        logger.info("📄 Parse do SPED concluído ({} registros) em {:.2f}s", len(self._fiscal_batch), time.perf_counter() - start_time)
        self.ddl_scripts.append(CREATE_TEMP_TABLE_SPED)

    def _parse_sintegra(self) -> None:
        start_time = time.perf_counter()
        sintegra_text = self._fiscal_file_bytes.decode("latin-1") if isinstance(self._fiscal_file_bytes, bytes) else self._fiscal_file_bytes
        SintegraParser.parse_sintegra(sintegra_text, self._fiscal_batch)
        
        logger.info("📄 Parse do Sintegra concluído ({} registros) em {:.2f}s", len(self._fiscal_batch), time.perf_counter() - start_time)
        self.ddl_scripts.append(CREATE_TEMP_TABLE_SINTEGRA)

    def run_audit(self) -> Dict[str, Any]:
        start_pipeline = time.perf_counter()
        logger.info("🚀 Iniciando pipeline de auditoria fiscal (Modo SPED: {})", self._is_sped)

        t0 = time.perf_counter()
        self._parse_xml_zip()
        logger.info("📦 {} XMLs parseados com sucesso em {:.2f}s", len(self._xml_batch), time.perf_counter() - t0)

        t0 = time.perf_counter()
        if self._is_sped:
            self._parse_sped()
        else:
            self._parse_sintegra()
        logger.info(
            "📄 Registros fiscais ({}) processados: {} itens em {:.2f}s",
            "SPED" if self._is_sped else "Sintegra",
            len(self._fiscal_batch),
            time.perf_counter() - t0
        )

        t0 = time.perf_counter()
        with DuckDBSession(self.ddl_scripts) as db:
            if len(self._xml_batch):
                db.executemany_sql(INSERT_XML, self._xml_batch)

            if len(self._fiscal_batch):
                insert_fiscal_archive = INSERT_SPED if self._is_sped else INSERT_SINTEGRA
                db.executemany_sql(insert_fiscal_archive, self._fiscal_batch)

            result = self._audit_query(db.execute_sql)

        logger.info("🦆 Consultas e conciliação no DuckDB concluídas em {:.2f}s", time.perf_counter() - t0)

        total_dur = time.perf_counter() - start_pipeline
        divergencias_count = len(result.get("dataframe", []))
        
        logger.success(
            "🎉 Auditoria finalizada! Divergências encontradas: {} | Tempo total: {:.2f}s",
            divergencias_count,
            total_dur
        )

        self._xml_batch.clear()
        self._fiscal_batch.clear()

        return result