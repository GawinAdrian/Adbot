"""Capability-led adapters for normalized Claude Ads inputs."""

from .base import (
    Adapter,
    AdapterCapabilities,
    AdapterError,
    BaseAdapter,
    Capability,
    MutationDisabledError,
)
from .csv_export import CSVExportError, GenericCSVExportAdapter
from .google_keyword_ideas import (
    GoogleKeywordIdeasAdapter,
    GoogleKeywordIdeasError,
)
from .google_live import (
    GoogleAdsLiveReadAdapter,
    GoogleLiveReadError,
    SUPPORTED_LIVE_QUERIES,
    flatten_gaql_row,
)
from .mappings_v1 import (
    NativeDateCheck,
    NativeExportProfile,
    NativeFieldMapping,
    NativeValueGuard,
    get_native_profile,
)
from .native_export import NativeCSVExportAdapter, NativeExportError

__all__ = [
    "Adapter",
    "AdapterCapabilities",
    "AdapterError",
    "BaseAdapter",
    "CSVExportError",
    "Capability",
    "GenericCSVExportAdapter",
    "GoogleAdsLiveReadAdapter",
    "GoogleKeywordIdeasAdapter",
    "GoogleKeywordIdeasError",
    "GoogleLiveReadError",
    "SUPPORTED_LIVE_QUERIES",
    "MutationDisabledError",
    "NativeCSVExportAdapter",
    "NativeDateCheck",
    "NativeExportError",
    "NativeExportProfile",
    "NativeFieldMapping",
    "NativeValueGuard",
    "flatten_gaql_row",
    "get_native_profile",
]
