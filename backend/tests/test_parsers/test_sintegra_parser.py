import pytest
from backend.src.parsers.sintegra_parser import SintegraParser


@pytest.fixture(autouse=True)
def reset_sintegra_state():
    SintegraParser.company_name = None
    SintegraParser.company_cnpj = None
    yield
    SintegraParser.company_name = None
    SintegraParser.company_cnpj = None


def build_fixed_line(prefix: str, content_dict: dict = None) -> str:
    """Gera uma linha com tamanho fixo mínimo de 126 caracteres preenchida com espaços."""
    line_chars = list(prefix.ljust(126, " "))
    if content_dict:
        for (start, end), val in content_dict.items():
            val_str = str(val)
            length = end - start
            line_chars[start:end] = list(val_str[:length].ljust(length, " "))
    return "".join(line_chars)


# ==============================================================================
# Testes do Método Auxiliar: _format_date (Complexidade V(G) = 3)
# ==============================================================================

class TestFormatDate:

    @pytest.mark.parametrize("raw_date, expected", [
        ("20230901", "2023-09-01"),
        ("20221231", "2022-12-31"),
        ("2023090", SintegraParser.FALLBACK_DATE),
        ("202309011", SintegraParser.FALLBACK_DATE),
        ("2023090A", SintegraParser.FALLBACK_DATE),
        ("", SintegraParser.FALLBACK_DATE),
    ])
    def test_format_date_branches(self, raw_date, expected):
        assert SintegraParser._format_date(raw_date) == expected


# ==============================================================================
# Testes do Registro 10 (_parse_record_10) (Complexidade V(G) = 3)
# ==============================================================================

class TestParseRecord10:

    def test_parse_10_success(self):
        line = build_fixed_line("10", {
            (2, 16): "12345678000195",
            (30, 65): "EMPRESA DE TESTE SINTEGRA LTDA"
        })
        result = SintegraParser._parse_record_10(line)

        assert result == {
            "company_name": "EMPRESA DE TESTE SINTEGRA LTDA",
            "company_cnpj": "12345678000195"
        }

    def test_parse_10_fallback_company_name(self):
        line = build_fixed_line("10", {(2, 16): "12345678000195"})
        result = SintegraParser._parse_record_10(line)

        assert result["company_name"] == SintegraParser.FALLBACK_COMPANY_NAME

    @pytest.mark.parametrize("invalid_line", [
        "10" + " " * 50,
        build_fixed_line("11")
    ])
    def test_parse_10_invalid_lines(self, invalid_line):
        assert SintegraParser._parse_record_10(invalid_line) is None


# ==============================================================================
# Testes do Registro 50 (_parse_record_50) (Complexidade V(G) = 4)
# ==============================================================================

class TestParseRecord50:

    def test_parse_50_success(self):
        line = build_fixed_line("50", {
            (2, 16): "12345678000195",
            (30, 38): "20230901",
            (42, 45): "001",
            (45, 51): "000100",
            (55, 56): "P",
            (125, 126): "N"
        })
        result = SintegraParser._parse_record_50(line)

        assert result == {
            "cnpj_issuer": "12345678000195",
            "nfe_series": "001",
            "nfe_number": "000100",
            "emission_date": "2023-09-01"
        }

    def test_parse_50_rejected_entry_direction(self):
        line = build_fixed_line("50", {(55, 56): "T", (125, 126): "N"})
        assert SintegraParser._parse_record_50(line) is None

    @pytest.mark.parametrize("cancelled_code", ["C", "S", "X", "2", "4"])
    def test_parse_50_rejected_cancelled_status(self, cancelled_code):
        line = build_fixed_line("50", {(55, 56): "P", (125, 126): cancelled_code})
        assert SintegraParser._parse_record_50(line) is None

    def test_parse_50_short_line(self):
        line = "50" + " " * 100
        assert SintegraParser._parse_record_50(line) is None


# ==============================================================================
# Testes do Registro 54 (_parse_record_54) (Complexidade V(G) = 5)
# ==============================================================================

