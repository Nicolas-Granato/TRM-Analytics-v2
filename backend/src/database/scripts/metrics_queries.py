XML_METRICS = """
SELECT 
    COUNT(*) AS total_count,
    COALESCE(SUM(value), 0) AS total_value
FROM xml;
"""

SPED_METRICS = """
SELECT 
    COUNT(*) AS total_count,
    COALESCE(SUM(value), 0) AS total_value
FROM sped;
"""

SINTEGRA_METRICS = """
SELECT 
    COALESCE(SUM(value), 0) AS total_value
FROM sintegra;
"""