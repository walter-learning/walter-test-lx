"""
À terme : mocks HTTP avec ``respx`` vérifiant 3 POST /channels/* avec Idempotency-Keys distinctes.

Pour l'état squelette : ``process_student`` doit encore lever ``NotImplementedError``.
"""

from walter_relance.orchestrator import process_student


def test_process_student_dispatches_to_three_channels_with_distinct_idempotency_keys():
    process_student("student-integration", "cpf-standard")
