"""Message catalogs and locale formatting for Adbot (German, Polish, English).

Design rules:

* English is the reference catalog and the output of every existing renderer; German and
  Polish must define exactly the same keys with the same ``{placeholders}`` (tested).
* A missing key in ``de``/``pl`` never falls back silently: the English text is returned
  with a visible ``[en]`` marker and the key is recorded in :attr:`Translator.missing`.
* Enum values (status, severity, ...) are translated through ``enum.<kind>.<value>`` keys;
  without such a key the legacy English formatting (``replace('_', ' ').title()``) applies.
* No third-party dependency: number, percent, money and date formats are implemented here.
"""
from __future__ import annotations

import importlib
import re
from datetime import date
from functools import lru_cache
from typing import Any

SUPPORTED_LANGUAGES: tuple[str, ...] = ("de", "pl", "en")
DEFAULT_LANGUAGE = "en"
MISSING_MARKER = "[en] "
_NBSP = " "
_PLACEHOLDER = re.compile(r"\{([a-z_][a-z0-9_]*)\}")
_CURRENCY_SYMBOLS = {"EUR": "€", "PLN": "zł", "USD": "$", "GBP": "£", "CHF": "CHF"}


class I18nError(ValueError):
    """Raised for unsupported languages, malformed catalogs, or unknown keys."""


def _module(language: str):
    if language not in SUPPORTED_LANGUAGES:
        raise I18nError(f"unsupported language {language!r}; expected one of: {', '.join(SUPPORTED_LANGUAGES)}")
    return importlib.import_module(f"{__name__}.catalog_{language}")


@lru_cache(maxsize=None)
def load_catalog(language: str) -> dict[str, str]:
    """Return the flat message catalog for *language* (without the ``META`` block)."""
    messages = getattr(_module(language), "MESSAGES", None)
    if not isinstance(messages, dict):
        raise I18nError(f"catalog for {language!r} must define a MESSAGES dict")
    bad = [k for k, v in messages.items() if not isinstance(v, str)]
    if bad:
        raise I18nError(f"catalog {language!r} has non-string values for: {', '.join(sorted(bad)[:5])}")
    return dict(messages)


def catalog_meta(language: str) -> dict[str, Any]:
    """Return the ``META`` block (language, review status) of a catalog."""
    meta = getattr(_module(language), "META", {})
    return dict(meta) if isinstance(meta, dict) else {}


def glossary() -> dict[str, Any]:
    """Return ``{"meta": ..., "terms": [...]}`` for the Google Ads glossary."""
    from . import glossary_data

    return {"meta": dict(glossary_data.META), "terms": [dict(term) for term in glossary_data.TERMS]}


def placeholders(message: str) -> frozenset[str]:
    """Return the set of ``{name}`` placeholders used in *message*."""
    return frozenset(_PLACEHOLDER.findall(message))


def normalize_language(value: str | None) -> str:
    """Map ``None``, ``de-DE``, ``PL`` and similar to a supported language code."""
    if not value:
        return DEFAULT_LANGUAGE
    code = value.strip().lower().replace("_", "-").split("-")[0]
    if code not in SUPPORTED_LANGUAGES:
        raise I18nError(f"unsupported language {value!r}; expected one of: {', '.join(SUPPORTED_LANGUAGES)}")
    return code


class Translator:
    """Look up messages and format values for one language."""

    def __init__(self, language: str | None = DEFAULT_LANGUAGE) -> None:
        self.language = normalize_language(language)
        self._messages = load_catalog(self.language)
        self._reference = load_catalog(DEFAULT_LANGUAGE)
        self.missing: list[str] = []

    # ------------------------------------------------------------------ messages
    def t(self, key: str, **params: object) -> str:
        """Return the message for *key*, formatted with *params*."""
        if key in self._messages:
            message = self._messages[key]
        elif key in self._reference:
            self.missing.append(key)
            message = MISSING_MARKER + self._reference[key]
        else:
            raise I18nError(f"unknown message key {key!r}")
        missing = placeholders(message) - set(params)
        if missing:
            raise I18nError(f"message {key!r} needs parameter(s): {', '.join(sorted(missing))}")
        return _PLACEHOLDER.sub(lambda m: str(params[m.group(1)]), message) if params else message

    def has(self, key: str) -> bool:
        """Return True when this language's catalog defines *key*."""
        return key in self._messages

    def label(self, kind: str, value: object) -> str:
        """Translate an enum *value* of *kind*; legacy English title case as fallback."""
        text = str(value)
        key = f"enum.{kind}.{text}"
        if key in self._messages:
            return self._messages[key]
        if self.language != DEFAULT_LANGUAGE and key in self._reference:
            self.missing.append(key)
            return MISSING_MARKER + self._reference[key]
        return text.replace("_", " ").title()

    def draft_notice(self) -> str | None:
        """Visible hint when this language's catalog has not been reviewed by a native speaker."""
        if catalog_meta(self.language).get("review_status") == "entwurf":
            return self.t("common.draft_notice")
        return None

    # ------------------------------------------------------------------ numbers
    def number(self, value: float, decimals: int = 2) -> str:
        """Format *value* with the language's decimal and thousands separators."""
        sign = "-" if value < 0 else ""
        text = f"{abs(float(value)):,.{decimals}f}"
        if self.language == "de":
            text = text.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
        elif self.language == "pl":
            text = text.replace(",", _NBSP).replace(".", ",")
        return sign + text

    def percent(self, value: float, decimals: int = 2) -> str:
        """Format a percentage that is already expressed in percent (12.5 -> 12.5%)."""
        text = self.number(value, decimals)
        return f"{text}{_NBSP}%" if self.language == "de" else f"{text}%"

    def score(self, value: float | None) -> str:
        """Format a 0-100 score, or the localized 'not scored' text."""
        if value is None:
            return self.t("report.not_scored")
        return f"{self.number(value, 2)} / 100"

    def money(self, amount: float, currency: str) -> str:
        """Format a money amount, e.g. ``1.234,56 €`` (de), ``1 234,56 zł`` (pl), ``€1,234.56`` (en)."""
        if not re.fullmatch(r"[A-Z]{3}", currency):
            raise I18nError(f"currency must be a three-letter ISO code, got {currency!r}")
        symbol = _CURRENCY_SYMBOLS.get(currency, currency)
        number = self.number(amount, 2)
        if self.language == "en":
            sign, digits = ("-", number[1:]) if number.startswith("-") else ("", number)
            return f"{sign}{symbol}{digits}" if currency in _CURRENCY_SYMBOLS else f"{sign}{currency} {digits}"
        return f"{number}{_NBSP}{symbol}"

    def date(self, value: str | date) -> str:
        """Format an ISO date (``2026-11-01``) as ``01.11.2026`` (de/pl) or unchanged (en)."""
        parsed = value if isinstance(value, date) else date.fromisoformat(str(value))
        if self.language == "en":
            return parsed.isoformat()
        return f"{parsed.day:02d}.{parsed.month:02d}.{parsed.year:04d}"
