"""Tests de l'adaptateur de notification."""
from datetime import datetime

import pytest

from app.adapters.notifications.email_notifier import PRODUCTION, PUBLIC, EmailNotifier
from app.application.ports import NotificationError
from app.domain.events import ConcertRescheduled, PublishedConcertRescheduled, SchedulePublished

START, END = datetime(2027, 6, 18, 21), datetime(2027, 6, 18, 22)


def test_reschedule_is_sent_to_production(capsys):
    EmailNotifier().notify(ConcertRescheduled(11, 1, START, END))
    out = capsys.readouterr().out
    assert f"to={PRODUCTION}" in out and "#11" in out


def test_published_changes_are_sent_to_public_with_reason(capsys):
    EmailNotifier().notify(PublishedConcertRescheduled(11, 1, START, END, "Retard du groupe"))
    EmailNotifier().notify(SchedulePublished(1, "Hellforge"))
    out = capsys.readouterr().out
    assert out.count(f"to={PUBLIC}") == 2
    assert "Retard du groupe" in out


def test_simulated_outage_raises_port_error(capsys):
    with pytest.raises(NotificationError):
        EmailNotifier(fail=True).notify(ConcertRescheduled(11, 1, START, END))
    assert capsys.readouterr().out == ""
