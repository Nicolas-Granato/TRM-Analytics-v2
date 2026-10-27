from typing import Optional
import re

class SpedParser:

    RECORD_DELIMITER = "|"
    ACCESS_KEY_LENGTH = 44

    FALLBACK_COMPANY_NAME = "EMPRESA_NAO_IDENTIFICADA"
    FALLBACK_DATE = "0000-00-00"
    FALLBACK_CNPJ = "00000000000000"

    OPERATION_TYPE_OUTGOING = "1"
    DOCUMENT_STATUS_CANCELLED = "02"
    TP_AMB_HOMOLOGATION = "2"

    company_name: str
    cnpj_issuer: str

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
        if len(fields) < 5 or fields[1] != "0000":
            return None

        company_name = fields[6].strip() if len(fields) > 6 and fields[6].strip() else cls.FALLBACK_COMPANY_NAME
        
        raw_cnpj = fields[7].strip() if len(fields) > 7 and fields[7].strip() else ""
        cnpj_issuer = re.sub(r"\D", "", raw_cnpj) or cls.FALLBACK_CNPJ

        return {
            "fields": len(fields),
            "company_name": company_name,
            "cnpj_issuer": cnpj_issuer
        }

    @classmethod
    def _parse_record_c100(cls, line_c100: str) -> Optional[dict]:
        fields = line_c100.split(cls.RECORD_DELIMITER)

        if len(fields) < 14:
            return None

        operation_type = fields[2].strip()
        if operation_type != cls.OPERATION_TYPE_OUTGOING:
            return None

        standard_key = fields[9].strip() if len(fields) > 9 else ""
        shifted_key = fields[10].strip() if len(fields) > 10 else ""
        if len(standard_key) == cls.ACCESS_KEY_LENGTH:
            key_index, status_index, date_index, value_index, environment_indices = 9, 6, 10, 12, (26,)
        elif len(shifted_key) == cls.ACCESS_KEY_LENGTH:
            key_index, status_index, date_index, value_index, environment_indices = 10, 7, 11, 13, (27, 26)
        else:
            return None

        document_status = fields[status_index].strip() or "00"
        if document_status == cls.DOCUMENT_STATUS_CANCELLED:
            return None

        if any(len(fields) > idx and fields[idx].strip() == cls.TP_AMB_HOMOLOGATION for idx in environment_indices):
            return None

        access_key = fields[key_index].strip()
        emission_date = cls._format_date(fields[date_index])
        total_value_cents = cls._convert_to_cents(fields[value_index])

        return {
            "access_key": access_key,
            "value": total_value_cents,
            "emission_date": emission_date,
        }

    @classmethod
    def parse_sped_content(cls, sped_content: str, sped_batch: list) -> None:
        parsed_0000: Optional[dict] = None
        record_0000_number_fields: Optional[int] = None
        sped_type: bool = False  # False -> SPED_COFINS (>=18 campos) | True -> SPED_FISCAL (<18 campos)

        lines = sped_content.splitlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            fields = line.split(cls.RECORD_DELIMITER)
            if len(fields) < 2:
                continue

            match fields[1]:
                case "0000":
                    parsed_0000 = cls._parse_record_0000(line)
                    if parsed_0000:
                        record_0000_number_fields = parsed_0000.get("fields")
                        if record_0000_number_fields is not None:
                            sped_type = False if record_0000_number_fields >= 18 else True

                        cls.company_name = parsed_0000.get("company_name")
                        cls.cnpj_issuer = parsed_0000.get("cnpj_issuer")

                case "C100":
                    parsed_c100 = cls._parse_record_c100(line)

                    if not parsed_c100 or not parsed_0000 or record_0000_number_fields is None:
                        continue

                    record_tuple = (
                        parsed_c100.get("access_key"),
                        parsed_c100.get("value"),
                        sped_type,
                        parsed_c100.get("emission_date"),
                    )

                    sped_batch.append(record_tuple)

                case _:
                    continue

    @classmethod
    def get_company_name(cls) -> str:
        if cls.company_name:
            return cls.company_name
        raise BrokenPipeError("VERIFIQUE A PIPELINE: NOME DA EMPRESA NÃO ENCONTRADO")

    @classmethod
    def get_cnpj(cls) -> str:
        if cls.cnpj_issuer:
            return cls.cnpj_issuer
        raise BrokenPipeError("VERIFIQUE A PIPELINE: CNPJ DA EMPRESA NÃO ENCONTRADO")