"""Doubles de test : implémentations en mémoire des ports (aucune base, aucun réseau)."""
import copy
from itertools import count

from app.application import ports
from app.application.ports import NotificationError


class InMemoryFestivalRepository(ports.FestivalRepository):
    def __init__(self, *festivals):
        self._ids = count(1000)
        self.items = {}
        self.saved = 0
        for f in festivals:
            self.save(f)
        self.saved = 0

    def get(self, festival_id):
        f = self.items.get(festival_id)
        return copy.deepcopy(f) if f else None  # comme une vraie base : copie détachée

    def list(self):
        return [copy.deepcopy(f) for f in self.items.values()]

    def find_by_concert(self, concert_id):
        return next((self.get(f.id) for f in self.items.values() if f.concert(concert_id)), None)

    def save(self, festival):
        if festival.id is None:
            festival.id = next(self._ids)
        for c in festival.concerts:
            if c.id is None:
                c.id = next(self._ids)
            c.festival_id = festival.id
        stored = copy.deepcopy(festival)
        stored._events = []  # les événements ne sont pas persistés
        self.items[festival.id] = stored
        self.saved += 1


class _SimpleRepository:
    def __init__(self, *items):
        self._ids = count(1000)
        self.items = {}
        for i in items:
            self.add(i)

    def get(self, item_id):
        return self.items.get(item_id)

    def add(self, item):
        if item.id is None:
            item.id = next(self._ids)
        self.items[item.id] = item
        return item


class InMemoryStageRepository(_SimpleRepository, ports.StageRepository):
    def list_for_festival(self, festival_id):
        return [s for s in self.items.values() if s.festival_id == festival_id]


class InMemoryArtistRepository(_SimpleRepository, ports.ArtistRepository):
    def list(self):
        return list(self.items.values())

    def get_by_name(self, name):
        return next((a for a in self.items.values() if a.name == name), None)


class InMemoryIncidentRepository(_SimpleRepository, ports.IncidentRepository):
    def list(self, concert_id=None):
        return [i for i in self.items.values() if concert_id is None or i.concert_id == concert_id]


class FakeNotifier(ports.Notifier):
    def __init__(self, fail=False):
        self.fail = fail
        self.sent = []

    def notify(self, event):
        if self.fail:
            raise NotificationError("panne simulée")
        self.sent.append(event)
