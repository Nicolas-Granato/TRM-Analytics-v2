
import re
import xml.etree.ElementTree as ET
from typing import Optional


class XmlParser:
    ACCESS_KEY_LENGTH = 44
    OPERATION_TYPE_OUTGOING = "1"

    @staticmethod
    def _find_node(
        parent: ET.Element,
        tag_name: str,
    ) -> Optional[ET.Element]:
        for elem in parent.iter():
            if elem.tag.endswith(tag_name):
                return elem

        return None

    @staticmethod
    def get_tag_text(
        parent: Optional[ET.Element],
        tag_name: str,
        default: str = "",
    ) -> str:
        if parent is None:
            return default

        for elem in parent.iter():
            if elem.tag.endswith(tag_name) and elem.text:
                return elem.text.strip()

        return default

    @classmethod
    def _extract_access_key(cls, root: ET.Element) -> str:
        key = cls.get_tag_text(root, "chNFe")

        if len(key) == cls.ACCESS_KEY_LENGTH and key.isdigit():
            return key

        for elem in root.iter():
            if elem.tag.endswith("infNFe"):
                key = elem.attrib.get("Id", "").replace("NFe", "").strip()

                if len(key) == cls.ACCESS_KEY_LENGTH and key.isdigit():
                    return key

        return ""

    @staticmethod
    def _to_cents(value: str) -> int:
        try:
            return int(round(float(value.replace(",", ".")) * 100))
        except (ValueError, AttributeError):
            return 0

    @classmethod
    def parse_xml(
        cls,
        xml_bytes: bytes,
        xmls_batch: list,
        cnpj_issuer: str,
    ) -> None:
        try:
            root = ET.fromstring(xml_bytes)

            ide_node = cls._find_node(root, "ide")

            if ide_node is None:
                return

            if cls.get_tag_text(ide_node, "tpNF") != cls.OPERATION_TYPE_OUTGOING:
                return

            emit_node = cls._find_node(root, "emit")

            if emit_node is None:
                return

            cnpj_xml = re.sub(
                r"\D",
                "",
                cls.get_tag_text(emit_node, "CNPJ"),
            ).zfill(14)

            cnpj_fiscal = re.sub(r"\D", "", cnpj_issuer or "").zfill(14)

            if (
                cnpj_fiscal != "00000000000000"
                and cnpj_xml[:8] != cnpj_fiscal[:8]
            ):
                return

            access_key = cls._extract_access_key(root)

            if len(access_key) != cls.ACCESS_KEY_LENGTH:
                return

            model = access_key[20:22]
            series = access_key[22:25]
            number = access_key[25:34]

            emission_date = cls.get_tag_text(ide_node, "dhEmi")[:10]

            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", emission_date):
                emission_date = cls.get_tag_text(ide_node, "dEmi")

                if len(emission_date) == 8 and emission_date.isdigit():
                    emission_date = (
                        f"{emission_date[4:8]}-"
                        f"{emission_date[2:4]}-"
                        f"{emission_date[0:2]}"
                    )
                else:
                    return

            if model != "65":
                if (
                    series != cls.get_tag_text(ide_node, "serie").zfill(3)
                    or number != cls.get_tag_text(ide_node, "nNF").zfill(9)
                ):
                    return

            total_node = cls._find_node(root, "total")
            value_text = cls.get_tag_text(
                total_node if total_node is not None else root,
                "vNF",
                "0.00",
            )

            xmls_batch.append(
                (
                    access_key,
                    cnpj_xml,
                    cls._to_cents(value_text),
                    series,
                    number,
                    emission_date,
                )
            )

        except (ET.ParseError, ValueError, TypeError, AttributeError):
            return
