CREATE_TEMP_TABLES = """
CREATE TEMP TABLE IF NOT EXISTS xml (
    access_key    VARCHAR(44) PRIMARY KEY,
    cnpj_issuer   VARCHAR(14),
    value         BIGINT,
    nfe_series    VARCHAR(3),
    nfe_number    VARCHAR(6),
    emission_date DATE
);

CREATE TEMP TABLE IF NOT EXISTS sped (
    access_key    VARCHAR(44),
    value         BIGINT,
    sped_type     BOOLEAN,
    emission_date DATE,
    PRIMARY KEY (access_key, sped_type)
);

CREATE TEMP TABLE IF NOT EXISTS sintegra (
    cnpj_issuer   VARCHAR(14),
    value         BIGINT,
    nfe_model     VARCHAR(2),
    nfe_series    VARCHAR(3),
    nfe_number    VARCHAR(6),
    emission_date DATE,
    PRIMARY KEY (cnpj_issuer, nfe_series, nfe_number)
);
"""