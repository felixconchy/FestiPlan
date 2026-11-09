from datetime import datetime

import pytest

from app.domain.errors import (InvalidTransition, InvalidValue, RuleViolation,
                               ScheduleLocked, SchedulingConflict)
from app.domain.events import (ConcertRescheduled, PublishedConcertRescheduled,
                               SchedulePublished)
from app.domain.model import (Artist, Concert, ConcertStatus, Festival, ScheduleStatus,
                              Stage)
from app.domain.value_objects import Equipment, FestivalPeriod, TimeSlot


def at(h, day=18):
    return datetime(2027, 6, day, h)


def slot(a, b, day=18):
    return TimeSlot(at(a, day), at(b, day))


@pytest.fixture()
def ctx():
    festival = Festival(1, "Hellforge", "Clisson", FestivalPeriod(at(10), at(23, 20)))
    main = Stage(1, 1, "Mainstage", 50000, Equipment.of(["special_lighting"]))
    warzone = Stage(2, 1, "Warzone", 15000)
    iron = Artist(1, "Iron Vow", "Heavy")
    crimson = Artist(2, "Crimson Engine", "Thrash")
    festival.concerts = [
        Concert(10, 1, iron.id, main.id, slot(18, 19)),
        Concert(11, 1, crimson.id, main.id, slot(20, 21)),
    ]
    return festival, {1: main, 2: warzone}, {1: iron, 2: crimson}


# --- programmation ----------------------------------------------------------------------

def test_schedule_valid_concert(ctx):
    festival, stages, artists = ctx
    concert = festival.schedule_concert(artists[2], stages[2], slot(18, 19, day=19))
    assert concert in festival.concerts


def test_r2_cannot_schedule_on_occupied_stage(ctx):
    festival, stages, artists = ctx
    with pytest.raises(SchedulingConflict):
        festival.schedule_concert(Artist(3, "Other", "Doom"), stages[1], slot(18, 19))


def test_r4_stage_must_belong_to_festival(ctx):
    festival, _, artists = ctx
    foreign = Stage(9, 2, "Ailleurs", 100)
    with pytest.raises(RuleViolation):
        festival.schedule_concert(artists[1], foreign, slot(12, 13))


def test_r5_required_equipment_must_be_available(ctx):
    festival, stages, _ = ctx
    picky = Artist(3, "Picky", "Prog", Equipment.of(["pyrotechnics"]))
    with pytest.raises(RuleViolation, match="pyrotechnics"):
        festival.schedule_concert(picky, stages[1], slot(12, 13))


def test_r6_concert_must_be_inside_festival_period(ctx):
    festival, stages, artists = ctx
    with pytest.raises(RuleViolation):
        festival.schedule_concert(artists[1], stages[2], slot(8, 9))


# --- déplacement (défaut 1) -------------------------------------------------------------

def test_r2_reschedule_onto_occupied_stage_is_refused_and_nothing_changes(ctx):
    festival, stages, artists = ctx
    with pytest.raises(SchedulingConflict, match="scène"):
        festival.reschedule_concert(11, slot(18, 20), stages[1], artists[2])
    assert festival.concert(11).slot == slot(20, 21)
    assert festival.pull_events() == []


def test_r3_artist_cannot_play_two_overlapping_concerts_on_different_stages(ctx):
    festival, stages, artists = ctx
    festival.concerts.append(Concert(12, 1, 1, 2, slot(12, 13)))  # Iron Vow sur Warzone
    with pytest.raises(SchedulingConflict, match="artiste"):
        festival.reschedule_concert(12, slot(18, 19), stages[2], artists[1])


def test_valid_reschedule_is_accepted_and_emits_event(ctx):
    festival, stages, artists = ctx
    festival.reschedule_concert(11, slot(21, 22), stages[1], artists[2])
    assert festival.concert(11).slot == slot(21, 22)
    assert festival.pull_events() == [ConcertRescheduled(11, 1, at(21), at(22))]


def test_reschedule_on_its_own_slot_is_not_a_conflict(ctx):
    festival, stages, artists = ctx
    festival.reschedule_concert(11, slot(20, 22), stages[1], artists[2])
    assert festival.concert(11).slot == slot(20, 22)


def test_cancelled_concert_frees_the_slot_and_cannot_be_moved(ctx):
    festival, stages, artists = ctx
    festival.cancel_concert(10)
    assert festival.concert(10).status == ConcertStatus.CANCELLED
    festival.reschedule_concert(11, slot(18, 19), stages[1], artists[2])
    with pytest.raises(InvalidTransition):
        festival.reschedule_concert(10, slot(12, 13), stages[1], artists[1])
    with pytest.raises(InvalidTransition):
        festival.cancel_concert(10)


# --- états du planning (défaut 3, R7, R8) -----------------------------------------------

def test_publish_valid_schedule(ctx):
    festival, stages, artists = ctx
    festival.publish(stages, artists)
    assert festival.status == ScheduleStatus.PUBLISHED
    assert festival.pull_events() == [SchedulePublished(1, "Hellforge")]


def test_cannot_publish_twice(ctx):
    festival, stages, artists = ctx
    festival.publish(stages, artists)
    with pytest.raises(InvalidTransition):
        festival.publish(stages, artists)


def test_r8_cannot_publish_inconsistent_schedule(ctx):
    festival, stages, artists = ctx
    festival.concerts.append(Concert(12, 1, 1, 2, slot(18, 19)))  # données incohérentes héritées
    with pytest.raises(SchedulingConflict):
        festival.publish(stages, artists)
    assert festival.status == ScheduleStatus.PREPARATION


@pytest.mark.parametrize("operation", ["reschedule", "cancel", "schedule"])
def test_r7_ordinary_operations_refused_once_published(ctx, operation):
    festival, stages, artists = ctx
    festival.publish(stages, artists)
    with pytest.raises(ScheduleLocked):
        if operation == "reschedule":
            festival.reschedule_concert(11, slot(21, 22), stages[1], artists[2])
        elif operation == "cancel":
            festival.cancel_concert(11)
        else:
            festival.schedule_concert(artists[2], stages[2], slot(12, 13))
    assert festival.concert(11).slot == slot(20, 21)


def test_published_reschedule_procedure(ctx):
    festival, stages, artists = ctx
    festival.publish(stages, artists)
    festival.pull_events()
    festival.reschedule_published_concert(11, slot(21, 22), "Retard du groupe", stages[1], artists[2])
    assert festival.concert(11).slot == slot(21, 22)
    assert festival.status == ScheduleStatus.PUBLISHED
    assert festival.pull_events() == [PublishedConcertRescheduled(11, 1, at(21), at(22), "Retard du groupe")]


def test_published_reschedule_still_checks_conflicts(ctx):
    festival, stages, artists = ctx
    festival.publish(stages, artists)
    with pytest.raises(SchedulingConflict):
        festival.reschedule_published_concert(11, slot(18, 19), "motif", stages[1], artists[2])


def test_published_reschedule_requires_reason_and_published_state(ctx):
    festival, stages, artists = ctx
    with pytest.raises(InvalidTransition):
        festival.reschedule_published_concert(11, slot(21, 22), "motif", stages[1], artists[2])
    festival.publish(stages, artists)
    with pytest.raises(InvalidValue):
        festival.reschedule_published_concert(11, slot(21, 22), "  ", stages[1], artists[2])
