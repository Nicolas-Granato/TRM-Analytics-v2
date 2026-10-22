import xml.etree.ElementTree as ET

class XmlParser:

    ACCESS_KEY_LENGTH = 44
    PRODUCTION_ENVIRONMENT_CODE = "1"
    OPERATION_TYPE_OUTGOINH = "1"

    @staticmethod
    def get_tag_text(root: ET.Element, tag_name: str, default: str = "") -> str:
        elem = root.find(f".//{{*}}{tag_name}")
        return elem.text.strip() if (elem is not None and elem.text) else default

    @classmethod
    def parse_xml(cls, xml_bytes: bytes) -> tuple:
        try:
            root = ET.fromstring(xml_bytes)

            tpAmb = int(cls.get_tag_text(root, "tpAmb", default="0"))
            if tpAmb != cls.PRODUCTION_ENVIRONMENT_CODE:
               return None 

            tpNF = int(cls.get_tag_text(root, "tpNF", default="0"))
            if tpNF != cls.OPERATION_TYPE_OUTGOINH:
                return None

            chNFe = cls.get_tag_text(root, "chNFe")
            if len(chNFe) != cls.ACCESS_KEY_LENGTH:
                return None

            cnpj = cls.get_tag_text(root, "CNPJ")
            serie = cls.get_tag_text(root, "serie")
            nNF = cls.get_tag_text(root, "nNF")
            dhEmi = cls.get_tag_text(root, "dhEmi")

            vNF_str = cls.get_tag_text(root, "vNF", default="0.00")
            vNF_centavos = int(round(float(vNF_str) * 100))

            return (chNFe, cnpj, vNF_centavos, serie, nNF, dhEmi, tpAmb, tpNF)

        except (ET.ParseError, ValueError, Exception) as err:
            raise ValueError("Erro ao processar o conteúdo do XML.") from err