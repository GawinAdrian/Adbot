"""Campaign briefing gate: the user confirms goal, budget, region, and conversion before any draft.

The assistant records the briefing here.  An unconfirmed or incomplete briefing is refused, so that
no campaign draft is built on guessed goals or budgets.  :func:`briefing_to_campaign` turns a
confirmed briefing plus keywords and ads into a Google Ads Editor draft that is always paused.
Nothing in this module talks to Google or writes to an account.
"""
from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence

from .editor_export import (
    EditorAdGroup,
    EditorCampaign,
    EditorKeyword,
    EditorNegativeKeyword,
    EditorResponsiveSearchAd,
)

BRIEFING_FIELDS: tuple[str, ...] = (
    "goal", "goal_kind", "daily_budget", "currency", "region", "conversion_definition",
    "offer", "website", "language", "confirmed_by_user", "confirmation_quote", "confirmed_at",
)
GOAL_KINDS = ("calls", "leads", "sales")
# Editor names for language and country; the Editor maps location text to targets on import,
# so the user checks the mapping preview (docs/runbooks/editor-csv-import.md).
EDITOR_MARKETS: dict[str, dict[str, tuple[str, ...]]] = {
    "de": {"languages": ("German",), "locations": ("Germany",)},
    "pl": {"languages": ("Polish",), "locations": ("Poland",)},
}


class BriefingError(ValueError):
    """Raised when a briefing is incomplete, unconfirmed, or inconsistent."""


def _nonempty(document: Mapping[str, Any], key: str) -> str:
    value = document[key]
    if not isinstance(value, str) or not value.strip():
        raise BriefingError(f"{key} must be a non-empty string")
    return value.strip()


def validate_briefing(document: Any, *, account_currency: str | None = None) -> dict[str, Any]:
    """Validate a confirmed campaign briefing and return a normalized copy.

    ``confirmation_quote`` holds the user's own words of approval (not a model summary).  When the
    account's currency is known, the briefing currency must match it: the Editor CSV carries no
    currency, so a mismatch would silently change what the budget means.
    """
    if not isinstance(document, Mapping):
        raise BriefingError("briefing must be an object")
    missing = [key for key in BRIEFING_FIELDS if key not in document]
    extra = sorted(set(document) - set(BRIEFING_FIELDS))
    if missing:
        raise BriefingError("briefing is missing: " + ", ".join(missing))
    if extra:
        raise BriefingError("briefing has unsupported field(s): " + ", ".join(extra))
    if document["confirmed_by_user"] is not True:
        raise BriefingError("briefing must be confirmed by the user before a draft is built")
    quote = document["confirmation_quote"]
    if not isinstance(quote, str) or len(quote.strip()) < 2:
        raise BriefingError("confirmation_quote must contain the user's own words of approval")
    try:
        datetime.fromisoformat(str(document["confirmed_at"]).replace("Z", "+00:00"))
    except ValueError as exc:
        raise BriefingError("confirmed_at must be an ISO 8601 timestamp") from exc
    clean: dict[str, Any] = {key: _nonempty(document, key) for key in
                             ("goal", "region", "conversion_definition", "offer", "website")}
    if document["goal_kind"] not in GOAL_KINDS:
        raise BriefingError(f"goal_kind must be one of: {', '.join(GOAL_KINDS)}")
    if document["language"] not in EDITOR_MARKETS:
        raise BriefingError("language must be 'de' or 'pl'")
    if not isinstance(document["currency"], str) or not re.fullmatch(r"[A-Z]{3}", document["currency"]):
        raise BriefingError("currency must be a three-letter ISO code")
    if account_currency is not None and document["currency"] != account_currency:
        raise BriefingError(f"briefing currency {document['currency']} differs from the account currency {account_currency}")
    try:
        budget = Decimal(str(document["daily_budget"]))
    except InvalidOperation as exc:
        raise BriefingError("daily_budget must be a number") from exc
    if not budget.is_finite() or budget <= 0:
        raise BriefingError("daily_budget must be greater than zero")
    if not re.fullmatch(r"https://[^\s/]+(/\S*)?", clean["website"]):
        raise BriefingError("website must be an https URL")
    clean.update(
        goal_kind=document["goal_kind"], language=document["language"], currency=document["currency"], confirmation_quote=quote.strip(),
        daily_budget=format(budget.quantize(Decimal("0.01")), "f"), confirmed_by_user=True,
        confirmed_at=str(document["confirmed_at"]),
    )
    return clean


def briefing_to_campaign(
    briefing: Mapping[str, Any],
    *,
    campaign_name: str,
    ad_group_name: str,
    keywords: Sequence[EditorKeyword],
    ads: Sequence[EditorResponsiveSearchAd],
    negatives: Sequence[EditorNegativeKeyword] = (),
    bid_strategy_type: str = "Maximize clicks",
    account_currency: str | None = None,
) -> EditorCampaign:
    """Build a paused Search campaign draft from a confirmed briefing (validated again here)."""
    checked = validate_briefing(briefing, account_currency=account_currency)
    market = EDITOR_MARKETS[checked["language"]]
    return EditorCampaign(
        name=campaign_name,
        daily_budget=checked["daily_budget"],
        ad_groups=(EditorAdGroup(name=ad_group_name, keywords=tuple(keywords), ads=tuple(ads)),),
        bid_strategy_type=bid_strategy_type,
        languages=market["languages"],
        locations=market["locations"],
        status="Paused",
        negative_keywords=tuple(negatives),
    )
