"""
Database seeding script for Missing Person Tracker.
Populates the database with initial missing person cases.

Run: python seed.py
"""

import time
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import requests
from bs4 import BeautifulSoup

from config import settings
from database import Base
from models import User, Case, MissingPerson

# Database setup
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Data
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INDIAN_CITIES = [
    "Mumbai", "Delhi", "Chennai", "Kolkata", "Hyderabad",
    "Bengaluru", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
    "Patna", "Bhopal", "Surat", "Indore", "Visakhapatnam"
]

INDIAN_STATES = {
    "Mumbai": "Maharashtra",
    "Delhi": "Delhi",
    "Chennai": "Tamil Nadu",
    "Kolkata": "West Bengal",
    "Hyderabad": "Telangana",
    "Bengaluru": "Karnataka",
    "Pune": "Maharashtra",
    "Ahmedabad": "Gujarat",
    "Jaipur": "Rajasthan",
    "Lucknow": "Uttar Pradesh",
    "Patna": "Bihar",
    "Bhopal": "Madhya Pradesh",
    "Surat": "Gujarat",
    "Indore": "Madhya Pradesh",
    "Visakhapatnam": "Andhra Pradesh"
}

MALE_NAMES = [
    "Rajesh Kumar", "Amit Singh", "Vikram Patel", "Suresh Sharma",
    "Arjun Reddy", "Rohan Verma", "Deepak Mishra", "Arun Nair",
    "Nikhil Gupta", "Prakash Rao", "Hari Prasad", "Devendra Kumar",
    "Sanjay Dwivedi", "Ashok Pandey", "Manoj Desai", "Rahul Joshi",
    "Vinod Saxena", "Pradeep Yadav", "Manish Kumar", "Sandeep Singh"
]

FEMALE_NAMES = [
    "Priya Sharma", "Anjali Singh", "Neha Patel", "Pooja Verma",
    "Shreya Reddy", "Divya Mishra", "Riya Nair", "Swati Gupta",
    "Ananya Rao", "Isha Prasad", "Kavya Kumar", "Sneha Dwivedi",
    "Diya Pandey", "Megha Desai", "Ritika Joshi", "Sonya Saxena",
    "Vaishali Yadav", "Nisha Kumar", "Sakshi Singh", "Tanvi Kapoor"
]

DESCRIPTIONS = [
    "Last seen wearing blue shirt and jeans",
    "Missing since morning, has mental health condition",
    "Left for school but never returned",
    "Mentally challenged, non-verbal",
    "Wandered away from home",
    "Missing from train station",
    "Left home after argument",
    "Last seen near railway station",
    "Likely confused and disoriented",
    "Takes medication for health condition",
    "May be in distress",
    "Not familiar with area",
    "Possibly travelling with unknown person",
    "Last seen at local market"
]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Scraping
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def try_scrape_khoya_paya():
    """
    Try to fetch real missing person cases from Khoya Paya.
    Returns list of dicts with: name, age, gender, city, state, date_missing, description
    On failure or empty, returns empty list.
    """
    cases = []
    try:
        print("Attempting to fetch data from Khoya Paya...")
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get("https://khoyapaya.gov.in", headers=headers, timeout=5)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            # This is a placeholder - actual parsing depends on page structure
            print("✓ Khoya Paya accessible but parsing not implemented (placeholder)")
        else:
            print(f"✗ Khoya Paya returned {response.status_code}")
    except Exception as e:
        print(f"✗ Failed to fetch Khoya Paya: {str(e)}")
    
    return cases


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Synthetic Data Generation
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_synthetic_cases(count: int = 25):
    """Generate synthetic missing person cases with realistic Indian data."""
    cases = []
    
    for i in range(count):
        is_male = random.choice([True, False])
        name = random.choice(MALE_NAMES if is_male else FEMALE_NAMES)
        age = random.randint(8, 70)
        gender = "Male" if is_male else "Female"
        city = random.choice(INDIAN_CITIES)
        state = INDIAN_STATES.get(city, "India")
        
        # Date missing: within last 18 months
        days_ago = random.randint(1, 540)
        date_missing = (datetime.now() - timedelta(days=days_ago)).date()
        
        description = random.choice(DESCRIPTIONS)
        
        cases.append({
            "name": name,
            "age": age,
            "gender": gender,
            "city": city,
            "state": state,
            "date_missing": date_missing,
            "description": description
        })
    
    return cases


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Database Seeding
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def seed():
    """Main seed function."""
    print("\n" + "="*60)
    print("🌱 Database Seeding - Missing Person Tracker")
    print("="*60 + "\n")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created\n")
    
    db = SessionLocal()
    
    try:
        # Try to scrape real data
        cases = try_scrape_khoya_paya()
        
        # If scrape failed or returned too few, use synthetic data
        if len(cases) < 10:
            print("Generating 25 synthetic cases...\n")
            cases = generate_synthetic_cases(25)
        
        total_cases = len(cases)
        
        # Get or create "System Import" user
        import_user = db.query(User).filter(User.email == "import@example.com").first()
        if not import_user:
            from auth import hash_password
            import_user = User(
                name="System Import",
                email="import@example.com",
                hashed_password=hash_password("System@1234"),
                role="user",
                is_active=True
            )
            db.add(import_user)
            db.commit()
            print("Created System Import user\n")
        
        # Seed cases
        for idx, case_data in enumerate(cases, 1):
            try:
                # Generate case number: MP-YYYY-NNNNN
                year = datetime.now().year
                case_number = f"MP-{year}-{idx:05d}"
                
                # Check if case already exists
                existing = db.query(Case).filter(Case.case_number == case_number).first()
                if existing:
                    print(f"[{idx}/{total_cases}] ⊘ Case {case_number} already exists")
                    continue
                
                # Create case
                case = Case(
                    case_number=case_number,
                    reported_by_id=import_user.id,
                    status="open",
                    priority="normal",
                    police_dispatch_mode="manual"
                )
                db.add(case)
                db.flush()  # Get case ID
                
                # Create missing person
                missing_person = MissingPerson(
                    case_id=case.id,
                    full_name=case_data["name"],
                    age=case_data["age"],
                    gender=case_data["gender"],
                    last_seen_date=case_data["date_missing"],
                    last_seen_city=case_data["city"],
                    last_seen_state=case_data["state"],
                    description=case_data["description"],
                    photo_url=None
                )
                db.add(missing_person)
                db.commit()
                
                print(f"✓ Seeded [{idx}/{total_cases}]: {case_data['name']} from {case_data['city']}")
                time.sleep(0.3)  # Rate limiting
                
            except Exception as e:
                db.rollback()
                print(f"✗ Error seeding case {idx}: {str(e)}")
                continue
        
        print("\n" + "="*60)
        print(f"✓ Seeding complete! {total_cases} cases added")
        print("="*60 + "\n")
        
    finally:
        db.close()


if __name__ == "__main__":
    seed()
