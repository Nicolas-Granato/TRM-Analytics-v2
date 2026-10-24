import io
import zipfile
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from src.services.audit.audit import AuditPipelineService


class TestAuditPipelineServiceComplexity:

    @pytest.fixture
    def sample_zip_bytes(self) -> bytes:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as zf:
            zf.writestr("nota1.xml", "<nfeProc></nfeProc>")
            zf.writestr("leia-me.txt", "Ignorar")
        return buffer.getvalue()

    @patch("src.services.audit.audit.XmlParser.parse_xml")
    def test_parse_xml_zip_success(self, mock_parse_xml, sample_zip_bytes):
        mock_parse_xml.return_value = ("3523...", "12345678000195", 10000, "1", "100", "2023-09-01")

        service = AuditPipelineService(zip_files=sample_zip_bytes, fiscal_file_bytes=b"content")
        service._parse_xml_zip()

        assert len(service._xml_batch) == 1
        assert "CREATE TEMP TABLE IF NOT EXISTS xml" in service.ddl_scripts[0]

    @patch("src.services.audit.audit.DuckDBSession")
    @patch.object(AuditPipelineService, "_parse_xml_zip")
    @patch.object(AuditPipelineService, "_parse_sped")
    def test_run_audit_sped_full_success(
        self, mock_parse_sped, mock_parse_xml, mock_duckdb_cls
    ):
        mock_db = MagicMock()
        mock_cursor = MagicMock()
        mock_duckdb_cls.return_value.__enter__.return_value = mock_db
        mock_db.execute_sql.return_value = mock_cursor

        mock_cursor.fetchone.side_effect = [(1, 100), (1, 100)]
        mock_cursor.df.return_value = pd.DataFrame(
            [{"access_key": "3523...", "divergence_type": "DIVERGENCIA_DE_VALOR"}]
        )

        service = AuditPipelineService(b"zip", b"sped", is_sped=True)
        xml_tuple = ("key", "cnpj", 100, "1", "1", "2023-01-01")
        sped_tuple = ("key", 100, True, "2023-01-01")

        service._xml_batch = [xml_tuple]
        service._fiscal_batch = [sped_tuple]

        result = service.run_audit()

        assert mock_db.executemany_sql.call_count == 2
        
        assert len(service._xml_batch) == 0
        assert len(service._fiscal_batch) == 0
        assert "metricas" in result
        assert len(result["dataframe"]) == 1