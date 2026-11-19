from datetime import datetime

from bson import ObjectId

from app.utils.mongo import serialize


def test_serialize_converts_ids_and_dates():
    oid = ObjectId()
    out = serialize({"_id": oid, "when": datetime(2026, 1, 1), "nested": [{"id": oid}]})
    assert out["_id"] == str(oid)
    assert out["when"].startswith("2026-01-01T00:00:00")
    assert out["nested"][0]["id"] == str(oid)