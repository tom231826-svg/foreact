"""AI layer: turn messy field notes into structured assumptions, and write the
plain-language decision brief — the operational work around the transparent
scoring formula.

Both functions are optional and degrade safely: with no LLM backend (or on any
error) `enrich_communities` returns the communities unchanged and
`generate_brief_narrative` returns None, so the deterministic scorer and the
template brief run exactly as before (do-no-harm, offline-capable). Every
AI-derived change is bounded, logged and surfaced for human review.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import llm
from .community import Community


@dataclass(frozen=True)
class NoteSignal:
    community_id: str
    summary: str
    access_override: Optional[float]
    health_facility_override: Optional[bool]
    flags: List[str]
    source: str  # "llm:<provider>"


def load_notes(path) -> Dict[str, str]:
    """Load free-text field notes keyed by community id (JSON: {id: text})."""
    if not path:
        return {}
    path = Path(path)
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: field notes must be a JSON object of community_id -> note text")
    return {str(k): str(v) for k, v in data.items() if not str(k).startswith("_")}


def enrich_communities(
    communities: List[Community],
    notes_by_id: Dict[str, str],
    use_llm: bool = False,
) -> Tuple[List[Community], Dict[str, NoteSignal]]:
    """Apply LLM-extracted note signals to community inputs before ranking.

    Returns (possibly-adjusted communities, signals by community id). If the LLM
    is off/unavailable or a note can't be parsed, that community is left exactly
    as-is — the formula still runs on the original, reviewable data.
    """
    if not use_llm or not notes_by_id or not llm.available():
        return list(communities), {}

    adjusted: List[Community] = []
    signals: Dict[str, NoteSignal] = {}
    for community in communities:
        note = notes_by_id.get(community.id, "").strip()
        if not note:
            adjusted.append(community)
            continue
        try:
            signal = _extract_signal(community, note)
        except (llm.LLMError, ValueError):
            adjusted.append(community)  # fallback: keep the original, unmodified
            continue
        signals[community.id] = signal
        adjusted.append(_apply_signal(community, signal))
    return adjusted, signals


def _extract_signal(community: Community, note: str) -> NoteSignal:
    system = (
        "You convert a short free-text disaster field note about one community into "
        "structured planning assumptions. Output ONLY a JSON object with keys: "
        "summary (one plain sentence), access_score (0=easy reach .. 1=very hard, or null "
        "if the note says nothing about access/roads), health_facility (true/false if the "
        "note clearly states a clinic is open/closed, else null), flags (short string list). "
        "Use ONLY what the note says; never invent damage, numbers or causes. No commentary."
    )
    user = f"Community: {community.name} ({community.division}). Field note: {note}"
    raw = llm.generate(system, user, max_tokens=250)
    data = _extract_json(raw)

    access = data.get("access_score")
    access = float(access) if isinstance(access, (int, float)) else None
    if access is not None:
        access = max(0.0, min(1.0, access))
    health = data.get("health_facility")
    health = bool(health) if isinstance(health, bool) else None
    flags = [str(f) for f in data.get("flags", []) if str(f).strip()][:6]
    summary = str(data.get("summary", "")).strip()[:200] or note[:200]
    return NoteSignal(
        community_id=community.id,
        summary=summary,
        access_override=access,
        health_facility_override=health,
        flags=flags,
        source="llm:" + llm.active_provider(),
    )


def _apply_signal(community: Community, signal: NoteSignal) -> Community:
    changes = {}
    # Conservative do-no-harm rule: AI-extracted field notes can escalate
    # planning risk automatically, but cannot de-escalate a community or mark a
    # closed/missing facility as available without human review.
    if signal.access_override is not None and signal.access_override > community.access_score:
        changes["access_score"] = signal.access_override
    if signal.health_facility_override is False:
        changes["health_facility"] = False
    return replace(community, **changes) if changes else community


def generate_brief_narrative(ranked, event, config, use_llm: bool = False) -> Optional[str]:
    """Write a short plain-language executive summary from the structured ranking.

    Returns None if the LLM is off/unavailable or on any error — the brief then
    renders from the deterministic template only.
    """
    if not use_llm or not ranked or not llm.available():
        return None
    facts = _ranking_facts(ranked, event, config)
    system = (
        f"You are writing a brief executive summary for {config.country}'s disaster and "
        "health authorities, from an anticipatory-action ranking. Use ONLY the facts "
        "provided — do not invent numbers, places or causes. 4-6 sentences, plain and "
        "direct, for decision-makers acting before impact. State clearly that this is "
        "advisory decision support requiring human review. No headings, no bullet list."
    )
    try:
        return llm.generate(system, facts, max_tokens=400)
    except llm.LLMError:
        return None


def _ranking_facts(ranked, event, config) -> str:
    lines = [
        f"Hazard: {event.hazard}; official trigger active: {event.official_trigger}; "
        f"confidence: {event.confidence:.2f}.",
        f"Top {min(len(ranked), 5)} ranked communities:",
    ]
    for item in ranked[:5]:
        actions = ", ".join(f"{a.units} {a.name}" for a in item.actions) or "monitor only"
        lines.append(
            f"- {item.community.name} ({item.community.division}), priority {item.priority}, "
            f"~{item.exposed_people} people exposed; reasons: {'; '.join(item.reasons)}; "
            f"actions: {actions}."
        )
    return "\n".join(lines)


def _extract_json(raw: str) -> dict:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("no JSON object in LLM response")
    return json.loads(match.group(0))
