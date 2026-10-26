import xml.etree.ElementTree as ET
from typing import Optional, Tuple
from loguru import logger

class XmlParser:

    ACCESS_KEY_LENGTH = 44
    PRODUCTION_ENVIRONMENT_CODE = "1"
    OPERATION_TYPE_OUTGOING = "1"

    @staticmethod
    def _find_node(parent: ET.Element, tag_name: str) -> Optional[ET.Element]:
        """Busca um nó ignorando completamente o namespace da SEFAZ."""
        for elem in parent.iter():
            if elem.tag.endswith(tag_name):
                return elem
        return None

    @staticmethod
    def get_tag_text(parent: Optional[ET.Element], tag_name: str, default: str = "") -> str:
        if parent is None:
            return default
        for elem in parent.iter():
            if elem.tag.endswith(tag_name) and elem.text:
                return elem.text.strip()
        return default

    @classmethod
    def _extract_access_key(cls, root: ET.Element) -> str:
        """Extrai a chave de acesso de 44 dígitos."""
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
    def parse_xml(cls, xml_bytes: bytes, xmls_batch: list) -> None:
        try:
            root = ET.fromstring(xml_bytes)

            ide_node = cls._find_node(root, "ide")
            if ide_node is None:
                return

            tpAmb = cls.get_tag_text(ide_node, "tpAmb")
            if tpAmb != cls.PRODUCTION_ENVIRONMENT_CODE:
                return

            tpNF = cls.get_tag_text(ide_node, "tpNF")
            if tpNF != cls.OPERATION_TYPE_OUTGOING:
                return

            emit_node = cls._find_node(root, "emit")
            if emit_node is None:
                return
                
            cnpj_emitente = cls.get_tag_text(emit_node, "CNPJ")

            chNFe = cls._extract_access_key(root)
            if len(chNFe) != cls.ACCESS_KEY_LENGTH:
                return

            serie = cls.get_tag_text(ide_node, "serie")
            nNF = cls.get_tag_text(ide_node, "nNF")
            dhEmi = cls.get_tag_text(ide_node, "dhEmi")
            
            formatted_date = dhEmi[:10] if len(dhEmi) >= 10 else "0000-00-00"

            total_node = cls._find_node(root, "total")
            vNF_str = cls.get_tag_text(total_node if total_node is not None else root, "vNF", default="0.00")
            vNF_centavos = int(round(float(vNF_str) * 100))

            record_tuple = (chNFe, cnpj_emitente, vNF_centavos, serie, nNF, formatted_date)
            xmls_batch.append(record_tuple)

        except ET.ParseError as pe:
            logger.warning("⚠️ Ignorando XML inválido/corrompido: {}", pe)
        except Exception as e:
            logger.error("❌ Erro no parse do XML: {}", e)