"""Verify the MongoDB connection, create indexes and run a write/read/delete test.

Run from the backend folder:  python -m scripts.setup_db
"""
import sys

from app import create_app
from app.db import ensure_indexes, get_db, ping_database


def main() -> int:
    app = create_app()
    with app.app_context():
        status = ping_database()
        print(f"Connection status: {status}")
        if status != "connected":
            print("Fix MONGODB_URI / Atlas network access, then run this again.")
            return 1

        db = get_db()
        ensure_indexes(db)
        print(f"Indexes ready in database '{db.name}'.")

        # Round-trip test with a throwaway document
        inserted = db.documents.insert_one({"user_id": "__setup_check__", "text": "ok"})
        found = db.documents.find_one({"_id": inserted.inserted_id})
        db.documents.delete_one({"_id": inserted.inserted_id})
        if not found:
            print("Write/read test FAILED.")
            return 1
        print("Write/read/delete test passed.")
        print("Collections now:", sorted(db.list_collection_names()))
    return 0


if __name__ == "__main__":
    sys.exit(main())