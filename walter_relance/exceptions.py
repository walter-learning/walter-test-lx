"""Errors raised by channel/LMS clients (symétriques aux codes HTTP du mock)."""


class ChannelError(Exception):
    """Réponse 5xx ou erreur applicative côté canal."""

    pass


class RateLimitError(ChannelError):
    """HTTP 429."""

    pass


class IdempotencyConflict(ChannelError):
    """HTTP 409 — même clé, corps différent."""

    pass


class LmsError(Exception):
    """Erreur LMS (4xx/5xx)."""

    pass
