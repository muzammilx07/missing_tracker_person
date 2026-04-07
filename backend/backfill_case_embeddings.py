import requests

from database import SessionLocal
from models import MissingPerson
from services.face_service import extract_encoding, is_face_engine_available


def main() -> None:
    db = SessionLocal()
    updated = 0
    failed = 0

    print(f"face_model_available={is_face_engine_available()}")

    rows = (
        db.query(MissingPerson)
        .filter(MissingPerson.face_encoding.is_(None), MissingPerson.photo_url.isnot(None))
        .all()
    )
    print(f"to_process={len(rows)}")

    for mp in rows:
        try:
            response = requests.get(mp.photo_url, timeout=25)
            response.raise_for_status()
            encoding = extract_encoding(response.content)
            if encoding:
                mp.face_encoding = encoding
                updated += 1
                print(f"updated case {mp.case_id}")
            else:
                failed += 1
                print(f"no-face case {mp.case_id}")
        except Exception as exc:
            failed += 1
            print(f"failed case {mp.case_id}: {str(exc)[:140]}")

    db.commit()
    db.close()

    print(f"updated={updated} failed={failed}")


if __name__ == "__main__":
    main()
