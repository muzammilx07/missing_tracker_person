"""
Alert Service - Manages notifications and alerts
Handles match notifications, recipient identification, and alert logging
"""

from sqlalchemy.orm import Session
from datetime import datetime
import logging

from models import Alert, User, Match, Case, MissingPerson, Sighting, VolunteerProfile

logger = logging.getLogger(__name__)


def get_alert_recipients(case_id: int, db: Session) -> dict:
    """
    Get all recipients for case alerts (admins, family, volunteers).
    
    Args:
        case_id: Case ID
        db: Database session
    
    Returns:
        dict with keys: admins, family, volunteers (each a list of User objects)
    """
    
    # Get case and missing person
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        return {"admins": [], "family": [], "volunteers": []}
    
    missing_person = db.query(MissingPerson).filter(MissingPerson.case_id == case_id).first()
    
    # Get all admins
    admins = db.query(User).filter(User.role == "admin").all()
    
    # Get family members
    from models import CaseFamilyMember
    family_members = db.query(CaseFamilyMember).filter(CaseFamilyMember.case_id == case_id).all()
    family_users = [fm.user for fm in family_members if fm.user]
    
    # Get volunteers - two groups:
    # 1. Volunteers assigned to this case
    from models import CaseVolunteer
    case_volunteers = db.query(CaseVolunteer).filter(CaseVolunteer.case_id == case_id).all()
    assigned_volunteers = [cv.volunteer.user for cv in case_volunteers if cv.volunteer and cv.volunteer.user]
    
    # 2. Approved volunteers with coverage matching case location
    coverage_volunteers = []
    if missing_person:
        mp_city = missing_person.last_seen_city
        mp_state = missing_person.last_seen_state
        
        approved_profiles = db.query(VolunteerProfile).filter(
            VolunteerProfile.status == "approved"
        ).all()
        
        for profile in approved_profiles:
            # Match by city
            if profile.coverage_type == "city" and profile.coverage_city and mp_city:
                if profile.coverage_city.lower() == mp_city.lower():
                    if profile.user and profile.user not in assigned_volunteers:
                        coverage_volunteers.append(profile.user)
            # Match by state
            elif profile.coverage_type == "state" and profile.coverage_state and mp_state:
                if profile.coverage_state.lower() == mp_state.lower():
                    if profile.user and profile.user not in assigned_volunteers:
                        coverage_volunteers.append(profile.user)
            # Any coverage type
            elif profile.coverage_type == "any":
                if profile.user and profile.user not in assigned_volunteers:
                    coverage_volunteers.append(profile.user)
    
    # Combine and deduplicate volunteers
    all_volunteers = assigned_volunteers + coverage_volunteers
    unique_volunteers = []
    seen_ids = set()
    for v in all_volunteers:
        if v and v.id not in seen_ids:
            unique_volunteers.append(v)
            seen_ids.add(v.id)
    
    return {
        "admins": admins,
        "family": family_users,
        "volunteers": unique_volunteers
    }


def log_alert(db: Session, case_id: int, match_id: int, alert_type: str, 
              recipient_type: str, message: str):
    """
    Create and log an alert record.
    
    Args:
        db: Database session
        case_id: Case ID
        match_id: Match ID (can be None for non-match alerts)
        alert_type: Type of alert (e.g., "match_found", "fir_sent", "case_opened")
        recipient_type: Recipient group ("admin", "family", "volunteer")
        message: Alert message text
    """
    
    try:
        alert = Alert(
            case_id=case_id,
            match_id=match_id,
            alert_type=alert_type,
            recipient_type=recipient_type,
            message=message,
            created_at=datetime.utcnow()
        )
        db.add(alert)
        db.commit()
        logger.info(f"Alert logged: {alert_type} for case {case_id}")
    except Exception as e:
        logger.error(f"Failed to log alert: {str(e)}")
        db.rollback()


def notify_match_found(match_id: int, db: Session):
    """
    Notify all relevant parties when a match is found.
    Creates alert records for admins, family, and volunteers.
    
    Args:
        match_id: Match ID
        db: Database session
    """
    
    try:
        # Fetch match and related data
        match = db.query(Match).filter(Match.id == match_id).first()
        if not match:
            logger.error(f"Match {match_id} not found")
            return
        
        case = db.query(Case).filter(Case.id == match.case_id).first()
        if not case:
            logger.error(f"Case {match.case_id} not found")
            return
        
        missing_person = db.query(MissingPerson).filter(MissingPerson.case_id == case.id).first()
        sighting = db.query(Sighting).filter(Sighting.id == match.sighting_id).first()
        
        # Build message
        mp_name = missing_person.full_name if missing_person else "Unknown"
        mp_age = missing_person.age if missing_person else "Unknown"
        confidence_pct = int(match.confidence * 100)
        sighting_city = sighting.sighting_city if sighting else "Unknown"
        sighting_date = sighting.created_at.strftime("%d-%m-%Y") if sighting else "Unknown"
        
        message = (
            f"MATCH FOUND — Case {case.case_number}\n"
            f"Missing: {mp_name}, Age {mp_age}\n"
            f"Confidence: {confidence_pct}% ({match.confidence_label})\n"
            f"Sighted in: {sighting_city} on {sighting_date}"
        )
        
        # Get recipients
        recipients = get_alert_recipients(case.id, db)
        
        # Log alerts for each group
        for admin in recipients["admins"]:
            log_alert(db, case.id, match_id, "match_found", "admin", message)
        
        for family_member in recipients["family"]:
            log_alert(db, case.id, match_id, "match_found", "family", message)
        
        for volunteer in recipients["volunteers"]:
            log_alert(db, case.id, match_id, "match_found", "volunteer", message)
        
        logger.info(f"Match notifications sent for match {match_id}")
        
    except Exception as e:
        logger.error(f"Error notifying match found: {str(e)}")


def notify_fir_sent(fir_id: int, case_id: int, db: Session):
    """
    Notify recipients when FIR is sent to police stations.
    
    Args:
        fir_id: FIR ID
        case_id: Case ID
        db: Database session
    """
    
    try:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            return
        
        message = f"FIR Sent to Police — Case {case.case_number}"
        
        recipients = get_alert_recipients(case.id, db)
        
        for admin in recipients["admins"]:
            log_alert(db, case.id, None, "fir_sent", "admin", message)
        
        for family_member in recipients["family"]:
            log_alert(db, case.id, None, "fir_sent", "family", message)
        
        logger.info(f"FIR sent notifications for case {case_id}")
        
    except Exception as e:
        logger.error(f"Error notifying FIR sent: {str(e)}")


def notify_case_opened(case_id: int, db: Session):
    """
    Notify admins when a new missing person case is opened.
    
    Args:
        case_id: Case ID
        db: Database session
    """
    
    try:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            return
        
        missing_person = db.query(MissingPerson).filter(MissingPerson.case_id == case_id).first()
        mp_name = missing_person.full_name if missing_person else "Unknown"
        
        message = f"New Case Opened — Missing: {mp_name} — Case {case.case_number}"
        
        # Notify admins only
        admins = db.query(User).filter(User.role == "admin").all()
        for admin in admins:
            log_alert(db, case.id, None, "case_opened", "admin", message)
        
        logger.info(f"Case opened notifications for case {case_id}")
        
    except Exception as e:
        logger.error(f"Error notifying case opened: {str(e)}")
