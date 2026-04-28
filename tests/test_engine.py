from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from walter_relance.engine import evaluate
from walter_relance.models import ActionLog, Preferences, Progress, Session, Student

Paris = ZoneInfo("Europe/Paris")


def _student_inactive_fixture() -> tuple[Student, Progress, Session, Preferences, datetime]:
    """Construit un apprenant en retard sous le checkpoint cp_25 (voir config/cpf_standard.yaml)."""
    sid = "student-test-suite"
    session_id = "session-test-suite"
    now = datetime(2025, 1, 9, 14, 0, 0, tzinfo=Paris)
    starting = datetime(2025, 1, 1).date()
    ending = datetime(2025, 2, 1).date()
    product_h = 100.0
    total_sec = int(product_h * 3600)
    student = Student(
        id=sid,
        first_name="Test",
        last_name="User",
        email="test.suite@example.com",
        phone="+33600000001",
        locale="fr-FR",
    )
    progress = Progress(
        student_id=sid,
        session_id=session_id,
        session_time_sec=50,
        last_activity_at=now,
        validated=False,
    )
    session = Session(
        id=session_id,
        student_id=sid,
        session_type="cpf",
        starting_date=starting,
        ending_date=ending,
        product_duration_h=product_h,
        status="Running",
    )
    prefs = Preferences(
        student_id=sid,
        opt_out_per_channel={"email": False, "sms": False, "call": False},
        tz="Europe/Paris",
    )
    return student, progress, session, prefs, now.astimezone(UTC)


def test_inactive_student_at_25pct_gets_email_sms_and_call(scenario_cpf):
    student, progress, session, prefs, now = _student_inactive_fixture()
    actions = evaluate(
        student,
        progress,
        session,
        prefs,
        scenario_cpf,
        last_actions=[],
        now=now,
    )
    channels = {a.channel for a in actions}
    assert channels == {"email", "sms", "call"}
    tmpl = {a.template_id for a in actions}
    assert tmpl == {"cpf_wakeup_email", "cpf_wakeup_sms", "cpf_wakeup_call"}


def test_on_track_student_gets_no_action(scenario_cpf):
    sid = "student-test-suite-ontrack"
    session_id = "session-test-suite-2"
    now = datetime(2025, 1, 9, 14, 0, 0, tzinfo=Paris)
    starting = datetime(2025, 1, 1).date()
    ending = datetime(2025, 2, 1).date()
    product_h = 100.0
    total_sec = int(product_h * 3600)
    student = Student(
        id=sid,
        first_name="A",
        last_name="B",
        email="on@example.com",
        phone="+33600000002",
        locale="fr-FR",
    )
    progress = Progress(
        student_id=sid,
        session_id=session_id,
        session_time_sec=int(total_sec * 0.56),
        last_activity_at=now,
        validated=False,
    )
    session = Session(
        id=session_id,
        student_id=sid,
        session_type="cpf",
        starting_date=starting,
        ending_date=ending,
        product_duration_h=product_h,
        status="Running",
    )
    prefs = Preferences(student_id=sid, opt_out_per_channel={}, tz="Europe/Paris")
    assert evaluate(student, progress, session, prefs, scenario_cpf, [], now.astimezone(UTC)) == []


def test_dedupe_per_channel_respects_different_windows(scenario_cpf):
    student, progress, session, prefs, now = _student_inactive_fixture()
    last = [
        ActionLog(
            student_id=student.id,
            scenario_id="cpf-standard",
            checkpoint_id="cp_25",
            channel="sms",
            template_id="cpf_wakeup_sms",
            sent_at=datetime(2025, 1, 6, 10, 0, 0, tzinfo=UTC),
            dedup_key="prior",
        )
    ]
    actions = evaluate(student, progress, session, prefs, scenario_cpf, last, now.astimezone(UTC))
    ch = [a.channel for a in actions]
    assert "sms" not in ch
    assert "email" in ch
    assert "call" in ch


def test_opted_out_call_only_gets_email_and_sms(scenario_cpf):
    student, progress, session, prefs, now = _student_inactive_fixture()
    prefs = prefs.model_copy(
        update={
            "opt_out_per_channel": {
                "email": False,
                "sms": False,
                "call": True,
            }
        }
    )
    actions = evaluate(student, progress, session, prefs, scenario_cpf, [], now.astimezone(UTC))
    assert {a.channel for a in actions} == {"email", "sms"}


def test_validated_student_gets_no_action(scenario_cpf):
    student, progress, session, prefs, now = _student_inactive_fixture()
    progress = progress.model_copy(update={"validated": True})
    assert evaluate(student, progress, session, prefs, scenario_cpf, [], now.astimezone(UTC)) == []
