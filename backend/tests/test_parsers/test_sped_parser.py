import pytest
from src.parsers.sped_parser import SpedParser

VALID_KEY = "35230900000000000191550010000000011000000001"


@pytest.fixture(autouse=True)
def reset_company_name():
    SpedParser.company_name = None
    yield
    SpedParser.company_name = None


# ==============================================================================
# Testes de Métodos Auxiliares (_format_date & _convert_to_cents)
# ==============================================================================

class TestSpedParserHelpers:

    @pytest.mark.parametrize("raw_date, expected", [
        ("01092023", "2023-09-01"),
        ("31122022", "2022-12-31"),
        ("1092023", SpedParser.FALLBACK_DATE),
        ("010920234", SpedParser.FALLBACK_DATE),
        ("0109202A", SpedParser.FALLBACK_DATE),
        ("", SpedParser.FALLBACK_DATE),
    ])
    def test_format_date_branches(self, raw_date, expected):
        """Testa todas as ramificações de validação de data."""
        assert SpedParser._format_date(raw_date) == expected

    @pytest.mark.parametrize("value_str, expected", [
        ("150,50", 15050),
        ("100.00", 10000),
        ("0,05", 5),
        ("", 0),
        ("   ", 0),
        ("INVALID_FLOAT", 0),
    ])
    def test_convert_to_cents_branches(self, value_str, expected):
        """Testa a conversão de valores decimais em centavos inteiros e tratamentos de erro."""
        assert SpedParser._convert_to_cents(value_str) == expected


# ==============================================================================
# Testes do Registro 0000 (_parse_record_0000)
# ==============================================================================

class TestParseRecord0000:

    def test_parse_0000_success_with_company_name(self):
        """Registro 0000 válido e com nome da empresa no campo 6."""
        line = "|0000|014|0|01012023|31012023|EMPRESA TESTE LTDA|12345678000195|"
        result = SpedParser._parse_record_0000(line)

        assert result is not None
        assert result["company_name"] == "EMPRESA TESTE LTDA"
        assert result["fields"] == 9

    def test_parse_0000_fallback_company_name(self):
        """Registro 0000 com número de campos insuficiente para conter a razão social."""
        line = "|0000|014|0|"
        result = SpedParser._parse_record_0000(line)

        assert result is not None
        assert result["company_name"] == SpedParser.FALLBACK_COMPANY_NAME

    @pytest.mark.parametrize("invalid_line", [
        "|000|014|0|",
        "|0000|014|",
        "LINHA_SEM_DELIMITADOR"
    ])
    def test_parse_0000_invalid_structures(self, invalid_line):
        """Descarte de registros 0000 malformados."""
        assert SpedParser._parse_record_0000(invalid_line) is None


# ==============================================================================
# Testes do Registro C100 (_parse_record_c100)
# ==============================================================================

class TestParseRecordC100:

    def _build_c100_line(
        self,
        tp_oper: str = "1",
        status: str = "00",
        key: str = VALID_KEY,
        date: str = "01092023",
        value: str = "150,50",
        tp_amb: str = "1",
        num_fields: int = 28
    ) -> str:
        """Constrói uma linha C100 sintética preenchendo os índices esperados."""
        fields = [""] * num_fields
        fields[1] = "C100"
        fields[2] = tp_oper
        fields[6] = status
        fields[9] = key
        fields[10] = date
        fields[12] = value
        if num_fields > 26:
            fields[26] = tp_amb
        return "|".join(fields)

    def test_parse_c100_success(self):
        """C100 válido: saída (1), status regular (00), ambiente produção (1)."""
        line = self._build_c100_line()
        result = SpedParser._parse_record_c100(line)

        assert result == {
            "access_key": VALID_KEY,
            "value": 15050,
            "emission_date": "2023-09-01",
        }

    @pytest.mark.parametrize("num_fields", [10, 13])
    def test_parse_c100_rejected_short_line(self, num_fields):
        """Rejeita linha C100 com menos de 14 campos."""
        fields = [""] * num_fields
        fields[1] = "C100"
        assert SpedParser._parse_record_c100("|".join(fields)) is None

    def test_parse_c100_rejected_incoming_operation(self):
        """Rejeita documentos de Entrada (tp_oper != '1')."""
        line = self._build_c100_line(tp_oper="0")
        assert SpedParser._parse_record_c100(line) is None

    def test_parse_c100_rejected_cancelled_document(self):
        """Rejeita documentos Cancelados (status == '02')."""
        line = self._build_c100_line(status="02")
        assert SpedParser._parse_record_c100(line) is None

    def test_parse_c100_rejected_homologation_environment(self):
        """Rejeita documentos emitidos em Homologação (campo 26 == '2')."""
        line = self._build_c100_line(tp_amb="2")
        assert SpedParser._parse_record_c100(line) is None

    def test_parse_c100_rejected_invalid_access_key(self):
        """Rejeita documento cuja chave de acesso não possua 44 dígitos."""
        line = self._build_c100_line(key="12345")
        assert SpedParser._parse_record_c100(line) is None


