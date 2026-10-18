"""Read-only optional SDK adapters and dependency-free normalizers."""

from .common import DataAdapterError, normalize_security_code
from .edinet import fetch_edinet_documents, normalize_edinet_document, parse_edinet_package
from .jquants import fetch_jquants_daily, normalize_jquants_daily

__all__ = [
    "DataAdapterError",
    "fetch_edinet_documents",
    "fetch_jquants_daily",
    "normalize_edinet_document",
    "normalize_jquants_daily",
    "normalize_security_code",
    "parse_edinet_package",
]
