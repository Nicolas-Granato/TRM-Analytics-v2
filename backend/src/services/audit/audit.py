from src.database.queries import AUDIT_SINTEGRA_QUERY, AUDIT_SPED_QUERY, SINTEGRA_METRICS, SPED_METRICS, XML_METRICS

from typing import Optional
import duckdb
import ctypes
import sys
import os

class Audit:

    def __init__(
            self,
            execute_sql: callable[str, tuple | None],
            is_sped: bool = True,
            conn: Optional[duckdb.DuckDBPyConnection] = None
        ):  
        self.execute_sql = execute_sql
        self.is_sped = is_sped
        self.conn = conn

    @staticmethod
    def _set_low_process_priority() -> None:
        try:
            if sys.platform == "win32":
                BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
                handle = ctypes.windll.kernel32.GetCurrentProcess()
                ctypes.windll.kernel32.SetPriorityClass(handle, BELOW_NORMAL_PRIORITY_CLASS)
            else:
                os.nice(10)
        except Exception as e:
            print(f"Falha ao ajustar a prioridade do processo: {e}")

    def _calculate_metrics(self):
        xml_metrics = self.execute_sql(XML_METRICS)

        if self.is_sped:
            sped_metrics = self.execute_sql(SPED_METRICS)
            return {
                "xml_metrics": xml_metrics,
                "sped_metrics": sped_metrics
            }

        sintegra_metrics = self.execute_sql(SINTEGRA_METRICS)

        return {
            "xml_metrics": xml_metrics,
            "sintegra_metrics": sintegra_metrics
        }

    def _sped_audit(self):
        if self.is_sped:
            self.execute_sql(AUDIT_SPED_QUERY)

        return {
            
        }

    def run_audit(self):
        return


    

        
        
        