# ==============================================================================
# Testes do Fluxo do Arquivo Completo (parse_sped_content)
# ==============================================================================

class TestParseSpedContent:

    def test_parse_sped_fiscal_type(self):
        """
        SPED Fiscal: Registro 0000 com menos de 18 campos.
        Define sped_type = True.
        """
        sped_content = (
            f"|0000|014|0|01012023|31012023|EMPRESA FISCAL LTDA|12345678000195|\n"
            f"|C100|1|0||||00|||{VALID_KEY}|01092023||100,00||||||||||||||1|\n"
        )
        batch = []
        SpedParser.parse_sped_content(sped_content, batch)

        assert len(batch) == 1
        assert batch[0] == (VALID_KEY, 10000, True, "2023-09-01")
        assert SpedParser.get_company_name() == "EMPRESA FISCAL LTDA"

    def test_parse_sped_cofins_type(self):
        """
        SPED EFD-Contribuições: Registro 0000 com 18 ou mais campos.
        Define sped_type = False.
        """
        fields_0000 = [""] * 19
        fields_0000[1] = "0000"
        fields_0000[6] = "EMPRESA COFINS LTDA"
        line_0000 = "|".join(fields_0000)

        c100_line = f"|C100|1|0||||00|||{VALID_KEY}|01092023||250,00||||||||||||||1|"

        sped_content = f"{line_0000}\n{c100_line}"
        batch = []
        SpedParser.parse_sped_content(sped_content, batch)

        assert len(batch) == 1
        assert batch[0] == (VALID_KEY, 25000, False, "2023-09-01")

    def test_parse_c100_before_0000_is_ignored(self):
        """Registros C100 que surgirem antes do registro 0000 devem ser ignorados."""
        c100_line = f"|C100|1|0||||00|||{VALID_KEY}|01092023||100,00||||||||||||||1|"
        line_0000 = "|0000|014|0|01012023|31012023|EMPRESA LTDA|12345678000195|"

        sped_content = f"{c100_line}\n{line_0000}"
        batch = []
        SpedParser.parse_sped_content(sped_content, batch)

        assert len(batch) == 0

    def test_parse_ignores_empty_lines_and_unknown_records(self):
        """Garante que linhas em branco e registros não mapeados (case _) sejam ignorados."""
        sped_content = (
            "\n"
            "   \n"
            "|INVALID|\n"
            "|9999|FIM|\n"
        )
        batch = []
        SpedParser.parse_sped_content(sped_content, batch)

        assert len(batch) == 0


# ==============================================================================
# Testes do Nome da Empresa (get_company_name)
# ==============================================================================

class TestGetCompanyName:

    def test_get_company_name_success(self):
        """Retorna o nome da empresa quando a variável de classe estiver preenchida."""
        SpedParser.company_name = "MINHA EMPRESA S.A."
        assert SpedParser.get_company_name() == "MINHA EMPRESA S.A."

    def test_get_company_name_raises_broken_pipe_error(self):
        """Dispara BrokenPipeError caso get_company_name seja chamado sem registro 0000 ter sido processado."""
        SpedParser.company_name = None
        with pytest.raises(BrokenPipeError, match="VERIFIQUE A PIPELINE"):
            SpedParser.get_company_name()