from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, Date,
    LargeBinary, ForeignKey, UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(15), nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String(20), default="user", nullable=False)  # user / admin
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    volunteer_profile = relationship("VolunteerProfile", back_populates="user", foreign_keys="VolunteerProfile.user_id", uselist=False, cascade="all, delete-orphan")
    cases_reported = relationship("Case", foreign_keys="Case.reported_by_id", back_populates="reported_by")
    family_members = relationship("CaseFamilyMember", foreign_keys="CaseFamilyMember.user_id", back_populates="user")
    volunteer_assignments = relationship("CaseVolunteer", foreign_keys="CaseVolunteer.volunteer_user_id", back_populates="volunteer")


class VolunteerProfile(Base):
    __tablename__ = "volunteer_profiles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    status = Column(String(20), default="pending", nullable=False)  # pending / approved / rejected
    coverage_type = Column(String(20), nullable=True)  # city / state / any
    coverage_city = Column(String(100), nullable=True)
    coverage_state = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="volunteer_profile")


class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_number = Column(String(20), unique=True, nullable=False, index=True)
    reported_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(30), default="open", nullable=False)  # open / matched / under_investigation / closed / false_alarm
    priority = Column(String(20), default="normal", nullable=False)  # normal / high / critical
    police_dispatch_mode = Column(String(20), default="manual", nullable=False)  # manual / auto
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    reported_by = relationship("User", foreign_keys=[reported_by_id], back_populates="cases_reported")
    missing_person = relationship("MissingPerson", back_populates="case", uselist=False, cascade="all, delete-orphan")
    family_members = relationship("CaseFamilyMember", back_populates="case", cascade="all, delete-orphan")
    volunteers = relationship("CaseVolunteer", back_populates="case", cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="case", cascade="all, delete-orphan")
    firs = relationship("FIR", back_populates="case", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="case", cascade="all, delete-orphan")


class CaseFamilyMember(Base):
    __tablename__ = "case_family_members"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    added_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (UniqueConstraint("case_id", "user_id", name="uq_case_family_member"),)
    
    # Relationships
    case = relationship("Case", back_populates="family_members")
    user = relationship("User", foreign_keys=[user_id], back_populates="family_members")


class CaseVolunteer(Base):
    __tablename__ = "case_volunteers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    volunteer_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    case = relationship("Case", back_populates="volunteers")
    volunteer = relationship("User", foreign_keys=[volunteer_user_id], back_populates="volunteer_assignments")


class MissingPerson(Base):
    __tablename__ = "missing_persons"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.id"), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False, index=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(10), nullable=True)
    last_seen_date = Column(Date, nullable=True)
    last_seen_city = Column(String(100), nullable=True)
    last_seen_state = Column(String(100), nullable=True)
    last_seen_address = Column(Text, nullable=True)
    last_seen_lat = Column(Float, nullable=True)
    last_seen_lng = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    photo_url = Column(String(500), nullable=True)
    face_encoding = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    case = relationship("Case", back_populates="missing_person")


class Sighting(Base):
    __tablename__ = "sightings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    reporter_name = Column(String(100), nullable=True)
    reporter_phone = Column(String(15), nullable=True)
    sighting_lat = Column(Float, nullable=False)
    sighting_lng = Column(Float, nullable=False)
    sighting_city = Column(String(100), nullable=True)
    sighting_state = Column(String(100), nullable=True)
    sighting_address = Column(Text, nullable=True)
    photo_url = Column(String(500), nullable=False)
    face_encoding = Column(LargeBinary, nullable=True)
    status = Column(String(20), default="pending", nullable=False)  # pending / processing / matched / no_match / no_face
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    matches = relationship("Match", back_populates="sighting")


class Match(Base):
    __tablename__ = "matches"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    sighting_id = Column(Integer, ForeignKey("sightings.id"), nullable=False)
    confidence = Column(Float, nullable=False)
    confidence_label = Column(String(20), nullable=True)  # low / medium / high / very_high
    match_type = Column(String(20), nullable=True)  # auto / review
    status = Column(String(30), default="pending", nullable=False)  # pending / auto_confirmed / confirmed / rejected
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    admin_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    case = relationship("Case", back_populates="matches")
    sighting = relationship("Sighting", back_populates="matches")
    alerts = relationship("Alert", back_populates="match")


class PoliceStation(Base):
    __tablename__ = "police_stations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    osm_id = Column(String(50), unique=True, nullable=False)  # OpenStreetMap node id
    name = Column(String(200), nullable=False)
    address = Column(Text, nullable=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    phone = Column(String(50), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    cached_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    dispatches = relationship("PoliceDispatch", back_populates="station")


class FIR(Base):
    __tablename__ = "firs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)
    fir_number = Column(String(50), unique=True, nullable=False, index=True)
    pdf_url = Column(String(500), nullable=True)
    status = Column(String(20), default="draft", nullable=False)  # draft / signed / sent
    signed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    signed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    case = relationship("Case", back_populates="firs")
    dispatches = relationship("PoliceDispatch", back_populates="fir")


class PoliceDispatch(Base):
    __tablename__ = "police_dispatches"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fir_id = Column(Integer, ForeignKey("firs.id"), nullable=False)
    station_id = Column(Integer, ForeignKey("police_stations.id"), nullable=False)
    method = Column(String(20), nullable=False)  # logged / manual
    sent_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="pending", nullable=False)  # pending / sent / failed
    
    # Relationships
    fir = relationship("FIR", back_populates="dispatches")
    station = relationship("PoliceStation", back_populates="dispatches")


class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)
    alert_type = Column(String(50), nullable=False)  # match_found / new_sighting / fir_sent / volunteer_assigned / case_update
    recipient_type = Column(String(20), nullable=False)  # admin / volunteer / family / all
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    case = relationship("Case", back_populates="alerts")
    match = relationship("Match", back_populates="alerts")