class TestParseRecord54:

    def test_parse_54_success(self):
        line = build_fixed_line("54", {
            (18, 21): "001",
            (21, 27): "000100",
            (62, 74): "000000015050"
        })
        valid_keys = {("001", "000100")}
        result = SintegraParser._parse_record_54(line, valid_50_keys=valid_keys)

        assert result == {
            "series_number": "001",
            "document_number": "000100",
            "product_value": 15050
        }

    def test_parse_54_key_not_in_valid_set(self):
        line = build_fixed_line("54", {(18, 21): "001", (21, 27): "000100"})
        valid_keys = {("001", "999999")}
        assert SintegraParser._parse_record_54(line, valid_50_keys=valid_keys) is None

    def test_parse_54_missing_series_or_document(self):
        line = build_fixed_line("54", {(18, 21): "   ", (21, 27): "000100"})
        assert SintegraParser._parse_record_54(line) is None

    def test_parse_54_non_digit_value_fallback_to_zero(self):
        line = build_fixed_line("54", {
            (18, 21): "001",
            (21, 27): "000100",
            (62, 74): "ABCDEF"
        })
        result = SintegraParser._parse_record_54(line)
        assert result["product_value"] == 0


# ==============================================================================
# Testes do Registro 61 (_parse_record_61) (Complexidade V(G) = 3)
# ==============================================================================

class TestParseRecord61:

    def test_parse_61_success(self):
        line = build_fixed_line("61", {
            (30, 38): "20230901",
            (57, 70): "000000005000"
        })
        result = SintegraParser._parse_record_61(line)

        assert result == {
            "value": 5000,
            "emission_date": "2023-09-01"
        }

    def test_parse_61_non_digit_value_fallback_to_zero(self):
        line = build_fixed_line("61", {
            (30, 38): "20230901",
            (57, 70): "NON_DIGITS"
        })
        result = SintegraParser._parse_record_61(line)
        assert result["value"] == 0

    def test_parse_61_short_line(self):
        line = "61" + " " * 50
        assert SintegraParser._parse_record_61(line) is None


# ==============================================================================
# Testes do Parser Completo (parse_sintegra) (Complexidade V(G) = 10)
# ==============================================================================

class TestParseSintegra:

    def test_parse_sintegra_complete_pipeline(self):
        line_10 = build_fixed_line("10", {
            (2, 16): "12345678000195",
            (30, 65): "EMPRESA SINTEGRA S.A."
        })
        line_50 = build_fixed_line("50", {
            (2, 16): "12345678000195",
            (30, 38): "20230901",
            (42, 45): "001",
            (45, 51): "000100",
            (55, 56): "P",
            (125, 126): "N"
        })
        line_54_item1 = build_fixed_line("54", {
            (18, 21): "001",
            (21, 27): "000100",
            (62, 74): "000000010000"
        })
        line_54_item2 = build_fixed_line("54", {
            (18, 21): "001",
            (21, 27): "000100",
            (62, 74): "000000005000"
        })
        line_61 = build_fixed_line("61", {
            (30, 38): "20230902",
            (57, 70): "000000003000"
        })

        content = f"{line_10}\n{line_50}\n{line_54_item1}\n{line_54_item2}\n{line_61}"
        batch = []

        SintegraParser.parse_sintegra(content, batch)

        assert SintegraParser.get_company_name() == "EMPRESA SINTEGRA S.A."
        assert len(batch) == 2

        rec_61 = [r for r in batch if r["nfe_model"] == "65"][0]
        assert rec_61["value"] == 3000
        assert rec_61["cnpj_issuer"] == "12345678000195"

        rec_50 = [r for r in batch if r["nfe_model"] == "55"][0]
        assert rec_50["value"] == 15000
        assert rec_50["nfe_series"] == "001"
        assert rec_50["nfe_number"] == "000100"

    def test_parse_sintegra_ignores_subsequent_10_records(self):
        line_10_first = build_fixed_line("10", {(30, 65): "PRIMEIRA EMPRESA"})
        line_10_second = build_fixed_line("10", {(30, 65): "SEGUNDA EMPRESA"})

        content = f"{line_10_first}\n{line_10_second}"
        batch = []

        SintegraParser.parse_sintegra(content, batch)
        assert SintegraParser.get_company_name() == "PRIMEIRA EMPRESA"

    def test_parse_sintegra_ignores_blank_lines_and_unknown_records(self):
        content = "\n  \n99" + " " * 120 + "\n"
        batch = []
        SintegraParser.parse_sintegra(content, batch)
        assert len(batch) == 0


# ==============================================================================
# Testes do Método: get_company_name (Complexidade V(G) = 2)
# ==============================================================================

class TestGetCompanyName:

    def test_get_company_name_success(self):
        SintegraParser.company_name = "MINHA EMPRESA LTDA"
        assert SintegraParser.get_company_name() == "MINHA EMPRESA LTDA"

    def test_get_company_name_raises_broken_pipe_error(self):
        SintegraParser.company_name = None
        with pytest.raises(BrokenPipeError, match="VERIFIQUE A PIPELINE"):
            SintegraParser.get_company_name()