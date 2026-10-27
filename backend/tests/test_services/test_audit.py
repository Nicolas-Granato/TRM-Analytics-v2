import io
import zipfile
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from src.services.audit.audit import AuditPipelineService


class TestAuditPipelineServiceComplexity:

    @pytest.fixture
    def sample_zip_bytes(self) -> bytes:
        """Gera em memória um arquivo ZIP válido contendo XMLs normais e de cancelamento."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zf:
            zf.writestr("35231000000000000000550010000000011000000000-nfe.xml", "<nfeProc></nfeProc>")
            zf.writestr("12345678901234567890123456789012345678901234-canc.xml", "<procEventoNFe></procEventoNFe>")
            zf.writestr("leia-me.txt", "Texto irrelevante")
            zf.writestr("pasta_xml/", "")
        return buffer.getvalue()

    @pytest.fixture
    def mock_duckdb_session(self):
        """Moca a sessão do DuckDB e seus métodos de execução SQL."""
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_db.execute_sql.return_value = mock_cursor
        return mock_db, mock_cursor

    # -------------------------------------------------------------------------
    # Testes para _parse_xml_zip e _parse_xml
    # -------------------------------------------------------------------------

    @patch("src.services.audit.audit.XmlParser.parse_xml")
    def test_parse_xml_zip_success_and_cancellation_event(
        self, mock_parse_xml, sample_zip_bytes
    ):
        """Testa o parsing de ZIP separando XMLs comuns de eventos de cancelamento."""
        service = AuditPipelineService(
            zip_files=sample_zip_bytes, fiscal_file_bytes=b"content"
        )
        service._parse_xml()

        assert mock_parse_xml.call_count == 1
        assert len(service._event_canc) == 1
        assert service._event_canc[0] == ("12345678901234567890123456789012345678901234",)
        assert "CREATE TEMP TABLE IF NOT EXISTS xml" in service.ddl_scripts[0]

    @patch("src.services.audit.audit.XmlParser.parse_xml")
    def test_parse_xml_with_secondary_zip(self, mock_parse_xml, sample_zip_bytes):
        """Testa o processamento quando um segundo arquivo ZIP é fornecido."""
        service = AuditPipelineService(
            zip_files=sample_zip_bytes,
            zip_files_2=sample_zip_bytes,
            fiscal_file_bytes=b"content",
        )
        service._parse_xml()

        assert mock_parse_xml.call_count == 2
        assert len(service._event_canc) == 2

    # -------------------------------------------------------------------------
    # Testes para _parse_sped e _parse_sintegra
    # -------------------------------------------------------------------------

    @patch("src.services.audit.audit.SpedParser.get_cnpj", return_value="12345678000195")
    @patch("src.services.audit.audit.SpedParser.parse_sped_content")
    def test_parse_sped_single_and_multiple_files(
        self, mock_parse_sped, mock_get_cnpj
    ):
        """Testa o parsing de SPED com 1 e 2 arquivos fiscais em bytes e string."""
        service = AuditPipelineService(
            zip_files=b"",
            fiscal_file_bytes=b"sped_1",
            fiscal_files_bytes_2="sped_2",
            is_sped=True,
        )
        service._parse_sped()

        assert mock_parse_sped.call_count == 2
        assert service._cnpj_issuer == "12345678000195"
        assert "CREATE TEMP TABLE IF NOT EXISTS sped" in service.ddl_scripts[0]

    @patch("src.services.audit.audit.SintegraParser.get_cnpj", return_value="12345678000195")
    @patch("src.services.audit.audit.SintegraParser.parse_sintegra")
    def test_parse_sintegra_flow(self, mock_parse_sintegra, mock_get_cnpj):
        """Testa a chamada do parser Sintegra com extração de CNPJ."""
        service = AuditPipelineService(
            zip_files=b"", fiscal_file_bytes=b"sintegra_content", is_sped=False
        )
        service._parse_sintegra()

        mock_parse_sintegra.assert_called_once_with("sintegra_content", service._fiscal_batch)
        assert service._cnpj_issuer == "12345678000195"
        assert "CREATE TEMP TABLE IF NOT EXISTS sintegra" in service.ddl_scripts[0]

    # -------------------------------------------------------------------------
    # Testes para _calculate_metrics
    # -------------------------------------------------------------------------

    def test_calculate_metrics_sped_with_data(self):
        """Fluxo SPED com métricas retornadas do banco."""
        mock_execute = MagicMock()
        mock_cursor_xml = MagicMock()
        mock_cursor_xml.fetchone.return_value = (10, 150000)
        mock_cursor_sped = MagicMock()
        mock_cursor_sped.fetchone.return_value = (8, 140000)

        mock_execute.side_effect = [mock_cursor_xml, mock_cursor_sped]

        service = AuditPipelineService(b"", b"", is_sped=True)
        metrics = service._calculate_metrics(mock_execute)

        assert metrics["xml_metrics"] == {"total_count": 10, "total_value": 150000}
        assert metrics["fiscal_archive_metrics"] == {"total_count": 8, "total_value": 140000}

    def test_calculate_metrics_sintegra_with_none_rows(self):
        """Fluxo Sintegra com fetchone retornando None (tratamento de null)."""
        mock_execute = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_execute.return_value = mock_cursor

        service = AuditPipelineService(b"", b"", is_sped=False)
        metrics = service._calculate_metrics(mock_execute)

        assert metrics["xml_metrics"] == {"total_count": 0, "total_value": 0}
        assert metrics["fiscal_archive_metrics"] == {"total_count": 0, "total_value": 0}

    # -------------------------------------------------------------------------
    # Testes do Pipeline Completo run_audit
    # -------------------------------------------------------------------------

    @patch("src.services.audit.audit.DuckDBSession")
    @patch.object(AuditPipelineService, "_parse_xml")
    @patch.object(AuditPipelineService, "_parse_sped")
    def test_run_audit_sped_full_success_with_deletes(
        self, mock_parse_sped, mock_parse_xml, mock_duckdb_cls
    ):
        """Testa fluxo completo com inserções de SPED, XML e deleções de notas canceladas."""
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_duckdb_cls.return_value.__enter__.return_value = mock_db
        mock_db.execute_sql.return_value = mock_cursor
        inserted_batches = []
        mock_db.executemany_sql.side_effect = lambda query, batch: inserted_batches.append((query, list(batch)))
        mock_cursor.fetchone.side_effect = [(1, 100), (1, 100)]
        mock_cursor.df.return_value = pd.DataFrame(
            [{"access_key": "3523...", "divergence_type": "DIVERGENCIA_DE_VALOR"}]
        )

        service = AuditPipelineService(b"zip", b"sped", is_sped=True)
        xml_tuple = ("key", "cnpj", 100, "1", "1", "2023-01-01")
        sped_tuple = ("key", 100, True, "2023-01-01")
        canc_tuple = ("12345678901234567890123456789012345678901234",)

        def populate_batches():
            service._xml_batch.append(xml_tuple)
            service._fiscal_batch.append(sped_tuple)
            service._event_canc.append(canc_tuple)

        mock_parse_xml.side_effect = populate_batches

        result = service.run_audit()

        assert mock_db.executemany_sql.call_count == 3
        assert service._xml_batch == []
        assert service._fiscal_batch == []
        assert service._event_canc == []
        assert "metricas" in result
        assert len(result["dataframe"]) == 1

    @patch("src.services.audit.audit.DuckDBSession")
    @patch.object(AuditPipelineService, "_parse_xml")
    @patch.object(AuditPipelineService, "_parse_sintegra")
    def test_run_audit_sintegra_empty_batches(
        self, mock_parse_sintegra, mock_parse_xml, mock_duckdb_cls, mock_duckdb_session
    ):
        """Testa o pipeline Sintegra com lotes vazios (garantindo que executemany_sql não é chamado)."""
        mock_db, mock_cursor = mock_duckdb_session
        mock_duckdb_cls.return_value.__enter__.return_value = mock_db

        mock_cursor.df.return_value = pd.DataFrame()
        mock_cursor.fetchone.side_effect = [(0, 0), (0, 0)]

        service = AuditPipelineService(b"zip", b"sintegra", is_sped=False)

        result = service.run_audit()

        mock_db.executemany_sql.assert_not_called()
        assert result["dataframe"] == []