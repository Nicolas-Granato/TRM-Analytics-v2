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
SELECT 
    x.access_key AS xml_access_key,
    COALESCE(x.cnpj_issuer, st.cnpj_issuer) AS cnpj_issuer,
    COALESCE(SUBSTR(x.access_key, 21, 2), st.nfe_model) AS nfe_model,
    COALESCE(x.nfe_series, st.nfe_series) AS nfe_series,
    COALESCE(x.nfe_number, st.nfe_number) AS nfe_number,
    x.value AS xml_value,
    st.value AS sintegra_value,
    (COALESCE(x.value, 0) - COALESCE(st.value, 0)) AS value_difference,
    CAST(x.emission_date AS VARCHAR) AS xml_emission_date,
    CAST(st.emission_date AS VARCHAR) AS sintegra_emission_date,
    CASE 
        WHEN x.access_key IS NULL THEN 'NOTA_PRESENTE_APENAS_NO_SINTEGRA'
        WHEN st.cnpj_issuer IS NULL THEN 'NOTA_PRESENTE_APENAS_NO_XML'
        WHEN x.value <> st.value THEN 'DIVERGENCIA_DE_VALOR'
    END AS divergence_type
FROM xml x
FULL OUTER JOIN sintegra st 
    ON x.cnpj_issuer = st.cnpj_issuer
   AND SUBSTR(x.access_key, 21, 2) = st.nfe_model
   AND x.nfe_series = st.nfe_series
   AND x.nfe_number = st.nfe_number
WHERE x.access_key IS NULL 
   OR st.cnpj_issuer IS NULL 
   OR x.value <> st.value;
"""