"""
Missing Person Tracker - Backend API
FastAPI application with routes for cases, sightings, face matching, and volunteer coordination.
"""

from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form, Query, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import io
import uuid
import logging
import hashlib
import time
import gc

from config import settings
from database import engine, get_db, Base, SessionLocal
from models import (
    User, VolunteerProfile, Case, MissingPerson, Sighting, Match,
    PoliceStation, FIR, PoliceDispatch, Alert, CaseFamilyMember, CaseVolunteer
)
from auth import (
    hash_password, verify_password, create_token,
    get_current_user, require_admin, get_optional_user
)
from services import (
    upload_photo, reverse_geocode, geocode_address, find_police_stations,
    extract_encoding, compare_encodings, run_face_match, get_confidence_label, match_against_open_cases,
    generate_fir_pdf, get_alert_recipients, log_alert, notify_match_found,
    notify_fir_sent, notify_case_opened, prepare_image_bytes_for_processing,
    log_memory_snapshot, warmup_face_models, is_face_engine_available,
    face_engine_unavailable_reason
)

logger = logging.getLogger(__name__)


# Lightweight in-memory anti-spam guard for public sighting submissions.
_SIGHTING_RATE_LIMIT: Dict[str, List[float]] = {}
_RECENT_IMAGE_FINGERPRINTS: Dict[str, float] = {}


def _enforce_sighting_rate_limit(client_key: str, image_bytes: bytes) -> None:
    now = time.time()
    window_seconds = 60
    max_requests = 3

    history = [ts for ts in _SIGHTING_RATE_LIMIT.get(client_key, []) if now - ts < window_seconds]
    if len(history) >= max_requests:
        raise HTTPException(
            status_code=429,
            detail="Too many submissions. Please wait before sending another sighting."
        )
    history.append(now)
    _SIGHTING_RATE_LIMIT[client_key] = history

    fingerprint = hashlib.sha256(image_bytes).hexdigest()
    last_seen = _RECENT_IMAGE_FINGERPRINTS.get(fingerprint)
    if last_seen and (now - last_seen) < 180:
        raise HTTPException(
            status_code=429,
            detail="Duplicate sighting image detected recently. Please avoid repeated submissions."
        )
    _RECENT_IMAGE_FINGERPRINTS[fingerprint] = now


def _next_fir_number(db: Session) -> str:
    year = datetime.utcnow().year
    prefix = f"FIR-{year}-"
    rows = db.query(FIR.fir_number).filter(FIR.fir_number.like(f"{prefix}%")).all()
    max_seq = 0
    for (fir_number,) in rows:
        try:
            seq = int(str(fir_number).split("-")[-1])
            if seq > max_seq:
                max_seq = seq
        except Exception:
            continue
    return f"{prefix}{max_seq + 1:06d}"


def _resolve_case_location(db: Session, case: Case) -> Dict:
    """Resolve best available coordinates for case operations.

    Priority:
    1) Missing person last seen coordinates
    2) Latest match's sighting coordinates
    """
    mp = case.missing_person if case else None
    if mp and mp.last_seen_lat is not None and mp.last_seen_lng is not None:
        return {
            "lat": mp.last_seen_lat,
            "lng": mp.last_seen_lng,
            "city": mp.last_seen_city,
            "state": mp.last_seen_state,
            "source": "missing_person_last_seen",
        }

    latest_match = db.query(Match).filter(Match.case_id == case.id).order_by(desc(Match.created_at)).first() if case else None
    latest_sighting = latest_match.sighting if latest_match else None
    if latest_sighting and latest_sighting.sighting_lat is not None and latest_sighting.sighting_lng is not None:
        return {
            "lat": latest_sighting.sighting_lat,
            "lng": latest_sighting.sighting_lng,
            "city": latest_sighting.sighting_city,
            "state": latest_sighting.sighting_state,
            "source": "latest_match_sighting",
        }

    return {
        "lat": None,
        "lng": None,
        "city": None,
        "state": None,
        "source": "unknown",
    }


def _find_stations_with_expanding_radius(lat: float, lng: float, limit: int = 10, base_radius_km: float = 5.0):
    """Try nearby station search with progressively wider radius."""
    base = max(1.0, float(base_radius_km))
    radius_steps_km = [base, max(base, 10.0), max(base, 20.0), max(base, 40.0)]

    for radius_km in radius_steps_km:
        stations = find_police_stations(lat, lng, radius_meters=int(radius_km * 1000))[:limit]
        if stations:
            return stations, radius_km

    return [], radius_steps_km[-1]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Startup & Shutdown
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    # Startup
    print("\n" + "="*50)
    print("🚀 Starting Missing Person Tracker Backend")
    print("="*50)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")

    # Warm face models once to avoid first-request overhead and memory spikes.
    warmup_face_models()
    
    # Check if admin exists, create if not
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == "admin").first()
        if not admin:
            default_admin = User(
                name="Admin User",
                email="admin@example.com",
                hashed_password=hash_password("Admin@1234"),
                role="admin",
                is_active=True
            )
            db.add(default_admin)
            db.commit()
            
            print("\n┌─────────────────────────────────────┐")
            print("│  DEFAULT ADMIN CREATED              │")
            print("│  Email:    admin@example.com        │")
            print("│  Password: Admin@1234               │")
            print("│  Change password after first login  │")
            print("└─────────────────────────────────────┘\n")
        else:
            print(f"✓ Admin user exists: {admin.email}")
    finally:
        db.close()
    
    print("="*50 + "\n")
    
    yield
    
    # Shutdown
    print("\n" + "="*50)
    print("🛑 Shutting down")
    print("="*50 + "\n")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FastAPI App
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

