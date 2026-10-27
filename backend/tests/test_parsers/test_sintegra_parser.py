import pytest
from src.parsers.sintegra_parser import SintegraParser


@pytest.fixture(autouse=True)
def reset_sintegra_state():
    SintegraParser.company_name = None
    SintegraParser.company_cnpj = None
    yield
    SintegraParser.company_name = None
    SintegraParser.company_cnpj = None


def build_fixed_line(prefix: str, content_dict: dict = None) -> str:
    """Gera uma linha com tamanho fixo EXATO de 126 caracteres preenchida com espaços."""
    line_chars = list(prefix.ljust(126, " "))
    if content_dict:
        for (start, end), val in content_dict.items():
            val_str = str(val)
            length = end - start
            formatted_val = val_str[:length].ljust(length, " ")
            for i, char in enumerate(formatted_val):
                if start + i < 126:
                    line_chars[start + i] = char
    return "".join(line_chars[:126])


class TestFormatDate:

    @pytest.mark.parametrize("raw_date, expected", [
        ("20230901", "2023-09-01"),
        ("20221231", "2022-12-31"),
        ("18991231", SintegraParser.FALLBACK_DATE),
        ("20231301", SintegraParser.FALLBACK_DATE),
        ("2023090", SintegraParser.FALLBACK_DATE),
        ("2023090A", SintegraParser.FALLBACK_DATE),
        ("", SintegraParser.FALLBACK_DATE),
    ])
    def test_format_date_branches(self, raw_date, expected):
        assert SintegraParser._format_date(raw_date) == expected


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


class TestParseRecord50:

    def test_parse_50_success(self):
        line = build_fixed_line("50", {
            (2, 16): "12345678000195",
            (30, 38): "20230901",
            (40, 42): "55",
            (42, 45): "001",
            (45, 51): "000100",
            (55, 56): "P",
            (125, 126): "N"
        })
        result = SintegraParser._parse_record_50(line)

        assert result == {
            "cnpj_issuer": "12345678000195",
            "nfe_model": "55",
            "nfe_series": "001",
            "nfe_number": "000100",
            "value": 0,
            "emission_date": "2023-09-01"
        }

    def test_parse_50_rejected_entry_direction(self):
        line = build_fixed_line("50", {(55, 56): "T", (125, 126): "N"})
        assert SintegraParser._parse_record_50(line) is None

    @pytest.mark.parametrize("cancelled_code", ["C", "S", "X", "2", "4"])
    def test_parse_50_rejected_cancelled_status(self, cancelled_code):
        line = build_fixed_line("50", {(55, 56): "P", (125, 126): cancelled_code})
        assert SintegraParser._parse_record_50(line) is None


class TestParseRecord54:

    def test_parse_54_success(self):
        line = build_fixed_line("54", {
            (18, 21): "001",
            (21, 27): "000100",
            (62, 74): "000000015050"
        })
        result = SintegraParser._parse_record_54(line)

        assert result == {
            "series_number": "001",
            "document_number": "000100",
            "product_value": 15050
        }

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


class TestParseRecord61:

    def test_parse_61_success(self):
        line = build_fixed_line("61", {
            (30, 38): "20230901",
            (38, 40): "65",
            (40, 43): "000",
            (45, 51): "000123",
            (57, 70): "000000005000"
        })
        result = SintegraParser._parse_record_61(line)

        assert result == {
            "value": 5000,
            "nfe_model": "65",
            "nfe_series": "000",
            "nfe_number": "000123",
            "emission_date": "2023-09-01"
        }

    def test_parse_61_fallback_number_from_date(self):
        """Testa quando o número ordinal inicial é '000000'."""
        line = build_fixed_line("61", {
            (30, 38): "20230901",
            (45, 51): "000000",
            (57, 70): "000000005000"
        })
        result = SintegraParser._parse_record_61(line)
        assert result["nfe_number"] == "230901"


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
            (45, 51): "000001",
            (57, 70): "000000003000"
        })

        content = f"{line_10}\n{line_50}\n{line_54_item1}\n{line_54_item2}\n{line_61}"
        batch = []

        SintegraParser.parse_sintegra(content, batch)

        assert SintegraParser.get_company_name() == "EMPRESA SINTEGRA S.A."
        assert len(batch) == 2

        # Valida formato de tupla do batch para DuckDB
        rec_61 = [r for r in batch if r[2] == "65"][0]
        assert rec_61 == ("12345678000195", 3000, "65", "000", "000001", "2023-09-02")

        rec_50 = [r for r in batch if r[2] == "55"][0]
        assert rec_50 == ("12345678000195", 15000, "55", "001", "000100", "2023-09-01")


class TestGetCompanyNameAndCnpj:

    def test_get_company_name_success(self):
        SintegraParser.company_name = "MINHA EMPRESA LTDA"
        assert SintegraParser.get_company_name() == "MINHA EMPRESA LTDA"

    def test_get_company_name_raises_broken_pipe_error(self):
        SintegraParser.company_name = None
        with pytest.raises(BrokenPipeError, match="VERIFIQUE A PIPELINE"):
            SintegraParser.get_company_name()

    def test_get_cnpj_fallback(self):
        SintegraParser.company_cnpj = None
        assert SintegraParser.get_cnpj() == SintegraParser.FALLBACK_CNPJ