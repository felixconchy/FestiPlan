class DomainError(Exception):
    """Une règle métier a été violée."""


class InvalidValue(DomainError):
    """Valeur métier invalide (créneau, capacité, description...)."""


class RuleViolation(DomainError):
    """Règle de programmation non respectée (R4, R5, R6)."""


class SchedulingConflict(DomainError):
    """Chevauchement sur une scène (R2) ou pour un artiste (R3)."""


class ScheduleLocked(DomainError):
    """Opération ordinaire refusée sur un planning publié (R7)."""


class InvalidTransition(DomainError):
    """Changement d'état non autorisé."""
