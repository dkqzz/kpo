"""Read models assembled for presentation without exposing storage details."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class EvaluationView:
    student_id: str
    criterion_id: str
    criterion_name: str
    score: Decimal
    max_score: Decimal
    comment: str
