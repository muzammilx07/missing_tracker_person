"""
Face recognition service implemented with DeepFace.
Handles face preprocessing, embedding extraction, and matching.
"""

import gc
import io
import logging
import pickle
import threading
import tracemalloc
from typing import BinaryIO, Dict, List, Optional

import numpy as np
from PIL import Image
from sqlalchemy.orm import Session

try:
    from deepface import DeepFace
    FACE_ENGINE_AVAILABLE = True
except ImportError as exc:
    FACE_ENGINE_AVAILABLE = False
    print(f"[FACE] WARNING: DeepFace not available: {str(exc)}")

from config import settings
from models import Alert, Case, Match, MissingPerson, Sighting

logger = logging.getLogger(__name__)

FACE_MODEL_NAME = "Facenet"
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_INPUT_DIMENSION = 2000
PROCESSING_MAX_DIMENSION = 640

_FACE_PROCESSING_SEMAPHORE = threading.BoundedSemaphore(value=1)
_MODEL_WARMUP_LOCK = threading.Lock()
_MODELS_WARMED = False

if not tracemalloc.is_tracing():
    tracemalloc.start(25)


def log_memory_snapshot(stage: str) -> None:
    """Log current and peak Python memory usage for face-processing telemetry."""
    try:
        current, peak = tracemalloc.get_traced_memory()
        logger.info(
            "[MEM] stage=%s current_mb=%.2f peak_mb=%.2f",
            stage,
            current / (1024 * 1024),
            peak / (1024 * 1024),
        )
    except Exception:
        pass


def prepare_image_bytes_for_processing(file_obj: BinaryIO) -> bytes:
    """Validate and resize uploaded image into a compact RGB JPEG byte buffer."""

    try:
        file_obj.seek(0, 2)
        size_bytes = file_obj.tell()
        file_obj.seek(0)
    except Exception:
        size_bytes = None

    if size_bytes is not None and size_bytes > MAX_UPLOAD_BYTES:
        raise ValueError("Image is too large. Maximum allowed size is 5MB")

    try:
        image = Image.open(file_obj)
    except Exception as exc:
        raise ValueError(f"Invalid image file: {str(exc)}")

    try:
        width, height = image.size
        if max(width, height) > MAX_INPUT_DIMENSION:
            raise ValueError("Image dimensions too large. Maximum allowed dimension is 2000px")

        if image.mode != "RGB":
            image = image.convert("RGB")

        if max(image.size) > PROCESSING_MAX_DIMENSION:
            image.thumbnail((PROCESSING_MAX_DIMENSION, PROCESSING_MAX_DIMENSION), Image.Resampling.BILINEAR)

        optimized = io.BytesIO()
        image.save(optimized, format="JPEG", quality=85, optimize=True)
        prepared_bytes = optimized.getvalue()
    finally:
        try:
            image.close()
        except Exception:
            pass

    if len(prepared_bytes) > MAX_UPLOAD_BYTES:
        raise ValueError("Image is too large after processing. Please upload a smaller image")

    return prepared_bytes


def warmup_face_models() -> None:
    """Warm DeepFace model once at startup to avoid first-request latency spikes."""

    global _MODELS_WARMED

    if not FACE_ENGINE_AVAILABLE or _MODELS_WARMED:
        return

    with _MODEL_WARMUP_LOCK:
        if _MODELS_WARMED:
            return
        try:
            sample = np.zeros((64, 64, 3), dtype=np.uint8)
            DeepFace.represent(
                img_path=sample,
                model_name=FACE_MODEL_NAME,
                detector_backend="opencv",
                enforce_detection=False,
            )
            _MODELS_WARMED = True
            logger.info("[FACE] DeepFace model warmup complete")
        except Exception as exc:
            logger.warning(f"[FACE] DeepFace warmup skipped: {str(exc)}")


