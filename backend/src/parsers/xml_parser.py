import xml.etree.ElementTree as ET
from typing import Optional

class XmlParser:

    ACCESS_KEY_LENGTH = 44
    PRODUCTION_ENVIRONMENT_CODE = "1"
    OPERATION_TYPE_OUTGOING = "1"

    @staticmethod
    def get_tag_text(root: ET.Element, tag_name: str, default: str = "") -> str:
        elem = root.find(f".//{{*}}{tag_name}")
        return elem.text.strip() if (elem is not None and elem.text) else default

    @classmethod
    def _extract_access_key(cls, root: ET.Element) -> str:
        chNFe = cls.get_tag_text(root, "chNFe")
        if len(chNFe) == cls.ACCESS_KEY_LENGTH and chNFe.isdigit():
            return chNFe

        for elem in root.iter():
            if elem.tag.endswith("infNFe"):
                inf_id = elem.attrib.get("Id", "").replace("NFe", "").strip()
                if len(inf_id) == cls.ACCESS_KEY_LENGTH and inf_id.isdigit():
                    return inf_id

        return ""

    @classmethod
    def parse_xml(cls, xml_bytes: bytes) -> Optional[tuple[str, str, int, str, str, str, str, str]]:
        try:
            root = ET.fromstring(xml_bytes)

            tpAmb = cls.get_tag_text(root, "tpAmb")
            if tpAmb != cls.PRODUCTION_ENVIRONMENT_CODE:
                return None

            tpNF = cls.get_tag_text(root, "tpNF")
            if tpNF != cls.OPERATION_TYPE_OUTGOING:
                return None

            chNFe = cls._extract_access_key(root)
            if len(chNFe) != cls.ACCESS_KEY_LENGTH:
                return None

            cnpj = cls.get_tag_text(root, "CNPJ")
            serie = cls.get_tag_text(root, "serie")
            nNF = cls.get_tag_text(root, "nNF")
            dhEmi = cls.get_tag_text(root, "dhEmi")

            vNF_str = cls.get_tag_text(root, "vNF", default="0.00")
            vNF_centavos = int(round(float(vNF_str) * 100))

            return (chNFe, cnpj, vNF_centavos, serie, nNF, dhEmi, tpAmb, tpNF)

        except (ET.ParseError, ValueError, Exception):
            return None