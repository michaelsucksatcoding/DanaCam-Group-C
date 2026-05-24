"""DanaCam simulation helpers.

This module contains pure functions used by API routes:
- Credit scoring simulation
- Late fee/penalty calculation

No external services; everything is deterministic and idempotent-compatible.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta



@dataclass(frozen=True)
class CreditScoringResult:
    score: int
    eligible: bool
    notes: str


def compute_credit_score(*, phone: str | None, ktp_number: str | None, amount: float) -> CreditScoringResult:
    """Simulate credit scoring (Stage 2 - Verifikasi & Analisis).

    Heuristic (deterministic):
    - phone present (digits >= 8) => +10
    - ktp present (>= 8 chars) => +20
    - amount bucket => lowers score for high amounts

    A deterministic pseudo "credit history" component is derived from the ktp_number
    last 2 digits.
    """

    phone_digits = "".join([c for c in (phone or "") if c.isdigit()])
    ktp = (ktp_number or "").strip()

    score = 0
    score += 10 if len(phone_digits) >= 8 else 0
    score += 20 if len(ktp) >= 8 else 0

    # pseudo credit history: last 2 digits mod 10 => [0..9]
    hist_component = 0
    if len(ktp) >= 2:
        last2 = ktp[-2:]
        if last2.isdigit():
            hist_component = int(last2) % 10
    score += hist_component  # +0..9

    # amount bucket risk adjustment
    # Higher amount => higher risk => lower score
    if amount <= 1_000_000:
        score += 20
    elif amount <= 5_000_000:
        score += 10
    elif amount <= 15_000_000:
        score += 0
    else:
        score -= 10

    # Clamp
    score = max(0, min(100, score))

    # Eligibility threshold
    eligible = score >= 75

    notes = (
        "Simulated scoring: phone+KTP heuristics with deterministic pseudo credit history; "
        "eligibility if score >= 75."
    )

    return CreditScoringResult(score=score, eligible=eligible, notes=notes)


def compute_late_fee_amount(
    *,
    principal: float,
    due_date: date,
    now: date,
    daily_rate: float = 0.01,
    max_fee_multiplier: float = 0.5,
) -> float:
    """Compute late fee for overdue loans.

    Late fee formula:
    late_days = (now - due_date).days (>=0)
    fee = principal * daily_rate * late_days
    fee capped at principal * max_fee_multiplier

    This function returns the full late fee that *should* apply as of `now`.
    Idempotency is handled by the API using `last_late_fee_applied_at`.
    """

    late_days = (now - due_date).days
    if late_days <= 0:
        return 0.0

    fee = principal * daily_rate * late_days
    cap = principal * max_fee_multiplier
    return float(min(fee, cap))


def compute_total_payable(principal: float, term_months: int) -> float:
    """Simple total payable calculation used in Stage 3.

    We apply a flat simulated monthly interest rate of 2%.
    total_payable = principal * (1 + 0.02 * term_months)
    """

    monthly_rate = 0.02
    return float(principal * (1.0 + monthly_rate * float(term_months)))


def compute_due_date(*, approved_at: datetime, term_months: int) -> date:
    """Compute due date as approved_at + term_months months (approx 30 days/month)."""

    days = int(term_months) * 30
    return approved_at.date() + timedelta(days=days)



