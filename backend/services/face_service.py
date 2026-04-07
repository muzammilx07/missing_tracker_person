"""
Face recognition service for detecting, encoding, and matching faces.
Uses face_recognition library for accurate face detection and encoding.

NOTE: face_recognition library has complex dependencies (dlib).
On Windows: pip install face_recognition (should work)
On Linux: May need: apt-get install cmake, then pip install dlib face_recognition
"""

import pickle
import logging
from typing import Optional, List, Dict, BinaryIO
import gc
import threading
import tracemalloc
from sqlalchemy.orm import Session
import numpy as np

# Try to import optional dependencies
try:
    import face_recognition
    from PIL import Image
    import io
    FACE_RECOGNITION_AVAILABLE = True
except ImportError as e:
    FACE_RECOGNITION_AVAILABLE = False
    print(f"[FACE] WARNING: face_recognition not available: {str(e)}")

from config import settings
from models import Sighting, MissingPerson, Match, Case, Alert

logger = logging.getLogger(__name__)

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
        # Memory telemetry must never interrupt request handling.
        pass


def prepare_image_bytes_for_processing(file_obj: BinaryIO) -> bytes:
    """Validate and resize uploaded image into a compact RGB JPEG byte buffer."""

    if not FACE_RECOGNITION_AVAILABLE:
        raise ValueError("Face recognition dependencies are unavailable")

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
    """Warm dlib/face_recognition models once to avoid first-request memory spikes."""

    global _MODELS_WARMED

    if not FACE_RECOGNITION_AVAILABLE or _MODELS_WARMED:
        return

    with _MODEL_WARMUP_LOCK:
        if _MODELS_WARMED:
            return
        try:
            sample = np.zeros((32, 32, 3), dtype=np.uint8)
            face_recognition.face_locations(sample, number_of_times_to_upsample=0, model="hog")
            _MODELS_WARMED = True
            logger.info("[FACE] Model warmup complete")
        except Exception as exc:
            logger.warning(f"[FACE] Model warmup skipped: {str(exc)}")


def extract_encoding(image_bytes: bytes) -> Optional[bytes]:
    """
    Extract face encoding from image bytes.
    
    Args:
        image_bytes: Raw image file content
    
    Returns:
        Pickled encoding (bytes), or None if no face found or lib not available
    """
    
    if not FACE_RECOGNITION_AVAILABLE:
        logger.warning("[FACE] face_recognition library not available")
        return None

    try:
        log_memory_snapshot("extract:start")

        with _FACE_PROCESSING_SEMAPHORE:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            if max(image.size) > PROCESSING_MAX_DIMENSION:
                image.thumbnail((PROCESSING_MAX_DIMENSION, PROCESSING_MAX_DIMENSION), Image.Resampling.BILINEAR)

            image_array = np.asarray(image, dtype=np.uint8)

            # Single-pass detection with HOG and no upscaling avoids large temporary allocations.
            face_locations = face_recognition.face_locations(
                image_array,
                number_of_times_to_upsample=0,
                model="hog",
            )

            if not face_locations:
                logger.info("[FACE] No face detected in image")
                return None

            if len(face_locations) > 1:
                best_location = max(
                    face_locations,
                    key=lambda loc: (loc[2] - loc[0]) * (loc[1] - loc[3]),
                )
                logger.info(f"[FACE] Multiple faces found, using largest of {len(face_locations)}")
            else:
                best_location = face_locations[0]

            # Extract only one face encoding.
            encodings = face_recognition.face_encodings(image_array, [best_location])

            if not encodings:
                logger.warning("[FACE] Could not extract encoding from face")
                return None

            encoding = np.asarray(encodings[0], dtype=np.float32)

            norm = np.linalg.norm(encoding)
            if norm == 0:
                logger.warning("[FACE] Invalid zero-norm embedding")
                return None
            encoding = encoding / norm

            return pickle.dumps(encoding)
    
    except Exception as e:
        logger.error(f"[FACE] Encoding extraction error: {str(e)}")
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
            del face_locations
        except Exception:
            pass
        try:
            del encodings
        except Exception:
            pass
        try:
            del encoding
        except Exception:
            pass
        gc.collect()
        log_memory_snapshot("extract:end")


def compare_encodings(enc1_bytes: bytes, enc2_bytes: bytes) -> float:
    """
    Compare two face encodings.
    
    Args:
        enc1_bytes: Pickled encoding 1
        enc2_bytes: Pickled encoding 2
    
    Returns:
        Cosine similarity score (-1.0 to 1.0), where higher = more similar
    """
    
    if not FACE_RECOGNITION_AVAILABLE:
        logger.warning("[FACE] face_recognition library not available")
        return 0.0
    
    try:
        enc1 = np.array(pickle.loads(enc1_bytes), dtype=np.float32)
        enc2 = np.array(pickle.loads(enc2_bytes), dtype=np.float32)

        # Keep compatibility if old non-normalized embeddings exist in DB.
        norm1 = np.linalg.norm(enc1)
        norm2 = np.linalg.norm(enc2)
        if norm1 == 0 or norm2 == 0:
            logger.warning("[FACE] Zero-norm embedding encountered during comparison")
            return 0.0

        enc1 = enc1 / norm1
        enc2 = enc2 / norm2

        # True cosine similarity in [-1, 1].
        cosine_similarity = float(np.dot(enc1, enc2))
        return round(max(-1.0, min(1.0, cosine_similarity)), 4)
    
    except Exception as e:
        logger.error(f"[FACE] Encoding comparison error: {str(e)}")
        return 0.0


