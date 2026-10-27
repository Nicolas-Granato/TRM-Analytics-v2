AUDIT_SPED_QUERY = """
SELECT 
    COALESCE(x.access_key, s.access_key) AS access_key,
    SUBSTR(COALESCE(x.access_key, s.access_key), 21, 2) AS nfe_model,
    x.value AS xml_value,
    s.value AS sped_value,
    (COALESCE(x.value, 0) - COALESCE(s.value, 0)) AS value_difference,
    CAST(x.emission_date AS VARCHAR) AS xml_emission_date,
    CAST(s.emission_date AS VARCHAR) AS sped_emission_date,
    CASE 
        WHEN x.access_key IS NULL THEN 'NOTA_PRESENTE_APENAS_NO_SPED'
        WHEN s.access_key IS NULL THEN 'NOTA_PRESENTE_APENAS_NO_XML'
        WHEN x.value <> s.value THEN 'DIVERGENCIA_DE_VALOR'
    END AS divergence_type
FROM xml x
FULL OUTER JOIN sped s ON x.access_key = s.access_key
WHERE x.access_key IS NULL 
   OR s.access_key IS NULL 
   OR x.value <> s.value;
"""


AUDIT_SINTEGRA_QUERY = """
WITH
xml_base AS (
    SELECT
        cnpj_issuer,
        SUBSTR(access_key, 21, 2) AS nfe_model,
        SUBSTR(access_key, 23, 3) AS nfe_series,
        SUBSTR(access_key, 26, 9) AS nfe_number,
        value,
        CAST(emission_date AS DATE) AS emission_date
    FROM xml
),

xml_nfe AS (
    SELECT
        cnpj_issuer,
        nfe_model,
        nfe_series,
        nfe_number,
        SUM(value) AS value,
        MIN(emission_date) AS emission_date,
        COUNT(*) AS document_count,
        COUNT(DISTINCT value) AS distinct_values,
        COUNT(DISTINCT emission_date) AS distinct_dates
    FROM xml_base
    WHERE nfe_model <> '65'
    GROUP BY
        cnpj_issuer, nfe_model, nfe_series, nfe_number
),

sintegra_nfe_base AS (
    SELECT
        cnpj_issuer,
        LPAD(TRIM(nfe_model), 2, '0') AS nfe_model,
        LPAD(TRIM(nfe_series), 3, '0') AS nfe_series,
        LPAD(TRIM(nfe_number), 9, '0') AS nfe_number,
        value,
        CAST(emission_date AS DATE) AS emission_date
    FROM sintegra
    WHERE TRY_CAST(TRIM(nfe_model) AS INTEGER) <> 65
),

sintegra_nfe AS (
    SELECT
        cnpj_issuer,
        nfe_model,
        nfe_series,
        nfe_number,
        SUM(value) AS value,
        MIN(emission_date) AS emission_date,
        COUNT(*) AS document_count,
        COUNT(DISTINCT value) AS distinct_values,
        COUNT(DISTINCT emission_date) AS distinct_dates
    FROM sintegra_nfe_base
    GROUP BY
        cnpj_issuer, nfe_model, nfe_series, nfe_number
),

audit_nfe AS (
    SELECT
        COALESCE(x.cnpj_issuer, s.cnpj_issuer) AS cnpj_issuer,
        COALESCE(x.nfe_model, s.nfe_model) AS nfe_model,

        CONCAT(
            'SERIE_', COALESCE(x.nfe_series, s.nfe_series),
            '_NUM_', COALESCE(x.nfe_number, s.nfe_number)
        ) AS composite_key,

        x.value AS xml_value,
        s.value AS sintegra_value,
        COALESCE(x.value, 0) - COALESCE(s.value, 0)
            AS value_difference,

        x.emission_date AS xml_emission_date,
        s.emission_date AS sintegra_emission_date,

        CASE
            WHEN x.cnpj_issuer IS NULL
                THEN 'ALERTA_PRESENTE_APENAS_NO_SINTEGRA'
            WHEN s.cnpj_issuer IS NULL
                THEN 'ALERTA_PRESENTE_APENAS_NO_XML'
            WHEN x.distinct_values > 1 OR x.distinct_dates > 1
                THEN 'ALERTA_XML_CHAVE_DUPLICADA_COM_DIVERGENCIA'
            WHEN s.distinct_values > 1 OR s.distinct_dates > 1
                THEN 'ALERTA_SINTEGRA_CHAVE_DUPLICADA_COM_DIVERGENCIA'
            WHEN x.value <> s.value
                THEN 'ERRO_DIVERGENCIA_DE_VALOR'
            WHEN x.emission_date IS DISTINCT FROM s.emission_date
                THEN 'ALERTA_DIVERGENCIA_DATA_EMISSAO'
        END AS divergence_type

    FROM xml_nfe x
    FULL OUTER JOIN sintegra_nfe s
        ON x.cnpj_issuer = s.cnpj_issuer
       AND x.nfe_model = s.nfe_model
       AND x.nfe_series = s.nfe_series
       AND x.nfe_number = s.nfe_number

    WHERE x.cnpj_issuer IS NULL
       OR s.cnpj_issuer IS NULL
       OR x.value <> s.value
       OR x.emission_date IS DISTINCT FROM s.emission_date
       OR x.distinct_values > 1
       OR x.distinct_dates > 1
       OR s.distinct_values > 1
       OR s.distinct_dates > 1
),

xml_nfce AS (
    SELECT
        cnpj_issuer,
        CAST(emission_date AS DATE) AS emission_date,
        SUM(value) AS value
    FROM xml
    WHERE SUBSTR(access_key, 21, 2) = '65'
    GROUP BY cnpj_issuer, CAST(emission_date AS DATE)
),

sintegra_nfce AS (
    SELECT
        cnpj_issuer,
        CAST(emission_date AS DATE) AS emission_date,
        SUM(value) AS value
    FROM sintegra
    WHERE TRY_CAST(TRIM(nfe_model) AS INTEGER) = 65
    GROUP BY cnpj_issuer, CAST(emission_date AS DATE)
),

audit_nfce AS (
    SELECT
        COALESCE(x.cnpj_issuer, s.cnpj_issuer) AS cnpj_issuer,
        '65' AS nfe_model,
        CONCAT(
            'NFCE_DIARIA_',
            CAST(COALESCE(x.emission_date, s.emission_date) AS VARCHAR)
        ) AS composite_key,

        x.value AS xml_value,
        s.value AS sintegra_value,
        COALESCE(x.value, 0) - COALESCE(s.value, 0)
            AS value_difference,

        x.emission_date AS xml_emission_date,
        s.emission_date AS sintegra_emission_date,

        CASE
            WHEN x.cnpj_issuer IS NULL
                THEN 'ALERTA_RESUMO_61_SEM_XML_NO_DIA'
            WHEN s.cnpj_issuer IS NULL
                THEN 'ALERTA_XML_NFCE_SEM_REGISTRO_61_NO_DIA'
            WHEN x.value <> s.value
                THEN 'ERRO_DIVERGENCIA_VALOR_LOTE_DIARIO'
        END AS divergence_type

    FROM xml_nfce x
    FULL OUTER JOIN sintegra_nfce s
        ON x.cnpj_issuer = s.cnpj_issuer
       AND x.emission_date = s.emission_date

    WHERE x.cnpj_issuer IS NULL
       OR s.cnpj_issuer IS NULL
       OR x.value <> s.value
)

SELECT
    cnpj_issuer,
    nfe_model,
    composite_key,
    xml_emission_date,
    sintegra_emission_date,
    xml_value,
    sintegra_value,
    value_difference,
    divergence_type
FROM audit_nfe

UNION ALL

SELECT
    cnpj_issuer,
    nfe_model,
    composite_key,
    xml_emission_date,
    sintegra_emission_date,
    xml_value,
    sintegra_value,
    value_difference,
    divergence_type
FROM audit_nfce
"""
