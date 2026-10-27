import pytest
from src.parsers.xml_parser import XmlParser


VALID_KEY = "35230900000000000191550010000001001000000001"


@pytest.fixture
def make_xml():
    def _create_xml_bytes(
        tpAmb: str = "1",
        tpNF: str = "1",
        chNFe: str = VALID_KEY,
        cnpj: str = "12345678000195",
        serie: str = "1",
        nNF: str = "100",
        dhEmi: str = "2023-09-01T10:00:00-03:00",
        dEmi: str = None,
        vNF: str = "150.50",
        include_chNFe_tag: bool = True,
        infNFe_id: str = None,
        include_ide: bool = True,
        include_emit: bool = True,
    ) -> bytes:
        inf_id_attr = (
            f' Id="NFe{infNFe_id or chNFe}"'
            if (infNFe_id or chNFe)
            else ""
        )

        date_tag = (
            f"<dEmi>{dEmi}</dEmi>"
            if dEmi is not None
            else f"<dhEmi>{dhEmi}</dhEmi>"
        )

        ide_block = (
            f"""
            <ide>
                <tpAmb>{tpAmb}</tpAmb>
                <tpNF>{tpNF}</tpNF>
                <serie>{serie}</serie>
                <nNF>{nNF}</nNF>
                {date_tag}
            </ide>
            """
            if include_ide
            else ""
        )

        emit_block = (
            f"""
            <emit>
                <CNPJ>{cnpj}</CNPJ>
            </emit>
            """
            if include_emit
            else ""
        )

        ch_nfe_tag = (
            f"<chNFe>{chNFe}</chNFe>"
            if include_chNFe_tag
            else ""
        )

        value_tag = (
            f"<vNF>{vNF}</vNF>"
            if vNF is not None
            else ""
        )

        xml_str = f"""
        <nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
            <NFe>
                <infNFe{inf_id_attr}>
                    {ide_block}
                    {emit_block}
                    <total>
                        <ICMSTot>{value_tag}</ICMSTot>
                    </total>
                </infNFe>
            </NFe>
            <protNFe>
                <infProt>{ch_nfe_tag}</infProt>
            </protNFe>
        </nfeProc>
        """

        return xml_str.encode("utf-8")

    return _create_xml_bytes


class TestParseXml:

    def test_parse_xml_success(self, make_xml):
        xml_bytes = make_xml(
            vNF="150.50",
            cnpj="12345678000195",
        )
        batch = []

        XmlParser.parse_xml(
            xml_bytes,
            batch,
            cnpj_issuer="12345678000195",
        )

        assert len(batch) == 1
        assert batch[0] == (
            VALID_KEY,
            "12345678000195",
            15050,
            "001",
            "000000100",
            "2023-09-01",
        )

    def test_parse_xml_date_dEmi_fallback(self, make_xml):
        xml_bytes = make_xml(
            dhEmi="",
            dEmi="01092023",
        )
        batch = []

        XmlParser.parse_xml(
            xml_bytes,
            batch,
            cnpj_issuer="12345678000195",
        )

        assert len(batch) == 1
        assert batch[0][5] == "2023-09-01"

    @pytest.mark.parametrize(
        "override_kwargs",
        [
            {"tpNF": "0"},
            {"include_ide": False},
            {"include_emit": False},
            {"cnpj": "99999999000199"},
        ],
    )
    def test_parse_xml_rejections(self, make_xml, override_kwargs):
        xml_bytes = make_xml(**override_kwargs)
        batch = []

        XmlParser.parse_xml(
            xml_bytes,
            batch,
            cnpj_issuer="12345678000195",
        )

        assert batch == []

    def test_parse_xml_rejects_invalid_access_key(self, make_xml):
        xml_bytes = make_xml(chNFe="123")
        batch = []

        XmlParser.parse_xml(
            xml_bytes,
            batch,
            cnpj_issuer="12345678000195",
        )

        assert batch == []

    def test_parse_xml_rejects_mismatched_series(self, make_xml):
        xml_bytes = make_xml(serie="2")
        batch = []

        XmlParser.parse_xml(
            xml_bytes,
            batch,
            cnpj_issuer="12345678000195",
        )

        assert batch == []

    def test_parse_xml_rejects_mismatched_number(self, make_xml):
        xml_bytes = make_xml(nNF="200")
        batch = []

        XmlParser.parse_xml(
            xml_bytes,
            batch,
            cnpj_issuer="12345678000195",
        )

        assert batch == []

    def test_parse_xml_handles_missing_value(self, make_xml):
        xml_bytes = make_xml(vNF=None)
        batch = []

        XmlParser.parse_xml(
            xml_bytes,
            batch,
            cnpj_issuer="12345678000195",
        )

        assert len(batch) == 1
        assert batch[0][2] == 0

    def test_parse_xml_handles_missing_access_key_tag(self, make_xml):
        xml_bytes = make_xml(include_chNFe_tag=False)
        batch = []

        XmlParser.parse_xml(
            xml_bytes,
            batch,
            cnpj_issuer="12345678000195",
        )

        assert len(batch) == 1
        assert batch[0][0] == VALID_KEY

    def test_parse_xml_handles_exceptions_silently(self):
        batch = []

        XmlParser.parse_xml(
            b"<invalid_xml",
            batch,
            cnpj_issuer="12345678000195",
        )

        assert batch == []
