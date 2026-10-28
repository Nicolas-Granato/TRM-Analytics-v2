from typing import Optional, Any


class SintegraParser:
    DIRECTION_TYPE = {
        "T": "ENTRADA",
        "P": "SAIDA"
    }

    STATUS_CODE_CANCELLED = ("C", "S", "X", "2", "4")

    FALLBACK_COMPANY_NAME = "EMPRESA_NAO_IDENTIFICADA"
    FALLBACK_DATE = "1970-01-01"
    FALLBACK_CNPJ = "00000000000000"

    company_name: Optional[str] = None
    company_cnpj: Optional[str] = None

    @classmethod
    def _format_date(cls, raw_date: str) -> str:
        raw_date = raw_date.strip()
        if len(raw_date) == 8 and raw_date.isdigit():
            year, month, day = raw_date[0:4], raw_date[4:6], raw_date[6:8]
            if 1 <= int(month) <= 12 and 1 <= int(day) <= 31 and int(year) >= 1900:
                return f"{year}-{month}-{day}"
        return cls.FALLBACK_DATE

    @classmethod
    def _parse_record_10(cls, line_10: str) -> Optional[dict]:
        if len(line_10) < 125 or not line_10.startswith("10"):
            return None

        company_name = line_10[30:65].strip() or cls.FALLBACK_COMPANY_NAME
        company_cnpj = line_10[2:16].strip().zfill(14)

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

        cnpj_issuer = line_50[2:16].strip().zfill(14)
        emission_date = line_50[30:38].strip()
        nfe_model = line_50[40:42].strip() or "55"
        nfe_series = line_50[42:45].strip().zfill(3)
        nfe_number = line_50[45:51].strip().zfill(9)

        return {
            "cnpj_issuer": cnpj_issuer,
            "nfe_model": nfe_model,
            "nfe_series": nfe_series,
            "nfe_number": nfe_number,
            "value": 0,
            "emission_date": cls._format_date(emission_date)
        }

    @classmethod
    def _parse_record_54(cls, line_54: str) -> Optional[dict]:
        if len(line_54) < 126 or not line_54.startswith("54"):
            return None

        series_number = line_54[18:21].strip().zfill(3)
        document_number = line_54[21:27].strip().zfill(9)

        if not (series_number and document_number):
            return None

        raw_value = line_54[62:74].strip()
        value_cents = int(raw_value) if raw_value.isdigit() else 0
        
        raw_discounts = line_54[74:86].strip()
        discounts_value_cents = int(raw_discounts) if raw_discounts.isdigit() else 0

        product_value_cents = value_cents - discounts_value_cents

        return {
            "series_number": series_number,
            "document_number": document_number,
            "product_value": product_value_cents
        }

    @classmethod
    def _parse_record_61(cls, line_61: str) -> Optional[dict]:
        if len(line_61) < 126 or line_61[:2] != "61" or line_61.startswith("61R"):
            return None

        raw_emission_date = line_61[30:38].strip()
        nfe_model = line_61[38:40].strip() or "65"
        nfe_series = line_61[40:43].strip() or "000"
        
        raw_ord_initial = line_61[45:51].strip()
        nfe_number = raw_ord_initial.zfill(9) if raw_ord_initial and raw_ord_initial != "000000" else raw_emission_date[2:8].zfill(9)

        raw_value = line_61[57:70].strip()
        value = int(raw_value) if raw_value.isdigit() else 0

        return {
            "value": value,
            "nfe_model": nfe_model,
            "nfe_series": nfe_series,
            "nfe_number": nfe_number,
            "emission_date": cls._format_date(raw_emission_date)
        }

    @classmethod
    def parse_sintegra(cls, sintegra_content: str, sintegra_batch: list) -> None:
        parsed_10: Optional[dict] = None
        parsed_50_records: dict[tuple[str, str], dict[str, Any]] = {}
        raw_54_lines: list[str] = []
        parsed_61_records: dict[tuple[str, str, str, str], tuple] = {}
        records_tuples: list[tuple] = []

        lines = sintegra_content.splitlines()

        for line in lines:
            line = line.rstrip("\r\n")
            if not line.strip() or line.startswith("61R"):
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

                    parsed_50_records[key] = {
                        "cnpj_issuer": parsed_50.get("cnpj_issuer"),
                        "value": 0,
                        "nfe_model": parsed_50.get("nfe_model", "55"),
                        "nfe_series": nfe_series,
                        "nfe_number": nfe_number,
                        "emission_date": parsed_50.get("emission_date")
                    }

                case "54":
                    raw_54_lines.append(line)

                case "61":
                    parsed_61 = cls._parse_record_61(line)
                    if not parsed_61:
                        continue

                    key_61 = (
                        parsed_61.get("nfe_model", "65"),
                        parsed_61.get("nfe_series", "000"),
                        parsed_61.get("nfe_number", "000000000"),
                        parsed_61.get("emission_date", cls.FALLBACK_DATE)
                    )

                    parsed_61_records[key_61] = (
                        cls.company_cnpj or cls.FALLBACK_CNPJ,
                        parsed_61.get("value", 0),
                        parsed_61.get("nfe_model", "65"),
                        parsed_61.get("nfe_series", "000"),
                        parsed_61.get("nfe_number", "000000000"),
                        parsed_61.get("emission_date", cls.FALLBACK_DATE)
                    )

                case _:
                    continue

        valid_50_keys = set(parsed_50_records.keys())
        for line_54 in raw_54_lines:
            parsed_54 = cls._parse_record_54(line_54)
            if not parsed_54:
                continue

            series = parsed_54.get("series_number", "")
            document = parsed_54.get("document_number", "")
            value = parsed_54.get("product_value", 0)
            key = (series, document)

            if key in valid_50_keys:
                parsed_50_records[key]["value"] += value

        records_tuples.extend(parsed_61_records.values())

        for doc in parsed_50_records.values():
            doc_tuple = (
                doc.get("cnpj_issuer") or cls.company_cnpj or cls.FALLBACK_CNPJ,
                doc.get("value", 0),
                doc.get("nfe_model", "55"),
                doc.get("nfe_series", ""),
                doc.get("nfe_number", ""),
                doc.get("emission_date", cls.FALLBACK_DATE)
            )
            records_tuples.append(doc_tuple)

        sintegra_batch.extend(records_tuples)

    @classmethod
    def get_company_name(cls) -> str:
        if cls.company_name:
            return cls.company_name
        raise BrokenPipeError("VERIFIQUE A PIPELINE: NOME DA EMPRESA NÃO ENCONTRADO")

    @classmethod
    def get_cnpj(cls) -> str:
        return getattr(cls, 'company_cnpj', None) or cls.FALLBACK_CNPJ