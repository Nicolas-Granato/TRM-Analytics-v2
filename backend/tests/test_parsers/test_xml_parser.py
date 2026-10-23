import pytest
import xml.etree.ElementTree as ET
from src.parsers.xml_parser import XmlParser


# ==============================================================================
# Fixtures e Funções Auxiliares
# ==============================================================================

VALID_KEY = "35230900000000000191550010000000011000000001"


@pytest.fixture
def make_xml():
    """Fixture geradora de XMLs em bytes com suporte a overrides para simular caminhos ciclomáticos."""
    def _create_xml_bytes(
        tpAmb: str = "1",
        tpNF: str = "1",
        chNFe: str = VALID_KEY,
        cnpj: str = "12345678000195",
        serie: str = "1",
        nNF: str = "100",
        dhEmi: str = "2023-09-01T10:00:00-03:00",
        vNF: str = "150.50",
        include_chNFe_tag: bool = True,
        infNFe_id: str = None
    ) -> bytes:
        inf_id_attr = f' Id="NFe{infNFe_id or chNFe}"' if (infNFe_id or chNFe) else ""
        
        xml_str = f"""<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
            <NFe>
                <infNFe{inf_id_attr}>
                    <ide>
                        <tpAmb>{tpAmb}</tpAmb>
                        <tpNF>{tpNF}</tpNF>
                        <serie>{serie}</serie>
                        <nNF>{nNF}</nNF>
                        <dhEmi>{dhEmi}</dhEmi>
                    </ide>
                    <emit>
                        <CNPJ>{cnpj}</CNPJ>
                    </emit>
                    <total>
                        <ICMSTot>
                            {"<vNF>" + vNF + "</vNF>" if vNF is not None else ""}
                        </ICMSTot>
                    </total>
                </infNFe>
            </NFe>
            <protNFe>
                <infProt>
                    {"<chNFe>" + chNFe + "</chNFe>" if include_chNFe_tag else ""}
                </infProt>
            </protNFe>
        </nfeProc>"""
        return xml_str.encode("utf-8")

    return _create_xml_bytes


# ==============================================================================
# Testes do Método: get_tag_text (Complexidade V(G) = 3)
# ==============================================================================

class TestGetTagText:

    def test_get_tag_text_success(self):
        """Caminho 1: Elemento encontrado e possui texto limpo."""
        root = ET.fromstring("<root><child>  conteudo  </child></root>")
        assert XmlParser.get_tag_text(root, "child") == "conteudo"

    def test_get_tag_text_empty_element_returns_default(self):
        """Caminho 2: Elemento encontrado, mas com texto vazio."""
        root = ET.fromstring("<root><child></child></root>")
        assert XmlParser.get_tag_text(root, "child", default="padrao") == "padrao"

    def test_get_tag_text_missing_element_returns_default(self):
        """Caminho 3: Elemento não encontrado no XML."""
        root = ET.fromstring("<root></root>")
        assert XmlParser.get_tag_text(root, "inexistente", default="padrao") == "padrao"


# ==============================================================================
# Testes do Método: _extract_access_key (Complexidade V(G) = 5)
# ==============================================================================

class TestExtractAccessKey:

    def test_extract_key_from_chNFe_tag_success(self, make_xml):
        """Caminho 1: Extrai chave válida diretamente da tag <chNFe>."""
        xml_bytes = make_xml(include_chNFe_tag=True)
        root = ET.fromstring(xml_bytes)
        assert XmlParser._extract_access_key(root) == VALID_KEY

    def test_extract_key_from_infNFe_attribute_fallback_success(self, make_xml):
        """Caminho 2: Tag <chNFe> ausente; extrai com sucesso do atributo 'Id' em <infNFe>."""
        xml_bytes = make_xml(include_chNFe_tag=False, infNFe_id=VALID_KEY)
        root = ET.fromstring(xml_bytes)
        assert XmlParser._extract_access_key(root) == VALID_KEY

    @pytest.mark.parametrize("invalid_key", [
        "1234567890",
        "3523090000000000019155001000000001100000000A"
    ])
    def test_extract_key_invalid_tag_and_invalid_attribute(self, make_xml, invalid_key):
        """Caminho 3 e 4: Chave inválida tanto na tag <chNFe> quanto no nó <infNFe>."""
        xml_bytes = make_xml(chNFe=invalid_key, include_chNFe_tag=False, infNFe_id=invalid_key)
        root = ET.fromstring(xml_bytes)
        assert XmlParser._extract_access_key(root) == ""


# ==============================================================================
# Testes do Método: parse_xml (Complexidade V(G) = 6)
# ==============================================================================

class TestParseXml:

    def test_parse_xml_success(self, make_xml):
        """Fluxo Principal: XML válido de produção e saída adicionado ao lote."""
        xml_bytes = make_xml(vNF="150.50")
        batch = []

        result = XmlParser.parse_xml(xml_bytes, batch)

        assert result is None
        assert len(batch) == 1
        assert batch[0] == (
            VALID_KEY,
            "12345678000195",
            15050,
            "1",
            "100",
            "2023-09-01T10:00:00-03:00",
            "1",
            "1"
        )

    def test_parse_xml_default_vNF_when_tag_missing(self, make_xml):
        """Garantia da branch vNF: Quando a tag <vNF> não existe, utiliza fallback '0.00' (0 centavos)."""
        xml_bytes = make_xml(vNF=None)
        batch = []

        XmlParser.parse_xml(xml_bytes, batch)

        assert len(batch) == 1
        assert batch[0][2] == 0

    @pytest.mark.parametrize("override_kwargs", [
        {"tpAmb": "2"},
        {"tpNF": "0"},
        {"chNFe": "123"},
    ])
    def test_parse_xml_rejections_return_none(self, make_xml, override_kwargs):
        """Testa todas as condicionais de descarte/rejeição do parse_xml."""
        xml_bytes = make_xml(**override_kwargs)
        batch = []

        result = XmlParser.parse_xml(xml_bytes, batch)

        assert result is None
        assert len(batch) == 0

    @pytest.mark.parametrize("corrupted_payload", [
        b"<nfeProc><invalidXml",
        b"texto plano aleatorio",
    ])
    def test_parse_xml_handles_exceptions_silently(self, corrupted_payload):
        """Testa o bloco try/except tratando falhas de parsing sem lançar exceção."""
        batch = []

        result = XmlParser.parse_xml(corrupted_payload, batch)

        assert result is None
        assert len(batch) == 0

    def test_parse_xml_handles_value_error_on_conversion(self, make_xml):
        """Testa tratamento de exceção (ValueError) caso <vNF> contenha string não conversível em float."""
        xml_bytes = make_xml(vNF="VALOR_INVALIDO")
        batch = []

        result = XmlParser.parse_xml(xml_bytes, batch)

        assert result is None
        assert len(batch) == 0