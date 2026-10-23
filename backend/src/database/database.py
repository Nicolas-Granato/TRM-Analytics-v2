import duckdb
from typing import Optional, Sequence

class DuckDBSession:

    def __init__(
        self, 
        memory_limit: str = "200MB", 
        ddl_scripts: Optional[Sequence[str]] = None
    ):
        self.memory_limit = memory_limit
        self._ddl_scripts = ddl_scripts or []
        self._conn: Optional[duckdb.DuckDBPyConnection] = None

    def _close_connection(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            finally:
                self._conn = None

    def _setup_database(self) -> None:
        try:
            self._conn = duckdb.connect(":memory:")
            self._conn.execute(f"SET memory_limit = '{self.memory_limit}';")
            self._conn.execute("SET threads = 1;")

            for script in self._ddl_scripts:
                if script and script.strip():
                    self._conn.execute(script)

        except (duckdb.ParserException, duckdb.Error) as e:
            self._close_connection()
            raise RuntimeError(f"Erro ao carregar o schema do banco de dados: {e}") from e

        except Exception as e:
            self._close_connection()
            raise RuntimeError(f"Erro ao inicializar o banco de dados: {e}") from e

    def execute_SQL(self, sql: str, parameters: Optional[tuple] = None) -> None:
        if self._conn:
            try:
                self._conn.execute(sql, parameters)
            except Exception as e:
                self._close_connection()
                raise RuntimeError(f"Erro ao executar a query no banco de dados: {e}") from e

    def __enter__(self) -> "DuckDBSession":
        self._setup_database()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._close_connection()