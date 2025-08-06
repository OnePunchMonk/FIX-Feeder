from prometheus_client import Counter

MESSAGES_INGESTED = Counter(
    'fix_messages_ingested_total',
    'Total number of FIX messages successfully parsed'
)

PARSE_ERRORS = Counter(
    'fix_parse_errors_total',
    'Total number of FIX messages that failed to parse'
)