def get_confidence_label(confidence: float) -> str:
    """
    Get human-readable confidence label.
    
    Args:
        confidence: Score 0.0-1.0
    
    Returns:
        Label: "low", "medium", "high", or "very_high"
    """
    
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

        if similarity > 0.60:
            results.append({
                "case_id": mp.case_id,
                "mp_id": mp.id,
                "confidence": similarity,
                "label": get_confidence_label(similarity),
            })

    results.sort(key=lambda x: x["confidence"], reverse=True)
    return results[:limit]


def run_face_match(sighting_id: int, db: Session) -> List[Dict]:
    """
    Run face matching for a sighting against all open cases.
    
    Process:
    1. Fetch sighting, mark as processing
    2. Extract all missing persons with face encodings from open cases
    3. Compare faces, collect matches above FACE_REVIEW_THRESHOLD (0.55)
    4. Auto-confirm if confidence >= FACE_AUTO_THRESHOLD (0.85)
    5. Create Match records + Alerts + update Case status
    6. Return match results
    
    Args:
        sighting_id: ID of sighting to match
        db: Database session
    
    Returns:
        List of match results (top 5):
        [{
            "case_id": int,
            "mp_id": int,
            "confidence": float,
            "label": str,
            "auto_confirmed": bool
        }]
    """
    
    if not FACE_RECOGNITION_AVAILABLE:
        logger.warning("[FACE] face_recognition library not available, skipping match")
        return []
    
    try:
        # Fetch sighting
        sighting = db.query(Sighting).filter(Sighting.id == sighting_id).first()
        
        if not sighting:
            logger.error(f"[FACE] Sighting {sighting_id} not found")
            return []
        
        # Check if face encoding exists
        if not sighting.face_encoding:
            logger.info(f"[FACE] Sighting {sighting_id} has no face encoding")
            sighting.status = "no_face"
            db.commit()
            return []
        
        # Mark as processing
        sighting.status = "processing"
        db.commit()
        
        logger.info(f"[FACE] Matching sighting {sighting_id} against open cases")
        
        # Fetch all missing persons from open cases with face encodings
        missing_persons = db.query(MissingPerson).join(
            Case, MissingPerson.case_id == Case.id
        ).filter(
            Case.status == "open",
            MissingPerson.face_encoding.isnot(None)
        ).all()
        
        logger.info(f"[FACE] Found {len(missing_persons)} open cases with face encodings")
        
        results = []
        
        # Compare against each missing person
        for mp in missing_persons:
            try:
                confidence = compare_encodings(sighting.face_encoding, mp.face_encoding)
                logger.info(
                    f"[FACE] Similarity sighting={sighting_id} vs case={mp.case_id} mp={mp.id}: {confidence:.4f}"
                )
                
                if confidence >= settings.FACE_REVIEW_THRESHOLD:
                    label = get_confidence_label(confidence)
                    results.append({
                        "case_id": mp.case_id,
                        "mp_id": mp.id,
                        "confidence": confidence,
                        "label": label
                    })
                    
                    logger.info(f"[FACE] Match found: Case {mp.case_id}, confidence {confidence:.2%}")
            
            except Exception as e:
                logger.error(f"[FACE] Error comparing with MP {mp.id}: {str(e)}")
                continue
        
        # Sort by confidence descending, keep top 5
        results.sort(key=lambda x: x["confidence"], reverse=True)
        results = results[:5]
        
        # Create Match records and handle auto-confirm logic
        for r in results:
            try:
                match_type = "auto" if r["confidence"] >= settings.FACE_AUTO_THRESHOLD else "review"
                status = "auto_confirmed" if match_type == "auto" else "pending"
                
                # Create Match record
                match = Match(
                    case_id=r["case_id"],
                    sighting_id=sighting_id,
                    confidence=r["confidence"],
                    confidence_label=r["label"],
                    match_type=match_type,
                    status=status
                )
                db.add(match)
                
                logger.info(f"[FACE] Created {match_type} Match for Case {r['case_id']}")
                
                # If auto-confirm, update case and create alert
                if match_type == "auto":
                    case = db.query(Case).filter(Case.id == r["case_id"]).first()
                    if case:
                        case.status = "matched"
                        case.priority = "critical"
                        
                        # Get missing person name
                        mp = db.query(MissingPerson).filter(MissingPerson.id == r["mp_id"]).first()
                        mp_name = mp.full_name if mp else "Unknown"
                        
                        # Create alert
                        alert = Alert(
                            case_id=r["case_id"],
                            match_id=match.id,
                            alert_type="match_found",
                            recipient_type="all",
                            message=f"AUTO MATCH {r['confidence']*100:.0f}%: {mp_name} — {sighting.city or 'Unknown city'}"
                        )
                        db.add(alert)
                        
                        logger.info(f"[FACE] Auto-match confirmed for Case {r['case_id']}, alert created")
                
                db.flush()
            
            except Exception as e:
                logger.error(f"[FACE] Error creating match for Case {r['case_id']}: {str(e)}")
                continue
        
        # Update sighting status based on results
        sighting.status = "matched" if results else "no_match"
        db.commit()
        
        logger.info(f"[FACE] Sighting {sighting_id} matching complete, found {len(results)} matches")
        
        return results
    
    except Exception as e:
        logger.error(f"[FACE] Critical error in face matching: {str(e)}")
        try:
            sighting = db.query(Sighting).filter(Sighting.id == sighting_id).first()
            if sighting:
                sighting.status = "error"
                db.commit()
        except:
            pass
        return []
