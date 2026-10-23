INSERT_XML = """
INSERT INTO xml (
    access_key,
    cnpj_issuer,
    value,
    nfe_series,
    nfe_number,
    emission_date
) VALUES (?, ?, ?, ?, ?, ?);
"""

INSERT_SPED = """
INSERT INTO sped (
    access_key,
    value,
    sped_type,
    emission_date
) VALUES (?, ?, ?, ?);
"""

INSERT_SINTEGRA = """
INSERT INTO sintegra (
    cnpj_issuer,
    value,
    nfe_model,
    nfe_series,
    nfe_number,
    emission_date
) VALUES (?, ?, ?, ?, ?, ?);
"""