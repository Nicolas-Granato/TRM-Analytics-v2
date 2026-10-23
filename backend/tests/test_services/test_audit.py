from unittest.mock import MagicMock
import pandas as pd
import pytest

from src.database.queries import (
    AUDIT_SINTEGRA_QUERY,
    AUDIT_SPED_QUERY,
    SINTEGRA_METRICS,
    SPED_METRICS,
    XML_METRICS,
)
from src.services.audit.audit import Audit


class TestAuditComplexity:

    @pytest.fixture
    def mock_execute_sql(self):
        """Fixture que simula a injeção do método execute_sql do DuckDB."""
        return MagicMock()

    # -------------------------------------------------------------------------
    # Testes para _calculate_metrics (V(G) = 2)
    # -------------------------------------------------------------------------

    def test_calculate_metrics_sped_flow(self, mock_execute_sql):
        """Caminho 1: Calcula métricas para fluxo SPED (is_sped=True)."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            [(100, "150000.00")],
            [(98, "149000.00")],
        ]
        mock_execute_sql.return_value = mock_cursor

        audit_service = Audit(execute_sql=mock_execute_sql, is_sped=True)
        metrics = audit_service._calculate_metrics()

        mock_execute_sql.assert_any_call(XML_METRICS, None)
        mock_execute_sql.assert_any_call(SPED_METRICS, None)
        
        assert metrics["xml_metrics"] == [(100, "150000.00")]
        assert metrics["fiscal_archive_metrics"] == [(98, "149000.00")]

    def test_calculate_metrics_sintegra_flow(self, mock_execute_sql):
        """Caminho 2: Calcula métricas para fluxo Sintegra (is_sped=False)."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [
            [(50, "75000.00")], 
            [(50, "75000.00")],
        ]
        mock_execute_sql.return_value = mock_cursor

        audit_service = Audit(execute_sql=mock_execute_sql, is_sped=False)
        metrics = audit_service._calculate_metrics()

        mock_execute_sql.assert_any_call(XML_METRICS, None)
        mock_execute_sql.assert_any_call(SINTEGRA_METRICS, None)
        
        assert metrics["xml_metrics"] == [(50, "75000.00")]
        assert metrics["fiscal_archive_metrics"] == [(50, "75000.00")]

    # -------------------------------------------------------------------------
    # Testes para run_audit (V(G) = 2)
    # -------------------------------------------------------------------------

    def test_run_audit_sped_success(self, mock_execute_sql):
        """Caminho 1: Executa a auditoria completa SPED e retorna o dicionário pronto."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [[(10, 1000)], [(10, 1000)]]
        
        df_mock = pd.DataFrame([
            {
                "chave_acesso": "35231000000000000000550010000000011000000000",
                "valor_xml": 1050.0,
                "valor_fiscal": 1200.0
            }
        ])
        mock_cursor.df.return_value = df_mock
        mock_execute_sql.return_value = mock_cursor

        audit_service = Audit(execute_sql=mock_execute_sql, is_sped=True)
        result = audit_service.run_audit()

        mock_execute_sql.assert_any_call(AUDIT_SPED_QUERY, None)
        assert "metricas" in result
        assert "dataframe" in result
        assert isinstance(result["dataframe"], list)
        assert len(result["dataframe"]) == 1
        assert result["dataframe"][0]["valor_xml"] == 1050.0

    def test_run_audit_sintegra_success(self, mock_execute_sql):
        """Caminho 2: Executa a auditoria completa Sintegra sem divergências (DataFrame vazio)."""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = [[(5, 500)], [(5, 500)]]
        
        mock_cursor.df.return_value = pd.DataFrame()
        mock_execute_sql.return_value = mock_cursor

        audit_service = Audit(execute_sql=mock_execute_sql, is_sped=False)
        result = audit_service.run_audit()

        mock_execute_sql.assert_any_call(AUDIT_SINTEGRA_QUERY, None)
        assert result["dataframe"] == []