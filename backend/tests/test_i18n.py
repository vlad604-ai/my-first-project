"""Every translation key referenced in code must exist in the French catalog."""
import re
from pathlib import Path

from app.i18n import fr
from app.models import BookingStatus, ProStatus, QuoteRequestStatus, QuoteStatus, Urgency, WorkMode

ROOT = Path(__file__).resolve().parents[1]
KEY_RE = re.compile(r"""\bt\(\s*["']([a-z_]+\.[a-z0-9_.]+)["']""")
TERNARY_RE = re.compile(
    r"""\bt\(\s*["']([a-z_]+\.[a-z0-9_.]+)["']\s+if\s.+?\selse\s+["']([a-z_]+\.[a-z0-9_.]+)["']""", re.S)


def test_static_keys_exist():
    missing = set()
    for path in list((ROOT / "app").rglob("*.py")) + list((ROOT / "bot").rglob("*.py")):
        src = path.read_text()
        keys = set(KEY_RE.findall(src))
        for a, b in TERNARY_RE.findall(src):
            keys |= {a, b}
        missing |= {k for k in keys if k not in fr.MESSAGES and not k.endswith(".")}
    assert not missing, sorted(missing)


def test_dynamic_keys_exist():
    expected = [f"status.{s.value}" for s in BookingStatus] + [f"prostatus.{s.value}" for s in ProStatus]
    expected += [f"qstatus.{s.value}" for s in QuoteRequestStatus] + [f"quote.status.{s.value}" for s in QuoteStatus]
    expected += [f"urgency.{u.value}" for u in Urgency] + [f"mode.{m.value}" for m in WorkMode]
    expected += [f"avail.{p}" for p in ("now", "30min", "1h", "3h", "today", "tomorrow")]
    expected += [f"notif.reminder.{k}" for k in ("24h", "1h")]
    expected += [f"notif.pro.status.{s.value}" for s in ProStatus if s.value != "pending"]
    expected += [f"booking.err.{c}" for c in ("slot_unavailable", "pro_unavailable", "self_booking", "unknown_service",
                                              "not_mobile", "address_required", "out_of_zone", "not_allowed",
                                              "invalid_state")]
    expected += [f"pf.{f}" for f in ("description", "phone", "address", "website", "specialties", "logo", "photos")]
    expected += [f"pf.ask_{f}" for f in ("description", "phone", "address", "website", "specialties", "logo",
                                         "photos")]
    missing = [k for k in expected if k not in fr.MESSAGES]
    assert not missing, missing


def test_placeholders_consistent_between_languages():
    from app.i18n import en

    for key, text in en.MESSAGES.items():
        assert key in fr.MESSAGES, f"{key} missing in fr"
        assert set(re.findall(r"{(\w+)}", text)) == set(re.findall(r"{(\w+)}", fr.MESSAGES[key])), key
