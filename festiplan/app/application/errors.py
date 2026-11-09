class NotFound(Exception):
    """Une ressource référencée n'existe pas."""


class AlreadyExists(Exception):
    """Une ressource portant le même identifiant métier existe déjà."""
