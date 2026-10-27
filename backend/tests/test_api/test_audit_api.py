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
        expected_xml = (
            "35230000000000000191550010000001001000000001",
            "12345678000195",
            10000,
            "001",
            "000000100",
            "2023-09-01",
        )

        def parse_xml_side_effect(xml_bytes, xmls_batch, cnpj_issuer):
            xmls_batch.append(expected_xml)

        mock_parse_xml.side_effect = parse_xml_side_effect

        service = AuditPipelineService(
            zip_files=sample_zip_bytes,
            fiscal_file_bytes=b"content",
        )

        service._parse_xml_zip(sample_zip_bytes)

        assert service._xml_batch == [expected_xml]
        mock_parse_xml.assert_called_once()


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