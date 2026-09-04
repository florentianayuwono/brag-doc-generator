from datetime import datetime, timezone
from bragdoc.models import WorkItem


def _item():
    return WorkItem(
        source="github_pr",
        project="aproxy-operator",
        org="canonical",
        title="Add PS7 support",
        url="https://github.com/canonical/aproxy-operator/pull/123",
        date=datetime(2026, 5, 14, tzinfo=timezone.utc),
        role="author",
        state="merged",
        identifier="#123",
        extra={"additions": 10},
    )


def test_roundtrip_json():
    item = _item()
    restored = WorkItem.from_dict(item.to_dict())
    assert restored == item


def test_date_serializes_to_iso():
    d = _item().to_dict()
    assert d["date"] == "2026-05-14T00:00:00+00:00"
    assert isinstance(d["extra"], dict)
