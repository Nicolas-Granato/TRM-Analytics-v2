import duckdb
from backend.src.database.queries import CREATE_TEMP_TABLES
from typing import Optional
from importlib.resources import files

class DuckDBSession:

    def __init__(self, memory_limits: str = "200MB"):
        self.memory_limits = memory_limits
        self._conn: Optional[duckdb.DuckDBPyConnection] = None

    @property
    def get_conn(self) -> duckdb.DuckDBPyConnection:
        if self._conn is None:
            raise RuntimeError(
                "A conexão com o banco não está ativa. Utilize a classe dentro de um bloco 'with'."
            )
        return self._conn

    def _close_connection(self):
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
            self._conn.execute(f"SET memory_limit = '{self.memory_limits}';")
            self._conn.execute("SET threads = 1;")

            if CREATE_TEMP_TABLES:
                self._conn.execute(CREATE_TEMP_TABLES)


        except (duckdb.ParserException, duckdb.Error) as e:
            self._close_connection()
            raise RuntimeError(f"Erro ao carregar o schema do banco de dados: {e}") from e

        except Exception as e:
            self._close_connection()
            raise RuntimeError(f"Erro ao inicializar o banco de dados: {e}") from e

    def __enter__(self):
        self._setup_database

    def __exit__(self, exc_type, exc, tb):
        self._close_connection
