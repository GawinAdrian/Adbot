"""Draft-write: render an approved campaign draft as a Google Ads Editor import CSV.

This is the only write-shaped capability in the Google surface and it never
touches an account.  It produces a file that an operator imports into Google
Ads Editor, reviews, and posts manually.  Every campaign is emitted ``Paused``
so nothing can serve before a human enables it.  Column headers follow the
official Google Ads Editor CSV column documentation (source ID
``google-ads-editor-csv-columns-official``); the writer fails closed on any
value that would be ambiguous or unsafe for import.
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from os import PathLike
from pathlib import Path
from typing import Iterable, Sequence

EDITOR_CSV_SOURCE_ID = "google-ads-editor-csv-columns-official"
MATCH_TYPES = ("Broad", "Phrase", "Exact")
# Google Ads Editor marks campaign-level negatives with the Type/Match type value
# "Campaign negative"; the match form is carried by the keyword text convention
# (plain = broad, "quoted" = phrase, [bracketed] = exact). Source ID:
# google-ads-editor-csv-columns-official (claim CLM-0212).
CAMPAIGN_NEGATIVE_TYPE = "Campaign negative"
ITEM_STATUSES = ("Enabled", "Paused")
CAMPAIGN_TYPES = ("Search",)
BID_STRATEGY_TYPES = (
    "Manual CPC",
    "Maximize clicks",
    "Maximize conversions",
    "Maximize conversion value",
    "Target CPA",
    "Target ROAS",
    "Target impression share",
)
HEADLINE_SLOTS = 15
DESCRIPTION_SLOTS = 4

COLUMNS: tuple[str, ...] = (
    "Campaign",
    "Campaign daily budget",
    "Campaign status",
    "Campaign type",
    "Bid strategy type",
    "Networks",
    "Languages",
    "Location",
    "Ad group",
    "Ad group status",
    "Max CPC",
    "Keyword",
    "Match type",
    "Status",
    "Final URL",
    *(f"Headline {index}" for index in range(1, HEADLINE_SLOTS + 1)),
    *(f"Description {index}" for index in range(1, DESCRIPTION_SLOTS + 1)),
    "Path 1",
    "Path 2",
)


class EditorExportError(ValueError):
    """Raised when a draft cannot be rendered safely for Google Ads Editor."""


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EditorExportError(f"{label} must be a non-empty string")
    if any(ch in value for ch in "\r\n\t"):
        raise EditorExportError(f"{label} must not contain line breaks or tabs")
    return value.strip()


def _money(value: str | Decimal, label: str) -> str:
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise EditorExportError(f"{label} must be a decimal amount") from exc
    if not amount.is_finite() or amount <= 0:
        raise EditorExportError(f"{label} must be a positive finite amount")
    return f"{amount.quantize(Decimal('0.01'))}"


def _https(value: str, label: str) -> str:
    url = _text(value, label)
    if not url.startswith("https://"):
        raise EditorExportError(f"{label} must be an https URL")
    return url


@dataclass(frozen=True)
class EditorKeyword:
    text: str
    match_type: str
    status: str = "Enabled"
    final_url: str | None = None


@dataclass(frozen=True)
class EditorNegativeKeyword:
    """A campaign-level negative keyword that must cite its search-term evidence.

    ``evidence_ref`` names the search terms report, form-submission review, or
    other evidence that justified the exclusion (skills/ads-google boundary:
    no negatives without evidence and an overblocking check).
    """

    text: str
    match_type: str
    evidence_ref: str


@dataclass(frozen=True)
class EditorResponsiveSearchAd:
    headlines: Sequence[str]
    descriptions: Sequence[str]
    final_url: str
    path1: str | None = None
    path2: str | None = None
    status: str = "Enabled"


@dataclass(frozen=True)
class EditorAdGroup:
    name: str
    keywords: Sequence[EditorKeyword]
    ads: Sequence[EditorResponsiveSearchAd]
    status: str = "Enabled"
    max_cpc: str | Decimal | None = None


@dataclass(frozen=True)
class EditorCampaign:
    name: str
    daily_budget: str | Decimal
    ad_groups: Sequence[EditorAdGroup]
    bid_strategy_type: str
    languages: Sequence[str]
    locations: Sequence[str]
    campaign_type: str = "Search"
    networks: Sequence[str] = field(default_factory=lambda: ("Google Search",))
    status: str = "Paused"
    negative_keywords: Sequence[EditorNegativeKeyword] = ()


def _blank_row() -> dict[str, str]:
    return {column: "" for column in COLUMNS}


def _negative_text(text: str, match_type: str) -> str:
    """Render a negative keyword in Editor text convention for its match type."""
    if match_type == "Phrase":
        return f'"{text}"'
    if match_type == "Exact":
        return f"[{text}]"
    return text


def build_editor_rows(campaigns: Iterable[EditorCampaign]) -> list[dict[str, str]]:
    """Validate a draft and return Editor rows (one dict per CSV line)."""
    rows: list[dict[str, str]] = []
    campaign_names: set[str] = set()
    for campaign in campaigns:
        name = _text(campaign.name, "campaign.name")
        if name in campaign_names:
            raise EditorExportError(f"duplicate campaign name {name!r}")
        campaign_names.add(name)
        if campaign.status != "Paused":
            raise EditorExportError("draft campaigns must be exported Paused; enable them in Google Ads Editor after review")
        if campaign.campaign_type not in CAMPAIGN_TYPES:
            raise EditorExportError(f"campaign.type must be one of {', '.join(CAMPAIGN_TYPES)}")
        if campaign.bid_strategy_type not in BID_STRATEGY_TYPES:
            raise EditorExportError(f"campaign.bid_strategy_type must be one of {', '.join(BID_STRATEGY_TYPES)}")
        if not campaign.languages or not campaign.locations:
            raise EditorExportError(f"campaign {name!r} needs at least one language and one location")
        if not campaign.ad_groups:
            raise EditorExportError(f"campaign {name!r} needs at least one ad group")
        base = _blank_row()
        base.update(
            {
                "Campaign": name,
                "Campaign daily budget": _money(campaign.daily_budget, "campaign.daily_budget"),
                "Campaign status": "Paused",
                "Campaign type": campaign.campaign_type,
                "Bid strategy type": campaign.bid_strategy_type,
                "Networks": "; ".join(_text(n, "campaign.networks") for n in campaign.networks),
                "Languages": "; ".join(_text(l, "campaign.languages") for l in campaign.languages),
                "Location": "; ".join(_text(l, "campaign.locations") for l in campaign.locations),
            }
        )
        rows.append(base)
        seen_negatives: set[tuple[str, str]] = set()
        for negative in campaign.negative_keywords:
            neg_text = _text(negative.text, "negative_keyword.text")
            if any(ch in neg_text for ch in '"[]'):
                raise EditorExportError(f"negative keyword {neg_text!r} must be plain text; match type sets the notation")
            if negative.match_type not in MATCH_TYPES:
                raise EditorExportError(f"negative keyword {neg_text!r}: match_type must be one of {', '.join(MATCH_TYPES)}")
            if not isinstance(negative.evidence_ref, str) or not negative.evidence_ref.strip():
                raise EditorExportError(
                    f"negative keyword {neg_text!r} has no evidence_ref; negatives require a search terms report or equivalent evidence"
                )
            neg_key = (neg_text.lower(), negative.match_type)
            if neg_key in seen_negatives:
                raise EditorExportError(f"duplicate negative keyword {neg_text!r} ({negative.match_type}) in campaign {name!r}")
            seen_negatives.add(neg_key)
            negative_row = _blank_row()
            negative_row.update(
                {
                    "Campaign": name,
                    "Keyword": _negative_text(neg_text, negative.match_type),
                    "Match type": CAMPAIGN_NEGATIVE_TYPE,
                    "Status": "Enabled",
                }
            )
            rows.append(negative_row)
        group_names: set[str] = set()
        for group in campaign.ad_groups:
            group_name = _text(group.name, "ad_group.name")
            if group_name in group_names:
                raise EditorExportError(f"duplicate ad group {group_name!r} in campaign {name!r}")
            group_names.add(group_name)
            if group.status not in ITEM_STATUSES:
                raise EditorExportError("ad_group.status must be Enabled or Paused")
            if not group.keywords or not group.ads:
                raise EditorExportError(f"ad group {group_name!r} needs keywords and at least one ad")
            group_row = _blank_row()
            group_row.update(
                {
                    "Campaign": name,
                    "Ad group": group_name,
                    "Ad group status": group.status,
                    "Max CPC": _money(group.max_cpc, "ad_group.max_cpc") if group.max_cpc is not None else "",
                }
            )
            rows.append(group_row)
            seen_keywords: set[tuple[str, str]] = set()
            for keyword in group.keywords:
                text = _text(keyword.text, "keyword.text")
                if keyword.match_type not in MATCH_TYPES:
                    raise EditorExportError(
                        f"keyword {text!r}: match_type must be one of {', '.join(MATCH_TYPES)}; use EditorCampaign.negative_keywords for exclusions"
                    )
                if keyword.status not in ITEM_STATUSES:
                    raise EditorExportError(f"keyword {text!r}: status must be Enabled or Paused")
                key = (text.lower(), keyword.match_type)
                if key in seen_keywords:
                    raise EditorExportError(f"duplicate keyword {text!r} ({keyword.match_type}) in {group_name!r}")
                seen_keywords.add(key)
                keyword_row = _blank_row()
                keyword_row.update(
                    {
                        "Campaign": name,
                        "Ad group": group_name,
                        "Keyword": text,
                        "Match type": keyword.match_type,
                        "Status": keyword.status,
                        "Final URL": _https(keyword.final_url, "keyword.final_url") if keyword.final_url else "",
                    }
                )
                rows.append(keyword_row)
            for index, ad in enumerate(group.ads, start=1):
                label = f"{group_name} ad {index}"
                headlines = [_text(h, f"{label} headline") for h in ad.headlines]
                descriptions = [_text(d, f"{label} description") for d in ad.descriptions]
                if not headlines or not descriptions:
                    raise EditorExportError(f"{label} needs headlines and descriptions")
                if len(headlines) > HEADLINE_SLOTS or len(descriptions) > DESCRIPTION_SLOTS:
                    raise EditorExportError(
                        f"{label} exceeds the Editor column set ({HEADLINE_SLOTS} headlines, {DESCRIPTION_SLOTS} descriptions)"
                    )
                if len(set(headlines)) != len(headlines) or len(set(descriptions)) != len(descriptions):
                    raise EditorExportError(f"{label} repeats a headline or description")
                if ad.status not in ITEM_STATUSES:
                    raise EditorExportError(f"{label}: status must be Enabled or Paused")
                ad_row = _blank_row()
                ad_row.update(
                    {
                        "Campaign": name,
                        "Ad group": group_name,
                        "Status": ad.status,
                        "Final URL": _https(ad.final_url, f"{label} final_url"),
                        "Path 1": _text(ad.path1, f"{label} path1") if ad.path1 else "",
                        "Path 2": _text(ad.path2, f"{label} path2") if ad.path2 else "",
                    }
                )
                for slot, headline in enumerate(headlines, start=1):
                    ad_row[f"Headline {slot}"] = headline
                for slot, description in enumerate(descriptions, start=1):
                    ad_row[f"Description {slot}"] = description
                rows.append(ad_row)
    if not rows:
        raise EditorExportError("draft contains no campaigns")
    return rows


def render_editor_csv(campaigns: Iterable[EditorCampaign]) -> str:
    """Return the CSV text (UTF-8 BOM added at write time)."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS, lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(build_editor_rows(campaigns))
    return buffer.getvalue()


def write_editor_csv(campaigns: Iterable[EditorCampaign], destination: str | PathLike[str]) -> Path:
    """Write the draft CSV with a UTF-8 BOM so Google Ads Editor reads umlauts correctly."""
    path = Path(destination)
    if path.suffix.lower() != ".csv":
        raise EditorExportError("destination must end with .csv")
    if path.exists() or path.is_symlink():
        raise EditorExportError(f"refusing to overwrite existing draft: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    text = render_editor_csv(campaigns)
    path.write_text(text, encoding="utf-8-sig", newline="")
    return path
