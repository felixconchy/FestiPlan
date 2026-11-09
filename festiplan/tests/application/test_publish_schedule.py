import pytest

from app.application.errors import NotFound
from app.application.notifications import EventDispatcher, NotificationStatus
from app.application.use_cases.concerts import (RescheduleConcert, RescheduleConcertCommand,
                                                ReschedulePublishedConcert,
                                                ReschedulePublishedConcertCommand)
from app.application.use_cases.festivals import PublishSchedule, PublishScheduleCommand
from app.domain.errors import InvalidTransition, ScheduleLocked, SchedulingConflict
from app.domain.events import PublishedConcertRescheduled, SchedulePublished
from app.domain.model import Concert, ScheduleStatus
from app.domain.value_objects import TimeSlot
from tests.application.conftest import at


def build(cls, r):
    return cls(r["festivals"], r["stages"], r["artists"], EventDispatcher(r["notifier"]))


def publish(r):
    return build(PublishSchedule, r).execute(PublishScheduleCommand(1))


def test_publish_valid_schedule(repos):
    result = publish(repos)
    assert result.notification_status == NotificationStatus.SENT
    assert repos["festivals"].get(1).status == ScheduleStatus.PUBLISHED
    assert repos["notifier"].sent == [SchedulePublished(1, "Hellforge")]


def test_publish_unknown_festival(repos):
    with pytest.raises(NotFound):
        build(PublishSchedule, repos).execute(PublishScheduleCommand(999))


def test_r8_inconsistent_schedule_cannot_be_published(repos):
    festival = repos["festivals"].get(1)
    festival.concerts.append(Concert(None, 1, 1, 2, TimeSlot(at(18), at(19))))  # Iron Vow à deux endroits
    repos["festivals"].save(festival)
    with pytest.raises(SchedulingConflict):
        publish(repos)
    assert repos["festivals"].get(1).status == ScheduleStatus.PREPARATION
    assert repos["notifier"].sent == []


def test_cannot_publish_twice(repos):
    publish(repos)
    with pytest.raises(InvalidTransition):
        publish(repos)


def test_publish_succeeds_even_if_notification_fails(repos):
    repos["notifier"].fail = True
    assert publish(repos).notification_status == NotificationStatus.FAILED
    assert repos["festivals"].get(1).status == ScheduleStatus.PUBLISHED


def test_ordinary_reschedule_refused_after_publication(repos):
    publish(repos)
    with pytest.raises(ScheduleLocked):
        build(RescheduleConcert, repos).execute(RescheduleConcertCommand(11, at(21), at(22)))
    assert repos["festivals"].get(1).concert(11).slot.start == at(20)


def test_published_reschedule_procedure(repos):
    publish(repos)
    repos["notifier"].sent.clear()
    result = build(ReschedulePublishedConcert, repos).execute(
        ReschedulePublishedConcertCommand(11, at(21), at(22), "Retard du groupe"))
    assert result.notification_status == NotificationStatus.SENT
    festival = repos["festivals"].get(1)
    assert festival.concert(11).slot.start == at(21)
    assert festival.status == ScheduleStatus.PUBLISHED
    assert repos["notifier"].sent == [PublishedConcertRescheduled(11, 1, at(21), at(22), "Retard du groupe")]


def test_published_reschedule_refused_while_in_preparation(repos):
    with pytest.raises(InvalidTransition):
        build(ReschedulePublishedConcert, repos).execute(
            ReschedulePublishedConcertCommand(11, at(21), at(22), "motif"))
