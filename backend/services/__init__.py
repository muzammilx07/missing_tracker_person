"""Services package for Missing Person Tracker."""

from .cloudinary_service import upload_photo
from .geo_service import reverse_geocode, geocode_address, find_police_stations, haversine
from .face_service import (
    extract_encoding,
    compare_encodings,
    run_face_match,
    get_confidence_label,
    match_against_open_cases,
    prepare_image_bytes_for_processing,
    log_memory_snapshot,
    warmup_face_models,
    is_face_engine_available,
    face_engine_unavailable_reason,
)
from .fir_service import generate_fir_pdf
from .alert_service import (
    get_alert_recipients, log_alert, notify_match_found, 
    notify_fir_sent, notify_case_opened
)

__all__ = [
    "upload_photo",
    "reverse_geocode",
    "geocode_address",
    "find_police_stations",
    "haversine",
    "extract_encoding",
    "compare_encodings",
    "run_face_match",
    "get_confidence_label",
    "match_against_open_cases",
    "prepare_image_bytes_for_processing",
    "log_memory_snapshot",
    "warmup_face_models",
    "is_face_engine_available",
    "face_engine_unavailable_reason",
    "generate_fir_pdf",
    "get_alert_recipients",
    "log_alert",
    "notify_match_found",
    "notify_fir_sent",
    "notify_case_opened",
]
