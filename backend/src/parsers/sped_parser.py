from typing import Optional

class SpedParser:

    RECORD_DELIMITER = "|"
    ACCESS_KEY_LENGTH = 44

    FALLBACK_COMPANY_NAME = "EMPRESA_NAO_IDENTIFICADA"
    FALLBACK_DATE = "0000-00-00"

    OPERATION_TYPE_OUTGOING = "1"
    DOCUMENT_STATUS_CANCELLED = "02"
    TP_AMB_HOMOLOGATION = "2"

    @staticmethod
    def _format_date(raw_date: str) -> str:
        raw_date = raw_date.strip()
        if len(raw_date) == 8 and raw_date.isdigit():
            day, month, year = raw_date[0:2], raw_date[2:4], raw_date[4:8]
            return f"{year}-{month}-{day}"
        return SpedParser.FALLBACK_DATE

    @staticmethod
    def _convert_to_cents(value_str: str) -> int:
        try:
            cleaned_value = value_str.strip().replace(",", ".")
            return int(round(float(cleaned_value) * 100)) if cleaned_value else 0
        except ValueError:
            return 0

    @classmethod
    def _parse_record_0000(cls, line_0000: str) -> Optional[dict]:
        fields = line_0000.split(cls.RECORD_DELIMITER)
        if len(fields) < 4 or fields[1] != "0000":
            return None

        company_name = fields[6].strip() if len(fields) > 6 else cls.FALLBACK_COMPANY_NAME

        return {
            "fields": len(fields),
            "company_name": company_name,
        }

    @classmethod
    def _parse_record_c100(cls, line_c100: str) -> Optional[dict]:
        fields = line_c100.split(cls.RECORD_DELIMITER)

        if len(fields) < 14:
            return None

        operation_type = fields[2].strip()
        if operation_type != cls.OPERATION_TYPE_OUTGOING:
            return None

        document_status = fields[6].strip() or "00"
        if document_status == cls.DOCUMENT_STATUS_CANCELLED:
            return None

        if len(fields) > 26 and fields[26].strip() == cls.TP_AMB_HOMOLOGATION:
            return None
        
        access_key = fields[9].strip()
        if len(access_key) != cls.ACCESS_KEY_LENGTH:
            return None


        emission_date = cls._format_date(fields[10])
        total_value_cents = cls._convert_to_cents(fields[12])

        return {
            "access_key": access_key,
            "value": total_value_cents,
            "emission_date": emission_date,
        }

    @classmethod
    def parse_sped_content(cls, sped_content: str, records: list) -> None:
        parsed_0000: Optional[list] = None
        sped_type: bool = False #False->SPED_COFINS True->SPED_FISCAL

        lines = sped_content.splitlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith(f"{cls.RECORD_DELIMITER}0000{cls.RECORD_DELIMITER}"):
                parsed_0000 = cls._parse_record_0000(line)
                if parsed_0000:
                    record_0000_number_fields = parsed_0000.get("fields")
                    sped_type = False if record_0000_number_fields >= 18 else True

            elif line.startswith(f"{cls.RECORD_DELIMITER}C100{cls.RECORD_DELIMITER}"):
                parsed_c100 = cls._parse_record_c100(line)
                
                if not parsed_c100 or not parsed_0000 or record_0000_number_fields is None:
                    continue

                record_tuple = (
                    parsed_c100.get("access_key"),
                    parsed_c100.get("value"),
                    sped_type,
                    parsed_c100.get("emission_date"),
                )
                records.append(record_tuple)
