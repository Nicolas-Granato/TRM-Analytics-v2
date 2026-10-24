import pytest

from src.database.session_manager.duckdb_session import DuckDBSession


class TestDuckDBSessionComplexity:

    def test_context_manager_setup_and_tear_down_success(self):
        """Valida se o gerenciador de contexto abre a conexão e executa scripts DDL."""
        ddl_scripts = [
            "CREATE TEMP TABLE test_tb (id INT, name VARCHAR);",
            "INSERT INTO test_tb VALUES (1, 'TRM Analytics');"
        ]

        with DuckDBSession(ddl_scripts) as session:
            res = session.execute_sql("SELECT name FROM test_tb WHERE id = 1;").fetchone()
            assert res is not None
            assert res[0] == "TRM Analytics"
            assert session._conn is not None

        assert session._conn is None

    def test_setup_database_handles_duckdb_parser_error(self):
        """Valida tratamento de erro de sintaxe nos scripts DDL no startup."""
        invalid_ddl = ["CREATE INVALID SYNTAX TABLE;"]

        with pytest.raises(RuntimeError) as exc_info:
            with DuckDBSession(invalid_ddl):
                pass

        assert "Erro ao carregar o schema do banco de dados" in str(exc_info.value)

    def test_execute_sql_raises_when_no_active_connection(self):
        """Garante exceção amigável caso se tente executar SQL fora do contexto with."""
        session = DuckDBSession()
        
        with pytest.raises(RuntimeError) as exc_info:
            session.execute_sql("SELECT 1;")

        assert "Conexão com o DuckDB não está ativa" in str(exc_info.value)

    def test_executemany_sql_success_and_batch_insertion(self):
        """Testa inserções em lote utilizando executemany_sql."""
        ddl = ["CREATE TEMP TABLE batch_tb (id INT, val BIGINT);"]
        data_batch = [(1, 100), (2, 200), (3, 300)]

        with DuckDBSession(ddl) as session:
            session.executemany_sql("INSERT INTO batch_tb VALUES (?, ?);", data_batch)
            count = session.execute_sql("SELECT COUNT(*) FROM batch_tb;").fetchone()[0]
            assert count == 3

    def test_close_connection_on_query_execution_error(self):
        """Garante fechamento e liberação de conexão se uma query falhar no meio do processo."""
        ddl = ["CREATE TEMP TABLE error_tb (id INT);"]

        with pytest.raises(RuntimeError) as exc_info:
            with DuckDBSession(ddl) as session:
                session.execute_sql("SELECT * FROM tabela_inexistente;")

        assert "Erro ao executar a query no banco de dados" in str(exc_info.value)
        assert session._conn is None