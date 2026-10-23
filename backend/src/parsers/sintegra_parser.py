from typing import Optional, Any

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
    company_cnpj: Optional[str] = None

    @classmethod
    def _format_date(cls, raw_date: str) -> str:
        raw_date = raw_date.strip()
        if len(raw_date) == 8 and raw_date.isdigit():
            year, month, day = raw_date[0:4], raw_date[4:6], raw_date[6:8]
            return f"{year}-{month}-{day}"
        return cls.FALLBACK_DATE

    @classmethod
    def _parse_record_10(cls, line_10: str) -> Optional[dict]:
        if len(line_10) < 125 or not line_10.startswith("10"):
            return None

        company_name = line_10[30:65].strip() or cls.FALLBACK_COMPANY_NAME
        company_cnpj = line_10[2:16].strip()

        return {
            "company_name": company_name,
            "company_cnpj": company_cnpj
        }

    @classmethod
    def _parse_record_50(cls, line_50: str) -> Optional[dict]:
        if len(line_50) < 126 or not line_50.startswith("50"):
            return None

        operation_type_code = line_50[55:56].strip()
        if cls.DIRECTION_TYPE.get(operation_type_code) == "ENTRADA":
            return None

        status_code = line_50[125:126].strip()
        if status_code in cls.STATUS_CODE_CANCELLED:
            return None

        cnpj_issuer = line_50[2:16].strip()
        emission_date = line_50[30:38].strip()
        nfe_series = line_50[42:45].strip()
        nfe_number = line_50[45:51].strip()

        return {
            "cnpj_issuer": cnpj_issuer,
            "nfe_series": nfe_series,
            "nfe_number": nfe_number,
            "emission_date": cls._format_date(emission_date)
        }

    @classmethod
    def _parse_record_54(cls, line_54: str, valid_50_keys: Optional[set] = None) -> Optional[dict]:
        if len(line_54) < 126 or not line_54.startswith("54"):
            return None

        series_number = line_54[18:21].strip()
        document_number = line_54[21:27].strip()

        if not (series_number and document_number):
            return None

        if valid_50_keys is not None and (series_number, document_number) not in valid_50_keys:
            return None

        raw_value = line_54[62:74].strip()
        product_value_cents = int(raw_value) if raw_value.isdigit() else 0

        return {
            "series_number": series_number,
            "document_number": document_number,
            "product_value": product_value_cents
        }

    @classmethod
    def _parse_record_61(cls, line_61: str) -> Optional[dict]:
        if len(line_61) < 126 or not line_61.startswith("61"):
            return None

        raw_value = line_61[57:70].strip()
        value = int(raw_value) if raw_value.isdigit() else 0

        emission_date = cls._format_date(line_61[30:38])

        return {
            "value": value,
            "emission_date": emission_date
        }

    @classmethod
    def parse_sintegra(cls, sintegra_content: str, sintegra_batch: list) -> None:
        parsed_10: Optional[dict] = None
        parsed_50_records: dict[tuple[str, str], dict[str, Any]] = {}
        records: list[dict] = []

        lines = sintegra_content.splitlines()

        for line in lines:
            line = line.rstrip("\\r\\n")
            if not line.strip():
                continue

            match line[:2]:
                case "10" if not parsed_10:
                    parsed_10 = cls._parse_record_10(line)
                    if parsed_10:
                        cls.company_name = parsed_10.get("company_name")
                        cls.company_cnpj = parsed_10.get("company_cnpj")

                case "50":
                    parsed_50 = cls._parse_record_50(line)
                    if not parsed_50:
                        continue

                    nfe_series = parsed_50.get("nfe_series", "")
                    nfe_number = parsed_50.get("nfe_number", "")
                    key = (nfe_series, nfe_number)

                    document_data = {
                        "cnpj_issuer": parsed_50.get("cnpj_issuer"),
                        "value": 0,
                        "nfe_model": "55",
                        "nfe_series": nfe_series,
                        "nfe_number": nfe_number,
                        "emission_date": parsed_50.get("emission_date")
                    }

                    parsed_50_records[key] = document_data

                case "54":
                    parsed_54 = cls._parse_record_54(line, set(parsed_50_records.keys()))
                    if not parsed_54:
                        continue

                    series = parsed_54.get("series_number", "")
                    document = parsed_54.get("document_number", "")
                    value = parsed_54.get("product_value", 0)

                    key = (series, document)

                    if key in parsed_50_records:
                        parsed_50_records[key]["value"] += value

                case "61":
                    parsed_61 = cls._parse_record_61(line)
                    if not parsed_61:
                        continue

                    record_61_data = {
                        "cnpj_issuer": cls.company_cnpj,
                        "value": parsed_61.get("value"),
                        "nfe_model": "65",
                        "nfe_series": cls.COMPLETE_SERIES,
                        "nfe_number": cls.COMPLETE_NUMBER,
                        "emission_date": parsed_61.get("emission_date")
                    }
                    records.append(record_61_data)

                case _:
                    continue

        records.extend(parsed_50_records.values())

        sintegra_batch.extend(records)

    @classmethod
    def get_company_name(cls) -> str:
        if cls.company_name:
            return cls.company_name
        raise BrokenPipeError("VERIFIQUE A PIPELINE: NOME DA EMPRESA NÃO ENCONTRADO")