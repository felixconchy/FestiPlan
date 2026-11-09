from datetime import datetime

import pytest

from app.domain.errors import InvalidValue
from app.domain.model import Incident, Stage
from app.domain.value_objects import Equipment, FestivalPeriod, TimeSlot


def slot(a, b):
    return TimeSlot(datetime(2027, 6, 18, a), datetime(2027, 6, 18, b))


@pytest.mark.parametrize("start,end", [(20, 19), (20, 20)])
def test_r1_slot_end_must_be_strictly_after_start(start, end):
    with pytest.raises(InvalidValue):
        slot(start, end)


def test_slots_overlap():
    assert slot(18, 20).overlaps(slot(19, 21))
    assert slot(18, 20).overlaps(slot(18, 20))
    assert slot(18, 20).overlaps(slot(17, 22))


def test_adjacent_slots_do_not_overlap():
    assert not slot(18, 19).overlaps(slot(19, 20))
    assert not slot(19, 20).overlaps(slot(18, 19))


def test_timeslot_is_immutable_value_object():
    s = slot(18, 19)
    assert s == slot(18, 19)
    with pytest.raises(Exception):
        s.start = datetime(2027, 1, 1)


def test_festival_period_contains_slot():
    period = FestivalPeriod(datetime(2027, 6, 18, 10), datetime(2027, 6, 18, 23))
    assert period.contains(slot(18, 19))
    assert not period.contains(slot(9, 11))
    assert not period.contains(TimeSlot(datetime(2027, 6, 18, 22), datetime(2027, 6, 19, 1)))


def test_equipment_missing_from():
    needs = Equipment.of(["special_lighting", " large_rigging ", ""])
    assert needs.missing_from(Equipment.of(["special_lighting"])) == {"large_rigging"}
    assert not needs.missing_from(Equipment.of(["large_rigging", "special_lighting", "pyro"]))


@pytest.mark.parametrize("capacity", [0, -10])
def test_r9_stage_capacity_must_be_positive(capacity):
    with pytest.raises(InvalidValue):
        Stage(None, 1, "Mainstage", capacity)


@pytest.mark.parametrize("description", ["", "   "])
def test_r10_incident_description_must_not_be_empty(description):
    with pytest.raises(InvalidValue):
        Incident(None, 1, description, datetime(2027, 6, 18, 18))
