import pytest

from app.application.errors import NotFound
from app.application.notifications import EventDispatcher, NotificationStatus
from app.application.use_cases.concerts import RescheduleConcert, RescheduleConcertCommand
from app.domain.errors import InvalidValue, SchedulingConflict
from app.domain.events import ConcertRescheduled
from tests.application.conftest import at


def use_case(r):
    return RescheduleConcert(r["festivals"], r["stages"], r["artists"], EventDispatcher(r["notifier"]))


def test_valid_reschedule_is_saved_and_notified(repos):
    result = use_case(repos).execute(RescheduleConcertCommand(11, at(21), at(22)))
    assert result.value.slot.start == at(21)
    assert result.notification_status == NotificationStatus.SENT
    assert repos["festivals"].get(1).concert(11).slot.start == at(21)
    assert repos["notifier"].sent == [ConcertRescheduled(11, 1, at(21), at(22))]


def test_conflict_is_refused_nothing_saved_nothing_notified(repos):
    with pytest.raises(SchedulingConflict):
        use_case(repos).execute(RescheduleConcertCommand(11, at(18), at(19)))
    assert repos["festivals"].saved == 0
    assert repos["festivals"].get(1).concert(11).slot.start == at(20)
    assert repos["notifier"].sent == []


def test_invalid_slot_is_refused_before_loading(repos):
    with pytest.raises(InvalidValue):
        use_case(repos).execute(RescheduleConcertCommand(999, at(21), at(20)))


def test_unknown_concert(repos):
    with pytest.raises(NotFound):
        use_case(repos).execute(RescheduleConcertCommand(999, at(21), at(22)))


def test_notification_failure_does_not_cancel_the_change(repos):
    repos["notifier"].fail = True
    result = use_case(repos).execute(RescheduleConcertCommand(11, at(21), at(22)))
    assert result.notification_status == NotificationStatus.FAILED
    assert repos["festivals"].saved == 1
    assert repos["festivals"].get(1).concert(11).slot.start == at(21)
