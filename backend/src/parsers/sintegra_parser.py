from typing import Optional

class SintegraParser:
    DIRECTION_TYPE = {
        "T": "ENTRADA",
        "P": "SAIDA"
    }

    STATUS_CODE_CANCELLED = ("C", "S", "X", "2", "4")

    FALLBACK_COMPANY_NAME = "EMPRESA_NAO_IDENTIFICADA"
    FALLBACK_DATE = "0000-00-00"

    COMPLETE_SERIES = "000000"
    COMPLETE_NUMBER = "000"

    company_name: Optional[str] = None

    @classmethod
    def _format_date(cls, raw_date: str) -> str:
        raw_date = raw_date.strip()
        if len(raw_date) == 8 and raw_date.isdigit():
            year, month, day = raw_date[0:4], raw_date[4:6], raw_date[6:8]
            return f"{year}-{month}-{day}"
        return cls.FALLBACK_DATE
    
    @classmethod
    def _parse_record_10(cls, line_10: str) -> str:
        if len(line_10) < 126 or not line_10.startswith("10"):
            return cls.FALLBACK_COMPANY_NAME

        company_name = line_10[30:65].strip()

        return {
            "company_name": company_name
        }

    @classmethod
    def _parse_record_50(cls, line_50: str) -> Optional[dict]:
        if len(line_50) < 126 or not line_50.startswith("50"):
            return None

        operation_type_code = line_50[55:56].strip()
        if operation_type_code or cls.DIRECTION_TYPE.get(operation_type_code) == "ENTRADA":
            return None

        status_code = line_50[125:126].strip()
        if status_code in cls.STATUS_CODE_CANCELLED:
            return None

        cnpj_issuer = line_50[2:16].strip()
        emission_date = line_50[30:38].strip()
        series_number = line_50[42:45].strip()
        document_number = line_50[45:51].strip()

        return {
            "cnpj_issuer": cnpj_issuer,
            "series_number": series_number,
            "document_number": document_number,
            "emission_date": cls._format_date(emission_date),
        }

    @classmethod
    def _parse_record_54(cls, line_54: str, valid_records_50: list) -> Optional[dict]:
        if len(line_54) < 126 or not line_54.startswith("54"):
            return None

        series_number = line_54[18:21].strip()
        document_number = line_54[21:27].strip()

        if not (series_number and document_number) or (series_number, document_number) not in valid_records_50:
            return None

        raw_qty = line_54[51:62].strip()
        quantity = float(raw_qty) / 1000.0 if raw_qty.isdigit() else 0.0

        raw_value = line_54[62:74].strip()
        product_value_cents = int(raw_value) if raw_value.isdigit() else 0

        value = quantity*product_value_cents

        return value

    @classmethod
    def _parse_record_61(cls, line_61: str) -> Optional[dict]:
        if len(line_61) < 126 or not line_61.startswith("61"):
            return None
        
        raw_value = line_61[57:70]
        value = int(raw_value) if raw_value.isdigit() else 0

        emission_date = cls._format_date(line_61[30:38])

        return {
            "value": value,
            "emission_date": emission_date
        }

    @classmethod
    def parse_sintegra(cls, sintegra_content: str, sintegra_batch: list) -> None:
        parsed_10 = None

        lines = sintegra_content.splitlines()

        for line in lines:
            if not line:
                return None

            if line.startswith("10") and not parsed_10:
                parsed_10 = cls._parse_record_10(line)
                cls.company_name = parsed_10.get("company_name")

            if line.startswith("50"):
                parsed_50 = cls._parse_record_50(line)
                document_data = {
                    "cnpj_issuer": parsed_50.get("cnpj_issuer"),
                    "value": None,
                    "nfe_model": "55",
                    "nfe_series": cls.COMPLETE_SERIES,
                    "nfe_number": cls.COMPLETE_NUMBER,
                    "series_number": parsed_50.get("series_number"),
                    "document_number": parsed_50.get("document_number"),
                    "emission_date": parsed_50.get("emission_date")
                }
            

    @classmethod
    def get_company_name(cls):
        if cls.company_name:
            return cls.company_name
        raise BrokenPipeError(f"VERIFIQUE A PIPELINE: NOME DA EMPRESA NÃO ENCONTRADO")