def _pick_largest_face(image_array: np.ndarray) -> Optional[np.ndarray]:
    """Return the largest detected face crop from an image."""
    faces = DeepFace.extract_faces(
        img_path=image_array,
        detector_backend="opencv",
        enforce_detection=False,
        align=True,
    )

    if not faces:
        return None

    best_face = max(
        faces,
        key=lambda face: int(face.get("facial_area", {}).get("w", 1)) * int(face.get("facial_area", {}).get("h", 1)),
    )
    face_img = best_face.get("face")
    if face_img is None:
        return None

    # DeepFace can return float in [0,1]; convert to uint8 for consistent downstream behavior.
    if face_img.dtype != np.uint8:
        face_img = np.clip(face_img * 255.0, 0, 255).astype(np.uint8)
    return face_img


def extract_encoding(image_bytes: bytes) -> Optional[bytes]:
    """Extract a normalized face embedding from image bytes using DeepFace."""

    if not FACE_ENGINE_AVAILABLE:
        logger.warning("[FACE] DeepFace library not available")
        return None

    try:
        log_memory_snapshot("extract:start")

        with _FACE_PROCESSING_SEMAPHORE:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            if max(image.size) > PROCESSING_MAX_DIMENSION:
                image.thumbnail((PROCESSING_MAX_DIMENSION, PROCESSING_MAX_DIMENSION), Image.Resampling.BILINEAR)

            image_array = np.asarray(image, dtype=np.uint8)
            selected_face = _pick_largest_face(image_array)
            if selected_face is None:
                logger.info("[FACE] No face detected in image")
                return None

            representations = DeepFace.represent(
                img_path=selected_face,
                model_name=FACE_MODEL_NAME,
                detector_backend="skip",
                enforce_detection=False,
            )

            if not representations:
                logger.info("[FACE] No embedding generated")
                return None

            embedding = np.asarray(representations[0].get("embedding", []), dtype=np.float32)
            if embedding.size == 0:
                logger.info("[FACE] Empty embedding generated")
                return None

            norm = np.linalg.norm(embedding)
            if norm == 0:
                logger.warning("[FACE] Invalid zero-norm embedding")
                return None

            embedding = embedding / norm
            return pickle.dumps(embedding)

    except Exception as exc:
        logger.error(f"[FACE] DeepFace extraction error: {str(exc)}")
        return None
    finally:
        try:
            del image
        except Exception:
            pass
        try:
            del image_array
        except Exception:
            pass
        try:
            del selected_face
        except Exception:
            pass
        try:
            del representations
        except Exception:
            pass
        try:
            del embedding
        except Exception:
            pass
        gc.collect()
        log_memory_snapshot("extract:end")


def compare_encodings(enc1_bytes: bytes, enc2_bytes: bytes) -> float:
    """Compare two stored embeddings with cosine similarity."""

    if not FACE_ENGINE_AVAILABLE:
        logger.warning("[FACE] DeepFace library not available")
        return 0.0

    try:
        emb1 = np.asarray(pickle.loads(enc1_bytes), dtype=np.float32)
        emb2 = np.asarray(pickle.loads(enc2_bytes), dtype=np.float32)

        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        if norm1 == 0 or norm2 == 0:
            logger.warning("[FACE] Zero-norm embedding encountered during comparison")
            return 0.0

        emb1 = emb1 / norm1
        emb2 = emb2 / norm2

        similarity = float(np.dot(emb1, emb2))
        return round(max(-1.0, min(1.0, similarity)), 4)
    except Exception as exc:
        logger.error(f"[FACE] Embedding comparison error: {str(exc)}")
        return 0.0


def get_confidence_label(confidence: float) -> str:
    """Get human-readable confidence label."""

    if confidence > 0.85:
        return "high"
    if confidence > 0.75:
        return "medium"
    if confidence > 0.60:
        return "low"
    return "none"