app = FastAPI(
    title="Missing Person Tracker",
    description="Backend API for missing person tracking with face recognition",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Pydantic Schemas
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class RegisterRequest(BaseModel):
    """User registration request."""
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None


class LoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response (no password)."""
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Authentication response with token."""
    id: int
    name: str
    email: str
    role: str
    token: str


class MissingPersonResponse(BaseModel):
    """Missing person details."""
    id: int
    case_id: int
    full_name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    last_seen_date: Optional[str] = None
    last_seen_city: str
    last_seen_state: Optional[str] = None
    last_seen_address: Optional[str] = None
    description: Optional[str] = None
    photo_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class CaseResponse(BaseModel):
    """Case details."""
    id: int
    case_number: str
    status: str
    priority: str
    police_dispatch_mode: str
    missing_person: Optional[MissingPersonResponse] = None
    created_at: datetime
    updated_at: datetime
    family_member_count: int = 0
    volunteer_count: int = 0
    
    class Config:
        from_attributes = True


class MatchResponse(BaseModel):
    """Match result."""
    id: int
    case_id: int
    sighting_id: int
    confidence: float
    confidence_label: str
    match_type: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class SightingResponse(BaseModel):
    """Sighting details."""
    id: int
    reporter_name: Optional[str] = None
    sighting_lat: float
    sighting_lng: float
    city: Optional[str] = None
    state: Optional[str] = None
    address: Optional[str] = None
    photo_url: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class VolunteerProfileResponse(BaseModel):
    """Volunteer profile details."""
    id: int
    user_id: int
    status: str
    coverage_type: Optional[str] = None
    coverage_city: Optional[str] = None
    coverage_state: Optional[str] = None
    bio: Optional[str] = None
    
    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: List
    total: int
    page: int
    limit: int
    pages: int


class AlertCreateRequest(BaseModel):
    case_id: int
    confidence: float
    location: Optional[str] = None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Health Check
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "missing-person-tracker-backend",
        "timestamp": datetime.utcnow().isoformat()
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Auth Routes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.post("/auth/register", response_model=AuthResponse, tags=["Auth"])
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    new_user = User(
        name=request.name,
        email=request.email,
        phone=request.phone,
        hashed_password=hash_password(request.password),
        role="user",
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    token = create_token(new_user.id, new_user.role)
    
    return AuthResponse(
        id=new_user.id,
        name=new_user.name,
        email=new_user.email,
        role=new_user.role,
        token=token
    )


@app.post("/auth/login", response_model=AuthResponse, tags=["Auth"])
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with email and password."""
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    token = create_token(user.id, user.role)
    
    return AuthResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        token=token
    )


@app.get("/auth/me", response_model=UserResponse, tags=["Auth"])
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user's information."""
    return current_user


@app.post("/ai/validate-photo", tags=["AI"])
def validate_photo(
    image: UploadFile = File(...),
):
    """Validate whether uploaded photo appears to contain a person face."""
    try:
        image_bytes = prepare_image_bytes_for_processing(image.file)
        log_memory_snapshot("validate_photo:prepared")

        # Use face encoding detector when available.
        if is_face_engine_available():
            encoding = extract_encoding(image_bytes)
            if encoding:
                return {"is_person": True, "confidence": 0.92}
            return {"is_person": False, "confidence": 0.28}

        # Fallback mode: if detection model is unavailable, ensure image is decodable
        # and allow submission with medium confidence instead of blocking all uploads.
        try:
            from PIL import Image
            Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception:
            return {"is_person": False, "confidence": 0.0}

        return {"is_person": True, "confidence": 0.61}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")
    finally:
        try:
            del image_bytes
        except Exception:
            pass
        try:
            del encoding
        except Exception:
            pass
        gc.collect()
        log_memory_snapshot("validate_photo:done")


@app.get("/users/search", tags=["Users"])
def search_users(
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search users by email for family member selection."""
    query = db.query(User).filter(User.email.ilike(f"%{q.strip()}%"))

    # Exclude current user from family-member suggestions.
    users = query.filter(User.id != current_user.id).order_by(User.email.asc()).limit(5).all()

    return {
        "users": [
            {
                "id": user.id,
                "name": user.name,
                "email": user.email,
            }
            for user in users
        ]
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Cases Routes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.post("/cases", response_model=Dict, tags=["Cases"])
def create_case(
    full_name: str = Form(...),
    age: Optional[int] = Form(None),
    gender: Optional[str] = Form(None),
    last_seen_date: Optional[str] = Form(None),
    last_seen_city: str = Form(...),
    last_seen_state: Optional[str] = Form(None),
    last_seen_address: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    police_dispatch_mode: str = Form("manual"),
    photo: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new missing person case.
    
    - **photo**: Required image file
    - **full_name**: Missing person's full name
    - **last_seen_city**: City where person was last seen
    - All other fields are optional
    """
    
    try:
        if not is_face_engine_available():
            reason = face_engine_unavailable_reason() or "Face recognition model not available"
            raise HTTPException(status_code=503, detail=f"Face recognition model not available: {reason}")

        # Validate and preprocess to memory-efficient size before any heavy operation.
        photo_bytes = prepare_image_bytes_for_processing(photo.file)
        log_memory_snapshot("create_case:prepared")
        
        # Upload to Cloudinary
        try:
            photo_url = upload_photo(
                photo_bytes,
                folder="missing_persons",
                filename=f"mp-{uuid.uuid4()}"
            )
        except Exception as e:
            logger.warning(f"Cloudinary upload failed, storing without URL: {str(e)}")
            photo_url = None
        
        # Extract face encoding
        face_encoding = extract_encoding(photo_bytes)
        if not face_encoding:
            raise HTTPException(
                status_code=400,
                detail="No face detected in uploaded photo. Please upload a clear face image."
            )
        log_memory_snapshot("create_case:encoded")
        
        # Geocode address if provided
        lat, lng = None, None
        if last_seen_address:
            coords = geocode_address(last_seen_address, last_seen_city, last_seen_state or "")
            if coords:
                lat, lng = coords["lat"], coords["lng"]
        
        # Generate case number
        case_count = db.query(Case).count()
        year = datetime.utcnow().year
        case_number = f"MP-{year}-{case_count + 1:05d}"
        
        # Create Case
        case = Case(
            case_number=case_number,
            reported_by_id=current_user.id,
            status="open",
            priority="normal",
            police_dispatch_mode=police_dispatch_mode
        )
        db.add(case)
        db.flush()
        
        # Create MissingPerson
        missing_person = MissingPerson(
            case_id=case.id,
            full_name=full_name,
            age=age,
            gender=gender,
            last_seen_date=last_seen_date,
            last_seen_city=last_seen_city,
            last_seen_state=last_seen_state,
            last_seen_address=last_seen_address,
            last_seen_lat=lat,
            last_seen_lng=lng,
            description=description,
            photo_url=photo_url,
            face_encoding=face_encoding
        )
        db.add(missing_person)
        db.commit()
        db.refresh(case)
        
        return {
            "case_id": case.id,
            "case_number": case.case_number,
            "message": "Case created successfully",
            "face_detected": face_encoding is not None
        }
    
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Error creating case: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating case: {str(e)}")
    finally:
        try:
            del photo_bytes
        except Exception:
            pass
        try:
            del face_encoding
        except Exception:
            pass
        gc.collect()
        log_memory_snapshot("create_case:done")


@app.get("/cases", response_model=Dict, tags=["Cases"])
def list_cases(
    status: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List cases. User sees own cases only, admin sees all.
    
    Query params:
    - **status**: Filter by status (open, matched, closed, etc.)
    - **city**: Filter by city
    - **page**: Page number (default 1)
    - **limit**: Items per page (default 20)
    """
    
    query = db.query(Case)
    
    # Non-admin users only see their own cases
    if current_user.role != "admin":
        query = query.filter(Case.reported_by_id == current_user.id)
    
    # Apply filters
    if status:
        query = query.filter(Case.status == status)
    
    if city:
        query = query.join(MissingPerson)
        query = query.filter(MissingPerson.last_seen_city.ilike(f"%{city}%"))
    
    # Count total
    total = query.count()
    
    # Paginate
    skip = (page - 1) * limit
    cases = query.order_by(desc(Case.created_at)).offset(skip).limit(limit).all()
    
    cases_data = []
    for case in cases:
        case_dict = {
            "id": case.id,
            "case_number": case.case_number,
            "status": case.status,
            "priority": case.priority,
            "created_at": case.created_at,
            "family_member_count": len(case.family_members),
            "volunteer_count": len(case.volunteers),
            "created_by": {
                "name": case.reported_by.name if case.reported_by else "Unknown",
                "email": case.reported_by.email if case.reported_by else "-",
            },
        }
        if case.missing_person:
            case_dict["missing_person_name"] = case.missing_person.full_name
            case_dict["city"] = case.missing_person.last_seen_city
            case_dict["missing_person"] = {
                "name": case.missing_person.full_name,
                "age": case.missing_person.age,
                "gender": case.missing_person.gender,
                "city": case.missing_person.last_seen_city,
                "state": case.missing_person.last_seen_state,
                "photo_url": case.missing_person.photo_url,
            }
        cases_data.append(case_dict)
    
    return {
        "cases": cases_data,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@app.get("/cases/{case_id}", response_model=Dict, tags=["Cases"])
def get_case(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get case details."""
    
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Check authorization
    if current_user.role != "admin" and case.reported_by_id != current_user.id:
        # Check if user is family member
        is_family = db.query(CaseFamilyMember).filter(
            and_(CaseFamilyMember.case_id == case_id, CaseFamilyMember.user_id == current_user.id)
        ).first()
        
        if not is_family:
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Build response
    case_data = {
        "id": case.id,
        "case_number": case.case_number,
        "status": case.status,
        "priority": case.priority,
        "police_dispatch_mode": case.police_dispatch_mode,
        "created_at": case.created_at,
        "updated_at": case.updated_at,
        "family_member_count": len(case.family_members),
        "volunteer_count": len(case.volunteers),
    }
    
    if case.missing_person:
        mp = case.missing_person
        case_data["missing_person"] = {
            "id": mp.id,
            "name": mp.full_name,
            "age": mp.age,
            "gender": mp.gender,
            "city": mp.last_seen_city,
            "state": mp.last_seen_state,
            "address": mp.last_seen_address,
            "photo_url": mp.photo_url,
            "description": mp.description
        }
    
    # Include matches (confidence/city only for non-admin)
    matches = db.query(Match).filter(Match.case_id == case_id).all()
    case_data["matches"] = []
    for m in matches:
        match_data = {
            "id": m.id,
            "confidence": m.confidence,
            "label": m.confidence_label,
            "status": m.status,
            "created_at": m.created_at
        }
        if current_user.role == "admin":
            match_data["sighting_city"] = m.sighting.sighting_city if m.sighting else None
        case_data["matches"].append(match_data)
    
    return case_data


@app.patch("/cases/{case_id}/status", tags=["Cases"])
def update_case_status(
    case_id: int,
    body: Dict,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update case status (admin only)."""
    
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    new_status = body.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="status field required")
    
    case.status = new_status
    case.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Case status updated", "status": case.status}


@app.patch("/cases/{case_id}/dispatch-mode", tags=["Cases"])
def update_dispatch_mode(
    case_id: int,
    body: Dict,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update police dispatch mode (admin only)."""
    
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    mode = body.get("mode")
    if mode not in ["manual", "auto"]:
        raise HTTPException(status_code=400, detail="mode must be 'manual' or 'auto'")
    
    case.police_dispatch_mode = mode
    db.commit()
    
    return {"message": "Dispatch mode updated", "mode": case.police_dispatch_mode}


@app.post("/cases/{case_id}/family", tags=["Cases"])
def add_family_member(
    case_id: int,
    body: Dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add family member to case (reporter only)."""
    
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    if case.reported_by_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only case reporter can add family members")
    
    email = body.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="email field required")
    
    # Find user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found — they must register first")
    
    # Check if already added
    existing = db.query(CaseFamilyMember).filter(
        and_(CaseFamilyMember.case_id == case_id, CaseFamilyMember.user_id == user.id)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already a family member")
    
    # Add family member
    family_member = CaseFamilyMember(
        case_id=case_id,
        user_id=user.id,
        added_by_id=current_user.id
    )
    db.add(family_member)
    db.commit()
    
    return {
        "message": "Family member added",
        "user_name": user.name
    }


@app.delete("/cases/{case_id}/family/{user_id}", tags=["Cases"])
def remove_family_member(
    case_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove family member from case."""
    
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    if case.reported_by_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    family_member = db.query(CaseFamilyMember).filter(
        and_(CaseFamilyMember.case_id == case_id, CaseFamilyMember.user_id == user_id)
    ).first()
    
    if not family_member:
        raise HTTPException(status_code=404, detail="Family member not found")
    
    db.delete(family_member)
    db.commit()
    
    return {"message": "Family member removed"}


@app.get("/cases/{case_id}/realtime", tags=["Cases"])
def get_case_realtime(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get realtime case updates (status, matches, sightings, timeline)."""
    
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Check authorization
    is_reporter = case.reported_by_id == current_user.id
    is_family = db.query(CaseFamilyMember).filter(
        and_(CaseFamilyMember.case_id == case_id, CaseFamilyMember.user_id == current_user.id)
    ).first() is not None
    is_volunteer = db.query(CaseVolunteer).filter(
        and_(CaseVolunteer.case_id == case_id, CaseVolunteer.volunteer_user_id == current_user.id)
    ).first() is not None
    is_admin = current_user.role == "admin"
    
    if not (is_reporter or is_family or is_volunteer or is_admin):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Build timeline
    timeline = []
    
    # Case filed event
    timeline.append({
        "event": "Case filed",
        "time": case.created_at.isoformat(),
        "by": case.reported_by.name if case.reported_by else "Unknown"
    })
    
    # Get matches and sightings
    matches = db.query(Match).filter(Match.case_id == case_id).order_by(desc(Match.created_at)).all()
    sightings = []
    for match in matches:
        if match.sighting:
            sightings.append(match.sighting)
    
    # Add sighting events
    for sighting in sightings:
        timeline.append({
            "event": f"Sighting detected in {sighting.sighting_city or 'unknown location'}",
            "time": sighting.created_at.isoformat(),
            "lat": sighting.sighting_lat,
            "lng": sighting.sighting_lng
        })
    
    # Add match events
    for match in matches:
        if match.status in ["confirmed", "auto_confirmed"]:
            timeline.append({
                "event": f"Face match found ({match.confidence*100:.0f}% confidence)",
                "time": match.created_at.isoformat(),
                "confidence": match.confidence,
                "match_type": match.match_type
            })
    
    # Get latest match and sighting
    latest_match = matches[0] if matches else None
    latest_sighting = sightings[0] if sightings else None
    
    response = {
        "case_id": case.id,
        "case_number": case.case_number,
        "status": case.status,
        "priority": case.priority,
        "updated_at": case.updated_at.isoformat(),
        "latest_match": None if not latest_match else {
            "confidence": latest_match.confidence,
            "city": latest_match.sighting.sighting_city if latest_match.sighting else None,
            "date": latest_match.created_at.isoformat()
        },
        "last_sighting": None if not latest_sighting else {
            "lat": latest_sighting.sighting_lat,
            "lng": latest_sighting.sighting_lng,
            "city": latest_sighting.sighting_city,
            "date": latest_sighting.created_at.isoformat()
        },
        "timeline": timeline
    }
    
    return response


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Sightings Routes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.post("/sightings/upload", response_model=Dict, tags=["Sightings"])
@app.post("/sightings", response_model=Dict, tags=["Sightings"])
def create_sighting(
    request: Request,
    sighting_lat: float = Form(...),
    sighting_lng: float = Form(...),
    reporter_name: Optional[str] = Form(None),
    reporter_phone: Optional[str] = Form(None),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Report a sighting (public endpoint, no auth required).
    
    - **sighting_lat, sighting_lng**: Coordinates where person was seen
    - **photo**: Required image file
    - **reporter_name, reporter_phone**: Optional reporter contact info
    
    Returns: Match result first, then stores sighting based on policy
    """
    
    try:
        if not is_face_engine_available():
            reason = face_engine_unavailable_reason() or "Face recognition model not available"
            raise HTTPException(status_code=503, detail=f"Face recognition model not available: {reason}")

        photo_bytes = prepare_image_bytes_for_processing(photo.file)
        log_memory_snapshot("create_sighting:prepared")

        client_ip = request.client.host if request.client else "unknown"
        client_key = f"{client_ip}:{(reporter_phone or '').strip()}"
        _enforce_sighting_rate_limit(client_key, photo_bytes)

        # STEP 1+2: extract face and embedding with the same model used for cases.
        face_encoding = extract_encoding(photo_bytes)
        if not face_encoding:
            raise HTTPException(
                status_code=400,
                detail="No face detected"
            )
        log_memory_snapshot("create_sighting:encoded")

        # STEP 3+4+5: compare against all existing case embeddings via cosine similarity.
        matches = match_against_open_cases(face_encoding, db)
        best_match = matches[0] if matches else None
        match_found = bool(best_match and best_match["confidence"] > settings.FACE_REVIEW_THRESHOLD)

        # Get location only once needed for response/alert/storage.
        geo = reverse_geocode(sighting_lat, sighting_lng)
        city_name = geo["city"] if geo else None
        state_name = geo["state"] if geo else None
        address_name = geo["address"] if geo else None

        # STEP 6: trigger alert system before any optional persistence.
        if match_found and best_match:
            alert = Alert(
                case_id=best_match["case_id"],
                alert_type="match_found",
                recipient_type="admin",
                message=f"Potential face match {best_match['confidence']:.2f} in {city_name or 'Unknown city'}"
            )
            db.add(alert)

        # STEP 7: Save sighting only after matching, based on policy.
        should_store = (
            (match_found and settings.STORE_MATCHED_SIGHTINGS) or
            (not match_found and settings.STORE_UNMATCHED_SIGHTINGS)
        )

        sighting_id = None
        if should_store:
            try:
                photo_url = upload_photo(
                    photo_bytes,
                    folder="sightings",
                    filename=f"sighting-{uuid.uuid4()}"
                )
            except Exception as e:
                logger.warning(f"Cloudinary upload failed for sighting: {str(e)}")
                photo_url = None

            sighting = Sighting(
                reporter_name=reporter_name,
                reporter_phone=reporter_phone,
                sighting_lat=sighting_lat,
                sighting_lng=sighting_lng,
                sighting_city=city_name,
                sighting_state=state_name,
                sighting_address=address_name,
                photo_url=photo_url,
                face_encoding=face_encoding,
                status="matched" if match_found else "no_match"
            )
            db.add(sighting)
            db.flush()
            sighting_id = sighting.id

            if match_found and best_match:
                db.add(Match(
                        case_id=best_match["case_id"],
                        sighting_id=sighting.id,
                        confidence=best_match["confidence"],
                        confidence_label=best_match["label"],
                        match_type="review" if best_match["confidence"] <= settings.FACE_AUTO_THRESHOLD else "auto",
                        status="pending" if best_match["confidence"] <= settings.FACE_AUTO_THRESHOLD else "auto_confirmed",
                    ))

        message = (
            "Thank you. Sighting analyzed, no match found."
            if not match_found
            else "Potential match found. Authorities notified."
        )

        db.commit()
        log_memory_snapshot("create_sighting:committed")

        return {
            "sighting_id": sighting_id,
            "stored": should_store,
            "match_found": match_found,
            "case_id": best_match["case_id"] if match_found and best_match else None,
            "confidence": best_match["confidence"] if match_found and best_match else None,
            "level": best_match["label"] if match_found and best_match else None,
            "message": message
        }
    
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        logger.error(f"Error creating sighting: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating sighting: {str(e)}")
    finally:
        try:
            del photo_bytes
        except Exception:
            pass
        try:
            del face_encoding
        except Exception:
            pass
        try:
            del matches
        except Exception:
            pass
        gc.collect()
        log_memory_snapshot("create_sighting:done")


@app.get("/sightings", tags=["Sightings"])
def list_sightings(
    status: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List sightings (admin only)."""
    
    query = db.query(Sighting)
    
    if status:
        query = query.filter(Sighting.status == status)
    
    if city:
        query = query.filter(Sighting.sighting_city.ilike(f"%{city}%"))
    
    total = query.count()
    skip = (page - 1) * limit
    sightings = query.order_by(desc(Sighting.created_at)).offset(skip).limit(limit).all()
    
    return {
        "sightings": [
            {
                "id": s.id,
                "city": s.sighting_city,
                "status": s.status,
                "created_at": s.created_at,
                "lat": s.sighting_lat,
                "lng": s.sighting_lng
            }
            for s in sightings
        ],
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }


@app.get("/sightings/{sighting_id}", tags=["Sightings"])
def get_sighting(
    sighting_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sighting details (admin only)."""
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    sighting = db.query(Sighting).filter(Sighting.id == sighting_id).first()
    if not sighting:
        raise HTTPException(status_code=404, detail="Sighting not found")
    
    return {
        "id": sighting.id,
        "reporter_name": sighting.reporter_name,
        "reporter_phone": sighting.reporter_phone,
        "lat": sighting.sighting_lat,
        "lng": sighting.sighting_lng,
        "city": sighting.sighting_city,
        "state": sighting.sighting_state,
        "address": sighting.sighting_address,
        "photo_url": sighting.photo_url,
        "status": sighting.status,
        "created_at": sighting.created_at
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Matches Routes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/matches", tags=["Matches"])
def list_matches(
    status: Optional[str] = Query(None),
    match_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List matches (admin only), ordered by confidence descending."""
    
    query = db.query(Match)
    
    if status:
        query = query.filter(Match.status == status)
    
    if match_type:
        query = query.filter(Match.match_type == match_type)
    
    total = query.count()
    skip = (page - 1) * limit
    matches = query.order_by(desc(Match.confidence)).offset(skip).limit(limit).all()
    
    matches_data = []
    for m in matches:
        case = db.query(Case).filter(Case.id == m.case_id).first()
        mp = case.missing_person if case and case.missing_person else None
        matches_data.append({
            "id": m.id,
            "case_id": m.case_id,
            "sighting_id": m.sighting_id,
            "confidence": m.confidence,
            "label": m.confidence_label,
            "match_type": m.match_type,
            "status": m.status,
            "missing_person_name": mp.full_name if mp else None,
            "sighting_city": m.sighting.sighting_city if m.sighting else None,
            "created_at": m.created_at
        })
    
    return {
        "matches": matches_data,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }


@app.get("/matches/pending-count", tags=["Matches"])
def get_pending_count(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get count of matches pending review (admin only)."""
    
    review_needed = db.query(Match).filter(Match.status == "pending").count()
    auto_pending = db.query(Match).filter(Match.status == "auto_confirmed").count()
    
    return {
        "review_needed": review_needed,
        "auto_pending_signoff": auto_pending
    }


@app.get("/matches/{match_id}", tags=["Matches"])
def get_match(
    match_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get match details (admin only)."""
    
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    case = db.query(Case).filter(Case.id == match.case_id).first()
    mp = case.missing_person if case else None
    sighting = db.query(Sighting).filter(Sighting.id == match.sighting_id).first()
    
    return {
        "id": match.id,
        "case_id": match.case_id,
        "case_number": case.case_number if case else None,
        "sighting_id": match.sighting_id,
        "confidence": match.confidence,
        "confidence_label": match.confidence_label,
        "match_type": match.match_type,
        "status": match.status,
        "missing_person": {
            "name": mp.full_name,
            "age": mp.age,
            "photo_url": mp.photo_url
        } if mp else None,
        "sighting": {
            "lat": sighting.sighting_lat,
            "lng": sighting.sighting_lng,
            "city": sighting.sighting_city,
            "photo_url": sighting.photo_url,
            "created_at": sighting.created_at
        } if sighting else None,
        "created_at": match.created_at
    }


@app.patch("/matches/{match_id}/review", tags=["Matches"])
def review_match(
    match_id: int,
    body: Dict,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Confirm or reject a match (admin only)."""
    
    match = db.query(Match).filter(Match.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    action = body.get("action")
    if action not in ["confirm", "reject"]:
        raise HTTPException(status_code=400, detail="action must be 'confirm' or 'reject'")
    
    notes = body.get("notes", "")
    
    if action == "confirm":
        match.status = "confirmed"
        match.reviewed_by_id = current_user.id
        match.reviewed_at = datetime.utcnow()
        
        # Update case status
        case = db.query(Case).filter(Case.id == match.case_id).first()
        if case:
            case.status = "matched"
            case.priority = "critical"
        
        # Create alert
        mp = case.missing_person if case else None
        alert = Alert(
            case_id=match.case_id,
            match_id=match.id,
            alert_type="match_confirmed",
            recipient_type="all",
            message=f"Match confirmed: {mp.full_name if mp else 'Missing person'} — Sighting in {match.sighting.sighting_city if match.sighting else 'unknown area'}"
        )
        db.add(alert)
        
        # Handle auto-dispatch if enabled
        if case and case.police_dispatch_mode == "auto":
            # TODO: Implement police dispatch logic
            pass
    
    else:  # reject
        match.status = "rejected"
        match.reviewed_by_id = current_user.id
        match.reviewed_at = datetime.utcnow()
        
        # If no other confirmed matches, reset case status
        other_confirmed = db.query(Match).filter(
            and_(Match.case_id == match.case_id, Match.status == "confirmed", Match.id != match.id)
        ).first()
        if not other_confirmed:
            case = db.query(Case).filter(Case.id == match.case_id).first()
            if case:
                case.status = "open"
    
    db.commit()
    
    return {
        "message": f"Match {action}ed",
        "match_id": match.id,
        "status": match.status
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Volunteers Routes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.post("/volunteers/apply", tags=["Volunteers"])
def apply_volunteer(
    body: Dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Apply to become a volunteer."""
    
    existing = db.query(VolunteerProfile).filter(VolunteerProfile.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already applied — application pending review")
    
    coverage_type = body.get("coverage_type")
    coverage_city = body.get("coverage_city")
    coverage_state = body.get("coverage_state")
    bio = body.get("bio")
    
    profile = VolunteerProfile(
        user_id=current_user.id,
        status="pending",
        coverage_type=coverage_type,
        coverage_city=coverage_city,
        coverage_state=coverage_state,
        bio=bio
    )
    db.add(profile)
    
    # Log alert for admins
    alert = Alert(
        alert_type="volunteer_applied",
        recipient_type="admin",
        message=f"New volunteer application from {current_user.name}"
    )
    db.add(alert)
    db.commit()
    
    return {"message": "Application submitted"}


@app.get("/volunteers", tags=["Volunteers"])
def list_volunteers(
    status: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List volunteer profiles (admin only)."""
    
    try:
        query = db.query(VolunteerProfile)
        
        if status:
            query = query.filter(VolunteerProfile.status == status)
        
        profiles = query.all()
        
        volunteers = []
        for v in profiles:
            user = db.query(User).filter(User.id == v.user_id).first()
            if user:
                volunteers.append({
                    "id": v.id,
                    "user_id": v.user_id,
                    "name": user.name,
                    "email": user.email,
                    "status": v.status,
                    "coverage_type": v.coverage_type,
                    "coverage_city": v.coverage_city,
                    "coverage_state": v.coverage_state,
                    "bio": v.bio,
                    "created_at": v.created_at
                })
        
        return {
            "volunteers": volunteers
        }
    except Exception as e:
        logger.error(f"Error listing volunteers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing volunteers: {str(e)}")


@app.patch("/volunteers/{volunteer_id}/approve", tags=["Volunteers"])
def approve_volunteer(
    volunteer_id: int,
    body: Dict,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Approve or reject volunteer application (admin only)."""
    
    volunteer = db.query(VolunteerProfile).filter(VolunteerProfile.id == volunteer_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")
    
    action = body.get("action")
    if action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="action must be 'approve' or 'reject'")
    
    if action == "approve":
        volunteer.status = "approved"
        volunteer.approved_by_id = current_user.id
        volunteer.approved_at = datetime.utcnow()
        
        # Create alert for volunteer
        alert = Alert(
            alert_type="volunteer_approved",
            recipient_type="specific",
            message=f"Your volunteer application has been approved!"
        )
    else:
        volunteer.status = "rejected"
        alert = Alert(
            alert_type="volunteer_rejected",
            recipient_type="specific",
            message=f"Your volunteer application was not approved at this time."
        )
    
    db.add(alert)
    db.commit()
    
    return {
        "message": f"Volunteer {action}ed",
        "volunteer_id": volunteer.id,
        "status": volunteer.status
    }


@app.get("/volunteers/my-cases", tags=["Volunteers"])
def get_volunteer_cases(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get cases assigned to current volunteer."""
    
    profile = db.query(VolunteerProfile).filter(VolunteerProfile.user_id == current_user.id).first()
    if not profile or profile.status != "approved":
        raise HTTPException(status_code=403, detail="Must be approved volunteer")
    
    # Get assigned cases
    assigned = db.query(Case).join(CaseVolunteer).filter(
        CaseVolunteer.volunteer_user_id == current_user.id
    ).all()
    
    # Get area-matching cases
    area_cases = db.query(Case).join(MissingPerson).filter(
        Case.status == "open"
    )
    
    if profile.coverage_type == "city" and profile.coverage_city:
        area_cases = area_cases.filter(MissingPerson.last_seen_city == profile.coverage_city)
    elif profile.coverage_type == "state" and profile.coverage_state:
        area_cases = area_cases.filter(MissingPerson.last_seen_state == profile.coverage_state)
    
    area_cases = area_cases.all()
    
    return {
        "assigned": [{
            "id": c.id,
            "case_number": c.case_number,
            "status": c.status,
            "missing_person": c.missing_person.full_name if c.missing_person else None
        } for c in assigned],
        "area_cases": [{
            "id": c.id,
            "case_number": c.case_number,
            "status": c.status,
            "missing_person": c.missing_person.full_name if c.missing_person else None,
            "city": c.missing_person.last_seen_city if c.missing_person else None
        } for c in area_cases]
    }


@app.post("/cases/{case_id}/volunteers/{user_id}", tags=["Cases"])
def assign_volunteer(
    case_id: int,
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Assign volunteer to case (admin only)."""
    
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    volunteer = db.query(VolunteerProfile).filter(VolunteerProfile.user_id == user_id).first()
    if not volunteer or volunteer.status != "approved":
        raise HTTPException(status_code=404, detail="Volunteer not found or not approved")
    
    # Check if already assigned
    existing = db.query(CaseVolunteer).filter(
        and_(CaseVolunteer.case_id == case_id, CaseVolunteer.volunteer_user_id == user_id)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Volunteer already assigned")
    
    assignment = CaseVolunteer(
        case_id=case_id,
        volunteer_user_id=user_id,
        assigned_by_id=current_user.id
    )
    db.add(assignment)
    
    # Create alert for volunteer
    user = db.query(User).filter(User.id == user_id).first()
    alert = Alert(
        case_id=case_id,
        alert_type="volunteer_assigned",
        recipient_type="specific",
        message=f"You've been assigned to case {case.case_number}"
    )
    db.add(alert)
    db.commit()
    
    return {"message": "Volunteer assigned", "case_id": case_id, "volunteer_id": user_id}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Admin Routes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/admin/stats", tags=["Admin"])
def get_admin_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get admin analytics stats for dashboard cards and charts (admin only)."""

    total_cases = db.query(Case).count()
    open_cases = db.query(Case).filter(Case.status == "open").count()
    matches_found = db.query(Match).filter(Match.status.in_(["confirmed", "auto_confirmed"])).count()
    volunteers_count = db.query(VolunteerProfile).filter(VolunteerProfile.status == "approved").count()
    firs_generated = db.query(FIR).count()

    case_rows = db.query(Case.created_at).all()
    match_rows = db.query(Match.created_at).all()

    cases_map = {}
    for (created_at,) in case_rows:
        key = created_at.strftime("%Y-%m-%d")
        cases_map[key] = cases_map.get(key, 0) + 1

    matches_map = {}
    for (created_at,) in match_rows:
        key = created_at.strftime("%Y-%m-%d")
        matches_map[key] = matches_map.get(key, 0) + 1

    status_rows = db.query(Case.status, func.count(Case.id)).group_by(Case.status).all()
    recent_alerts = db.query(Alert).order_by(desc(Alert.sent_at)).limit(15).all()

    return {
        "total_cases": total_cases,
        "open_cases": open_cases,
        "matches_found": matches_found,
        "volunteers": volunteers_count,
        "firs_generated": firs_generated,
        "cases_over_time": [
            {"date": k, "count": v}
            for k, v in sorted(cases_map.items())
        ],
        "matches_over_time": [
            {"date": k, "count": v}
            for k, v in sorted(matches_map.items())
        ],
        "status_distribution": [
            {"status": status, "count": count}
            for status, count in status_rows
        ],
        "recent_activity": [
            {
                "type": a.alert_type,
                "message": a.message,
                "time": a.sent_at.isoformat(),
            }
            for a in recent_alerts
        ],
    }


@app.get("/admin/cases", tags=["Admin"])
def admin_list_cases(
    status: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all cases for admin panel with creator + person details."""
    query = db.query(Case)

    if status:
        query = query.filter(Case.status == status)

    if city:
        query = query.join(MissingPerson).filter(MissingPerson.last_seen_city.ilike(f"%{city}%"))

    rows = query.order_by(desc(Case.created_at)).all()

    return {
        "cases": [
            {
                "id": c.id,
                "case_number": c.case_number,
                "status": c.status,
                "priority": c.priority,
                "created_at": c.created_at,
                "missing_person_name": c.missing_person.full_name if c.missing_person else None,
                "city": c.missing_person.last_seen_city if c.missing_person else None,
                "created_by": {
                    "name": c.reported_by.name if c.reported_by else "Unknown",
                    "email": c.reported_by.email if c.reported_by else "-",
                },
            }
            for c in rows
        ]
    }


@app.get("/admin/matches", tags=["Admin"])
def admin_list_matches(
    status: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all matches with joined case and sighting context."""
    query = db.query(Match)
    if status:
        query = query.filter(Match.status == status)

    rows = query.order_by(desc(Match.created_at)).all()
    return {
        "matches": [
            {
                "id": m.id,
                "case_id": m.case_id,
                "person_name": m.case.missing_person.full_name if m.case and m.case.missing_person else None,
                "confidence": m.confidence,
                "sighting_city": m.sighting.sighting_city if m.sighting else None,
                "status": m.status,
                "created_at": m.created_at,
            }
            for m in rows
        ]
    }


@app.get("/admin/sightings", tags=["Admin"])
def admin_list_sightings(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List sightings for admin panel."""
    rows = db.query(Sighting).order_by(desc(Sighting.created_at)).all()
    return {
        "sightings": [
            {
                "id": s.id,
                "city": s.sighting_city,
                "created_at": s.created_at,
                "matches_found": len(s.matches),
                "submitted_by": s.reporter_name,
            }
            for s in rows
        ]
    }


@app.get("/admin/volunteers", tags=["Admin"])
def admin_list_volunteers(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List volunteers for admin panel, grouped into pending and approved."""
    profiles = db.query(VolunteerProfile).order_by(desc(VolunteerProfile.created_at)).all()
    volunteers = []

    for v in profiles:
        user = db.query(User).filter(User.id == v.user_id).first()
        if not user:
            continue
        volunteers.append({
            "id": v.id,
            "user_id": v.user_id,
            "name": user.name,
            "email": user.email,
            "coverage": " ".join([x for x in [v.coverage_type, v.coverage_city, v.coverage_state] if x]) or "-",
            "bio": v.bio,
            "status": v.status,
            "created_at": v.created_at,
        })

    return {
        "pending": [v for v in volunteers if v["status"] == "pending"],
        "approved": [v for v in volunteers if v["status"] == "approved"],
        "volunteers": volunteers,
    }


@app.get("/admin/fir", tags=["Admin"])
def admin_list_fir(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List FIR records for admin panel."""
    rows = db.query(FIR).order_by(desc(FIR.created_at)).all()
    return {
        "firs": [
            {
                "id": f.id,
                "fir_number": f.fir_number,
                "case_id": f.case_id,
                "case_number": f.case.case_number if f.case else None,
                "status": f.status,
                "created_at": f.created_at,
                "pdf_url": f.pdf_url,
            }
            for f in rows
        ]
    }


@app.patch("/admin/cases/{case_id}/close", tags=["Admin"])
def close_case_admin(
    case_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Close a case (admin only)."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case.status = "closed"
    case.updated_at = datetime.utcnow()
    db.add(Alert(
        case_id=case.id,
        alert_type="case_closed",
        recipient_type="all",
        message=f"Case {case.case_number} was closed by admin"
    ))
    db.commit()

    return {"message": "Case closed", "case_id": case.id, "status": case.status}


@app.delete("/admin/cases/{case_id}", tags=["Admin"])
def delete_case_admin(
    case_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a case permanently (admin only)."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case_number = case.case_number
    db.delete(case)
    db.commit()

    return {"message": "Case deleted", "case_number": case_number}


@app.get("/admin/alerts", tags=["Admin"])
def list_admin_alerts(
    limit: int = Query(30, ge=1, le=200),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List latest alerts for admin dashboard."""
    alerts = db.query(Alert).order_by(desc(Alert.sent_at)).limit(limit).all()
    return {
        "alerts": [
            {
                "id": a.id,
                "type": a.alert_type,
                "message": a.message,
                "case_id": a.case_id,
                "match_id": a.match_id,
                "sent_at": a.sent_at,
            }
            for a in alerts
        ]
    }


@app.get("/admin/firs", tags=["Admin"])
def list_firs_admin(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List FIR records for admin."""
    firs = db.query(FIR).order_by(desc(FIR.created_at)).all()
    return {
        "firs": [
            {
                "id": f.id,
                "case_id": f.case_id,
                "case_number": f.case.case_number if f.case else None,
                "status": f.status,
                "pdf_url": f.pdf_url,
                "created_at": f.created_at,
                "signed_at": f.signed_at,
            }
            for f in firs
        ]
    }


@app.patch("/admin/firs/{fir_id}", tags=["Admin"])
def update_fir_admin(
    fir_id: int,
    body: Dict,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update FIR editable fields (admin only)."""
    fir = db.query(FIR).filter(FIR.id == fir_id).first()
    if not fir:
        raise HTTPException(status_code=404, detail="FIR not found")

    next_status = body.get("status")
    pdf_url = body.get("pdf_url")

    if next_status:
        fir.status = next_status
    if pdf_url is not None:
        fir.pdf_url = pdf_url

    db.commit()
    return {"message": "FIR updated", "id": fir.id, "status": fir.status}


@app.post("/admin/volunteers/{user_id}/assign/{case_id}", tags=["Admin"])
def assign_volunteer_admin(
    user_id: int,
    case_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Assign approved volunteer to a case (admin only)."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    volunteer = db.query(VolunteerProfile).filter(VolunteerProfile.user_id == user_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer profile not found")
    if volunteer.status != "approved":
        raise HTTPException(status_code=400, detail="Volunteer must be approved")

    existing = db.query(CaseVolunteer).filter(
        and_(CaseVolunteer.case_id == case_id, CaseVolunteer.volunteer_user_id == user_id)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Volunteer already assigned")

    db.add(CaseVolunteer(
        case_id=case_id,
        volunteer_user_id=user_id,
        assigned_by_id=current_user.id,
    ))
    db.commit()
    return {"message": "Volunteer assigned", "user_id": user_id, "case_id": case_id}


@app.delete("/admin/volunteers/{user_id}/assign/{case_id}", tags=["Admin"])
def remove_volunteer_assignment_admin(
    user_id: int,
    case_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Remove volunteer from case assignment (admin only)."""
    assignment = db.query(CaseVolunteer).filter(
        and_(CaseVolunteer.case_id == case_id, CaseVolunteer.volunteer_user_id == user_id)
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    db.delete(assignment)
    db.commit()
    return {"message": "Volunteer removed from case", "user_id": user_id, "case_id": case_id}


@app.patch("/admin/volunteers/{volunteer_id}/ban", tags=["Admin"])
def ban_volunteer_admin(
    volunteer_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Ban volunteer profile (admin only)."""
    volunteer = db.query(VolunteerProfile).filter(VolunteerProfile.id == volunteer_id).first()
    if not volunteer:
        raise HTTPException(status_code=404, detail="Volunteer not found")

    volunteer.status = "banned"
    db.commit()
    return {"message": "Volunteer banned", "id": volunteer.id, "status": volunteer.status}


@app.get("/notifications", tags=["Notifications"])
def get_notifications(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get notifications for current user."""
    
    if current_user.role == "admin":
        # Admin sees all alerts from last 7 days
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        alerts = db.query(Alert).filter(Alert.sent_at >= cutoff_date).order_by(
            desc(Alert.sent_at)
        ).limit(limit).all()
    else:
        # Users see alerts for their cases + family cases + volunteer cases
        my_cases = db.query(Case).filter(Case.reported_by_id == current_user.id).all()
        family_cases = db.query(Case).join(CaseFamilyMember).filter(
            CaseFamilyMember.user_id == current_user.id
        ).all()
        volunteer_cases = db.query(Case).join(CaseVolunteer).filter(
            CaseVolunteer.volunteer_user_id == current_user.id
        ).all()
        
        case_ids = set(c.id for c in my_cases + family_cases + volunteer_cases)
        
        alerts = db.query(Alert).filter(Alert.case_id.in_(case_ids)).order_by(
            desc(Alert.sent_at)
        ).limit(limit).all()
    
    return {
        "notifications": [
            {
                "id": a.id,
                "type": a.alert_type,
                "message": a.message,
                "case_id": a.case_id,
                "sent_at": a.sent_at.isoformat()
            }
            for a in alerts
        ]
    }


@app.get("/notifications/count", tags=["Notifications"])
def get_notification_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get unread notification count."""
    
    if current_user.role == "admin":
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        count = db.query(Alert).filter(Alert.sent_at >= cutoff_date).count()
    else:
        my_cases = db.query(Case).filter(Case.reported_by_id == current_user.id).all()
        case_ids = set(c.id for c in my_cases)
        count = db.query(Alert).filter(Alert.case_id.in_(case_ids)).count()
    
    return {"count": count}


@app.post("/alerts", tags=["Alerts"])
def create_alert(
    payload: AlertCreateRequest,
    current_user: User = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """Create alert entry for admin notifications."""
    message = f"Potential face match {payload.confidence:.2f} at {payload.location or 'unknown location'}"
    alert = Alert(
        case_id=payload.case_id,
        alert_type="match_found",
        recipient_type="admin",
        message=message,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    return {
        "id": alert.id,
        "case_id": alert.case_id,
        "message": alert.message,
        "sent_at": alert.sent_at,
        "created_by": current_user.email if current_user else "system",
    }


@app.post("/admin/reindex-case-embeddings", tags=["Admin"])
def reindex_case_embeddings(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Backfill missing case face embeddings from stored photo URLs."""
    import requests

    rows = db.query(MissingPerson).filter(
        MissingPerson.face_encoding.is_(None),
        MissingPerson.photo_url.isnot(None),
    ).all()

    updated = 0
    failed = 0

    for mp in rows:
        try:
            response = requests.get(mp.photo_url, timeout=25)
            response.raise_for_status()
            encoding = extract_encoding(response.content)
            if encoding:
                mp.face_encoding = encoding
                updated += 1
            else:
                failed += 1
        except Exception:
            failed += 1

    db.commit()
    return {
        "processed": len(rows),
        "updated": updated,
        "failed": failed,
    }


@app.post("/test-match", tags=["Testing"])
def test_match(
    image_a: UploadFile = File(...),
    image_b: UploadFile = File(...),
):
    """Test endpoint: compare two uploaded images using the same face pipeline."""
    if not is_face_engine_available():
        reason = face_engine_unavailable_reason() or "Face recognition model not available"
        raise HTTPException(status_code=503, detail=f"Face recognition model not available: {reason}")

    bytes_a = image_a.file.read()
    bytes_b = image_b.file.read()

    enc_a = extract_encoding(bytes_a)
    enc_b = extract_encoding(bytes_b)

    if not enc_a or not enc_b:
        raise HTTPException(status_code=400, detail="No face detected")

    similarity = compare_encodings(enc_a, enc_b)
    return {
        "similarity": similarity,
        "passes_same_image_expectation": similarity > 0.9,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Test Admin Route
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/admin/test", tags=["Admin"])
def admin_test(current_user: User = Depends(require_admin)):
    """Test admin access."""
    return {
        "message": "Welcome Admin!",
        "user": current_user.name,
        "email": current_user.email
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 3: POLICE STATIONS, FIR GENERATION, ALERTS, DISPATCH
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ───────────────────────────────────────────────────────
# Police Stations Routes
# ───────────────────────────────────────────────────────

@app.get("/police-stations", tags=["Police Stations"])
def get_police_stations(
    latitude: float,
    longitude: float,
    radius_km: float = 5.0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get nearby police stations from OpenStreetMap.
    
    Args:
        latitude: Latitude of search center
        longitude: Longitude of search center
        radius_km: Search radius in kilometers (default: 5 km)
        limit: Maximum number of results (default: 10)
    
    Returns:
        List of police stations with names, addresses, and OSM URLs
    """
    try:
        radius_meters = max(500, int(radius_km * 1000))
        stations = find_police_stations(latitude, longitude, radius_meters=radius_meters)[:limit]
        return {
            "status": "success",
            "count": len(stations),
            "search_center": {"lat": latitude, "lng": longitude},
            "radius_km": radius_km,
            "stations": stations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cases/{case_id}/police-stations", tags=["Police Stations"])
def get_case_police_stations(
    case_id: int,
    radius_km: float = 5.0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get police stations near a case's last seen location.
    
    Returns stations ordered by distance with OpenStreetMap links.
    """
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    resolved_location = _resolve_case_location(db, case)
    search_lat = resolved_location["lat"]
    search_lng = resolved_location["lng"]
    city_name = resolved_location["city"] or "Unknown"
    state_name = resolved_location["state"]
    location_source = resolved_location["source"]

    if search_lat is None or search_lng is None:
        return {
            "status": "success",
            "case_id": case_id,
            "missing_person": case.missing_person.full_name if case.missing_person else None,
            "location": None,
            "location_source": location_source,
            "count": 0,
            "radius_km": radius_km,
            "stations": [],
            "message": "No usable coordinates found for this case yet",
        }
    
    try:
        stations, used_radius_km = _find_stations_with_expanding_radius(
            search_lat,
            search_lng,
            limit=limit,
            base_radius_km=radius_km,
        )

        return {
            "status": "success",
            "case_id": case_id,
            "missing_person": case.missing_person.full_name if case.missing_person else None,
            "location": {
                "city": city_name,
                "state": state_name,
                "lat": search_lat,
                "lng": search_lng
            },
            "location_source": location_source,
            "count": len(stations),
            "radius_km": used_radius_km,
            "stations": stations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ───────────────────────────────────────────────────────
# FIR Generation & Management Routes
# ───────────────────────────────────────────────────────

@app.post("/fir/generate/{case_id}", tags=["FIR"])
def generate_fir(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate FIR PDF for a case.
    
    Creates a draft FIR in Indian police format with case details.
    Returns FIR ID for further operations.
    """
    # Verify case exists and user has access
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Verify user is admin or case creator
    if current_user.role != "admin" and case.reported_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to generate FIR for this case")
    
    try:
        fir_number = _next_fir_number(db)
        pdf_url = None

        nearest_station = None
        if case.missing_person and case.missing_person.last_seen_lat is not None and case.missing_person.last_seen_lng is not None:
            stations = find_police_stations(
                case.missing_person.last_seen_lat,
                case.missing_person.last_seen_lng,
                radius_meters=5000,
            )
            nearest_station = stations[0] if stations else None

        try:
            fir_pdf = generate_fir_pdf({
                "case": case,
                "missing_person": case.missing_person,
                "reporter": case.reported_by,
                "fir_number": fir_number,
                "station": nearest_station,
            })
            pdf_url = upload_photo(fir_pdf, folder="firs", filename=fir_number)
        except Exception as e:
            logger.warning(f"FIR PDF generation/upload failed, creating FIR without PDF: {str(e)}")

        fir_record = FIR(
            case_id=case_id,
            fir_number=fir_number,
            pdf_url=pdf_url,
            status="draft",
        )
        db.add(fir_record)
        db.commit()
        db.refresh(fir_record)

        return {
            "status": "success",
            "message": "FIR generated successfully",
            "fir_id": fir_record.id,
            "fir_number": fir_record.fir_number,
            "fir_status": fir_record.status,
            "case_id": case_id,
            "pdf_url": pdf_url,
            "generated_at": fir_record.created_at.isoformat(),
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FIR generation failed: {str(e)}")


@app.get("/fir/{fir_id}", tags=["FIR"])
def get_fir_details(
    fir_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get FIR details and current status."""
    fir = db.query(FIR).filter(FIR.id == fir_id).first()
    if not fir:
        raise HTTPException(status_code=404, detail="FIR not found")

    case = fir.case
    if not case:
        raise HTTPException(status_code=404, detail="Related case not found")

    if current_user.role != "admin" and case.reported_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    mp = case.missing_person

    nearest_stations = []
    resolved_location = _resolve_case_location(db, case)
    search_lat = resolved_location["lat"]
    search_lng = resolved_location["lng"]
    location_source = resolved_location["source"]

    used_radius_km = 7.0
    if search_lat is not None and search_lng is not None:
        nearest_stations, used_radius_km = _find_stations_with_expanding_radius(
            search_lat,
            search_lng,
            limit=5,
            base_radius_km=7.0,
        )

    case = fir.case
    signed_user = db.query(User).filter(User.id == fir.signed_by_id).first() if fir.signed_by_id else None
    return {
        "status": "success",
        "fir_id": fir.id,
        "fir_number": fir.fir_number,
        "case_id": fir.case_id,
        "case_number": case.case_number,
        "fir_status": fir.status,
        "generated_at": fir.created_at.isoformat(),
        "generated_by": case.reported_by.email if case.reported_by else None,
        "signed_by": signed_user.email if signed_user else None,
        "signed_at": fir.signed_at.isoformat() if fir.signed_at else None,
        "pdf_url": fir.pdf_url,
        "download_url": f"/fir/{fir.id}/download",
        "dispatch_count": len(fir.dispatches) if fir.dispatches else 0,
        "dispatches": [
            {
                "dispatch_id": d.id,
                "station_name": d.station.name if d.station else "Unknown",
                "dispatch_status": d.status,
                "dispatched_at": d.sent_at.isoformat() if d.sent_at else None,
            }
            for d in fir.dispatches
        ] if fir.dispatches else [],
        "case_details": {
            "status": case.status,
            "priority": case.priority,
        },
        "missing_person": {
            "name": mp.full_name if mp else None,
            "age": mp.age if mp else None,
            "city": mp.last_seen_city if mp else None,
            "state": mp.last_seen_state if mp else None,
        },
        "location": {
            "lat": search_lat,
            "lng": search_lng,
            "city": resolved_location.get("city"),
            "state": resolved_location.get("state"),
            "source": location_source,
        },
        "station_search_radius_km": used_radius_km,
        "station_search_location_source": location_source,
        "nearest_stations": nearest_stations,
    }


@app.get("/fir/{fir_id}/download", tags=["FIR"])
def download_fir(
    fir_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download FIR as generated PDF bytes with current FIR/case details."""
    fir = db.query(FIR).filter(FIR.id == fir_id).first()
    if not fir:
        raise HTTPException(status_code=404, detail="FIR not found")

    case = fir.case
    if not case:
        raise HTTPException(status_code=404, detail="Related case not found")

    if current_user.role != "admin" and case.reported_by_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    match = db.query(Match).filter(Match.case_id == case.id).order_by(desc(Match.created_at)).first()
    sighting = match.sighting if match else None

    station_data = None
    if case.missing_person and case.missing_person.last_seen_lat is not None and case.missing_person.last_seen_lng is not None:
        stations = find_police_stations(case.missing_person.last_seen_lat, case.missing_person.last_seen_lng, radius_meters=5000)
        station_data = stations[0] if stations else None

    signed_user = db.query(User).filter(User.id == fir.signed_by_id).first() if fir.signed_by_id else None

    pdf_bytes = generate_fir_pdf({
        "case": case,
        "missing_person": case.missing_person,
        "match": match,
        "sighting": sighting,
        "reporter": case.reported_by,
        "station": station_data,
        "signed_by": signed_user,
        "signed_at": fir.signed_at,
        "fir_number": fir.fir_number,
    })

    filename = f"{fir.fir_number}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/fir/{fir_id}/sign", tags=["FIR"])
def sign_fir(
    fir_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Sign FIR (admin only).
    
    Changes status from draft to signed.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can sign FIRs")
    
    fir = db.query(FIR).filter(FIR.id == fir_id).first()
    if not fir:
        raise HTTPException(status_code=404, detail="FIR not found")
    
    if fir.status != "draft":
        raise HTTPException(status_code=400, detail=f"FIR status is {fir.status}, cannot sign")
    
    try:
        fir.status = "signed"
        fir.signed_by_id = current_user.id
        fir.signed_at = datetime.utcnow()
        db.commit()

        return {
            "status": "success",
            "message": "FIR signed successfully",
            "fir_id": fir_id,
            "fir_status": "signed",
            "signed_by": current_user.email,
            "signed_at": fir.signed_at.isoformat()
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ───────────────────────────────────────────────────────
# FIR Dispatch Routes (Send to Police Stations)
# ───────────────────────────────────────────────────────

@app.post("/fir/{fir_id}/dispatch", tags=["FIR Dispatch"])
def dispatch_fir_to_station(
    fir_id: int,
    station_osm_id: Optional[str] = Query(None, description="Optional OSM station id to dispatch to"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Dispatch FIR to nearest police station or a selected OSM station."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can dispatch FIRs")
    
    fir = db.query(FIR).filter(FIR.id == fir_id).first()
    if not fir:
        raise HTTPException(status_code=404, detail="FIR not found")
    
    if fir.status != "signed":
        raise HTTPException(status_code=400, detail="FIR must be signed before dispatch")
    
    case = fir.case
    resolved_location = _resolve_case_location(db, case)
    if resolved_location["lat"] is None or resolved_location["lng"] is None:
        raise HTTPException(status_code=400, detail="No usable coordinates available for dispatch")

    try:
        candidates, used_radius_km = _find_stations_with_expanding_radius(
            resolved_location["lat"],
            resolved_location["lng"],
            limit=25,
            base_radius_km=10.0,
        )
        if not candidates:
            raise HTTPException(status_code=400, detail="No nearby police stations found")

        selected = None
        if station_osm_id:
            selected = next((s for s in candidates if str(s.get("osm_id")) == str(station_osm_id)), None)
            if not selected:
                raise HTTPException(status_code=404, detail="Selected station not found in nearby stations")
        else:
            selected = candidates[0]

        station = db.query(PoliceStation).filter(PoliceStation.osm_id == str(selected.get("osm_id"))).first()
        if not station:
            station = PoliceStation(
                osm_id=str(selected.get("osm_id")),
                name=selected.get("name") or "Police Station",
                address=selected.get("address"),
                lat=selected.get("lat"),
                lng=selected.get("lng"),
                phone=selected.get("phone"),
                city=resolved_location.get("city"),
                state=resolved_location.get("state"),
            )
            db.add(station)
            db.flush()

        dispatch = PoliceDispatch(
            fir_id=fir.id,
            station_id=station.id,
            method="manual",
            sent_at=datetime.utcnow(),
            status="sent",
        )
        db.add(dispatch)
        fir.status = "sent"
        db.commit()

        return {
            "status": "success",
            "message": "FIR dispatched successfully",
            "fir_id": fir.id,
            "dispatch_id": dispatch.id,
            "station": {
                "id": station.id,
                "name": station.name,
                "address": station.address,
                "phone": station.phone,
                "lat": station.lat,
                "lng": station.lng,
                "distance_km": selected.get("distance_km"),
            },
            "location_source": resolved_location.get("source"),
            "station_search_radius_km": used_radius_km,
            "dispatched_at": dispatch.sent_at.isoformat(),
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fir/{fir_id}/dispatch-auto", tags=["FIR Dispatch"])
def dispatch_fir_auto(
    fir_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Auto-dispatch FIR to 3 nearest police stations.
    
    Uses case's last seen location to find nearest stations via OpenMap.
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can dispatch FIRs")
    
    fir = db.query(FIR).filter(FIR.id == fir_id).first()
    if not fir:
        raise HTTPException(status_code=404, detail="FIR not found")
    
    if fir.status != "signed":
        raise HTTPException(status_code=400, detail="FIR must be signed before dispatch")
    
    case = fir.case
    resolved_location = _resolve_case_location(db, case)
    if resolved_location["lat"] is None or resolved_location["lng"] is None:
        raise HTTPException(
            status_code=400,
            detail="No usable coordinates available for auto-dispatch"
        )
    
    try:
        # Find 3 nearest police stations
        stations, used_radius_km = _find_stations_with_expanding_radius(
            resolved_location["lat"],
            resolved_location["lng"],
            limit=3,
            base_radius_km=10.0,
        )
        
        if not stations:
            raise HTTPException(
                status_code=400,
                detail="No police stations found near case location"
            )
        
        dispatches = []
        for station in stations:
            station_row = db.query(PoliceStation).filter(PoliceStation.osm_id == str(station.get("osm_id"))).first()
            if not station_row:
                station_row = PoliceStation(
                    osm_id=str(station.get("osm_id")),
                    name=station.get("name") or "Police Station",
                    address=station.get("address"),
                    lat=station.get("lat"),
                    lng=station.get("lng"),
                    phone=station.get("phone"),
                    city=resolved_location.get("city"),
                    state=resolved_location.get("state"),
                )
                db.add(station_row)
                db.flush()

            dispatch = PoliceDispatch(
                fir_id=fir.id,
                station_id=station_row.id,
                method="logged",
                sent_at=datetime.utcnow(),
                status="sent",
            )
            db.add(dispatch)
            dispatches.append(dispatch)

        fir.status = "sent"
        db.commit()
        
        return {
            "status": "success",
            "message": f"FIR auto-dispatched to {len(dispatches)} nearest stations",
            "fir_id": fir.id,
            "case_id": fir.case_id,
            "location_source": resolved_location.get("source"),
            "station_search_radius_km": used_radius_km,
            "dispatch_count": len(dispatches),
            "dispatches": [
                {
                    "dispatch_id": d.id,
                    "station_name": d.station.name if d.station else "Unknown",
                    "station_address": d.station.address if d.station else None,
                    "dispatch_status": d.status,
                    "dispatched_at": d.sent_at.isoformat() if d.sent_at else None,
                }
                for d in dispatches
            ]
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/fir/stats", tags=["FIR"])
def fir_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get FIR generation and dispatch statistics (admin only).
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view statistics")
    total_firs = db.query(FIR).count()
    draft_firs = db.query(FIR).filter(FIR.status == "draft").count()
    signed_firs = db.query(FIR).filter(FIR.status == "signed").count()
    sent_firs = db.query(FIR).filter(FIR.status == "sent").count()
    total_dispatches = db.query(PoliceDispatch).count()

    return {
        "status": "success",
        "total_firs": total_firs,
        "draft_firs": draft_firs,
        "signed_firs": signed_firs,
        "sent_firs": sent_firs,
        "total_dispatches": total_dispatches,
    }


# Root
@app.get("/", tags=["Root"])
def read_root():
    """API root endpoint."""
    return {
        "message": "Missing Person Tracker API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
