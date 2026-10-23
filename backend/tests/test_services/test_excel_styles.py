import pytest
from openpyxl.styles import Font, PatternFill

from src.services.export.excel_styles import ExcelStyles


class TestExcelStyles:

    @pytest.mark.parametrize(
        "status, expected_style_key",
        [
            ("MISSING_XML", "CRITICAL"),
            ("XML_AUSENTE", "CRITICAL"),
            ("missing_fiscal", "CRITICAL"),
            ("VALUE_DIVERGENCE", "WARNING"),
            ("DIVERGENCIA_VALOR", "WARNING"),
            ("DIVERGENCIA_DATA", "WARNING"),
            ("OK", "OK"),
            ("APROVADO", "OK"),
            ("correto", "OK"),
        ],
    )
    def test_get_status_style_known_statuses(self, status: str, expected_style_key: str):
        """Valida se os status conhecidos retornam as cores/fontes corretas."""
        fill, font = ExcelStyles.get_status_style(status)

        expected = ExcelStyles.STATUS_STYLES[expected_style_key]
        assert isinstance(fill, PatternFill)
        assert isinstance(font, Font)
        assert fill.start_color.rgb == expected["fill"].start_color.rgb
        assert font.color.rgb == expected["font"].color.rgb

    @pytest.mark.parametrize("invalid_status", ["UNKNOWN", "", None, "STATUS_INEXISTENTE"])
    def test_get_status_style_unknown_or_empty_statuses(self, invalid_status):
        """Valida se status desconhecidos ou vazios retornam None para estilo."""
        fill, font = ExcelStyles.get_status_style(invalid_status)
        assert fill is None
        assert font is None

    @pytest.mark.parametrize(
        "model_input, expected_output",
        [
            ("55", "NF-e"),
            ("65", "NFC-e"),
            ("NFe", "NF-e"),
            ("NFCe", "NFC-e"),
            ("57", "57"),
            ("", "Não identificado"),
            (None, "Não identificado"),
        ],
    )
    def test_format_nfe_model(self, model_input, expected_output: str):
        """Testa o mapeamento correto dos códigos de modelo de NF-e/NFC-e."""
        result = ExcelStyles.format_nfe_model(model_input)
        assert result == expected_output