def match_against_open_cases(sighting_encoding: bytes, db: Session, limit: int = 5) -> List[Dict]:
    """Match a sighting embedding against all case embeddings without persisting a sighting first."""

    if not sighting_encoding:
        return []

    missing_persons = db.query(MissingPerson).filter(MissingPerson.face_encoding.isnot(None)).all()

    results: List[Dict] = []

    for mp in missing_persons:
        similarity = compare_encodings(sighting_encoding, mp.face_encoding)
        logger.info(f"[FACE] case_id={mp.case_id} similarity_score={similarity:.4f}")

        if similarity > settings.FACE_REVIEW_THRESHOLD:
            results.append(
                {
                    "case_id": mp.case_id,
                    "mp_id": mp.id,
                    "confidence": similarity,
                    "label": get_confidence_label(similarity),
                }
            )

    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results[:limit]


def run_face_match(sighting_id: int, db: Session) -> List[Dict]:
    """Run face matching for a sighting against all open cases."""

    if not FACE_ENGINE_AVAILABLE:
        logger.warning("[FACE] DeepFace library not available, skipping match")
        return []

    try:
        sighting = db.query(Sighting).filter(Sighting.id == sighting_id).first()

        if not sighting:
            logger.error(f"[FACE] Sighting {sighting_id} not found")
            return []

        if not sighting.face_encoding:
            logger.info(f"[FACE] Sighting {sighting_id} has no embedding")
            sighting.status = "no_face"
            db.commit()
            return []

        sighting.status = "processing"
        db.commit()

        missing_persons = (
            db.query(MissingPerson)
            .join(Case, MissingPerson.case_id == Case.id)
            .filter(Case.status == "open", MissingPerson.face_encoding.isnot(None))
            .all()
        )

        results = []

        for mp in missing_persons:
            try:
                confidence = compare_encodings(sighting.face_encoding, mp.face_encoding)
                if confidence >= settings.FACE_REVIEW_THRESHOLD:
                    results.append(
                        {
                            "case_id": mp.case_id,
                            "mp_id": mp.id,
                            "confidence": confidence,
                            "label": get_confidence_label(confidence),
                        }
                    )
            except Exception as exc:
                logger.error(f"[FACE] Error comparing with MP {mp.id}: {str(exc)}")
                continue

        results.sort(key=lambda x: x["confidence"], reverse=True)
        results = results[:5]

        for result in results:
            try:
                match_type = "auto" if result["confidence"] >= settings.FACE_AUTO_THRESHOLD else "review"
                status = "auto_confirmed" if match_type == "auto" else "pending"

                match = Match(
                    case_id=result["case_id"],
                    sighting_id=sighting_id,
                    confidence=result["confidence"],
                    confidence_label=result["label"],
                    match_type=match_type,
                    status=status,
                )
                db.add(match)

                if match_type == "auto":
                    case = db.query(Case).filter(Case.id == result["case_id"]).first()
                    if case:
                        case.status = "matched"
                        case.priority = "critical"

                        mp = db.query(MissingPerson).filter(MissingPerson.id == result["mp_id"]).first()
                        mp_name = mp.full_name if mp else "Unknown"

                        alert = Alert(
                            case_id=result["case_id"],
                            match_id=match.id,
                            alert_type="match_found",
                            recipient_type="all",
                            message=f"AUTO MATCH {result['confidence']*100:.0f}%: {mp_name} — {sighting.sighting_city or 'Unknown city'}",
                        )
                        db.add(alert)

                db.flush()
            except Exception as exc:
                logger.error(f"[FACE] Error creating match for Case {result['case_id']}: {str(exc)}")
                continue

        sighting.status = "matched" if results else "no_match"
        db.commit()

        return results

    except Exception as exc:
        logger.error(f"[FACE] Critical error in face matching: {str(exc)}")
        try:
            sighting = db.query(Sighting).filter(Sighting.id == sighting_id).first()
            if sighting:
                sighting.status = "error"
                db.commit()
        except Exception:
            pass
        return []
