"""
VC Analyst Agent – B2B enterprise VC analyst (10+ years).

Takes a research thesis → suggests structured attributes + qualitative heuristics
for search/filter. RAG-ready; fine-tuning can be added later.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Optional OpenAI
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

SYSTEM_PROMPT = """You are a senior VC analyst with 10+ years in venture capital, focused on B2B enterprise. You help translate research theses into concrete search criteria and qualitative heuristics.

Your role:
1. Interpret the user's research thesis (sector, stage, geography, logic).
2. Suggest structured attributes: company size, funding stage, target investors, geography, industry/vertical, exclusions.
3. Write short, actionable heuristics (2–4 sentences) that capture qualitative match logic—e.g. PLG motion, technical founders, early dev traction, category leadership potential. These will drive both scraper filters and AI ranking.

Be concise. Use standard terms: Seed, Series A, Series B, Series C; US, EU, etc. For investors, use well-known names (a16z, Sequoia, YC, etc.) or categories (e.g. "top-tier growth", "strategic angels") when specific names aren't given."""

USER_PROMPT_TEMPLATE = """Research thesis:

{thesis}

Respond with a single JSON object (no markdown, no code block) with exactly these keys:
- "suggested_attributes": {{
  "company_size": "e.g. 10–50 employees or $1M–$10M ARR",
  "funding_stage": ["Seed", "Series A", ...],
  "target_investors": "e.g. a16z, Sequoia, YC alumni",
  "geography": "e.g. US, US + EU",
  "industry_vertical": "e.g. Dev tools, vertical AI, fintech",
  "exclusions": "e.g. Consumer, crypto, hardware"
}}
- "heuristics": "2–4 sentences of qualitative match logic used for search/filter."
"""


def _get_client(api_key: Optional[str] = None) -> Optional[OpenAI]:
    if not OPENAI_AVAILABLE:
        return None
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key or not key.strip().startswith("sk-"):
        return None
    return OpenAI(api_key=key.strip())


def _extract_json(raw: str) -> Optional[Dict[str, Any]]:
    raw = raw.strip()
    # Strip markdown code blocks if present
    if "```" in raw:
        for marker in ("```json", "```"):
            if marker in raw:
                raw = raw.split(marker, 1)[-1].rsplit("```", 1)[0].strip()
                break
    # Try to find JSON object
    start = raw.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(raw)):
        if raw[i] == "{":
            depth += 1
        elif raw[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(raw[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def suggest_from_thesis(
    thesis: str,
    *,
    api_key: Optional[str] = None,
    model: str = "gpt-4o-mini",
) -> Dict[str, Any]:
    """
    Given a research thesis, return suggested attributes + heuristics.

    Returns:
        {
            "suggested_attributes": { ... },
            "heuristics": "...",
            "ok": True
        }
        or {"ok": False, "error": "..."}
    """
    if not thesis or not thesis.strip():
        return {"ok": False, "error": "Research thesis is required."}

    client = _get_client(api_key)
    if not client:
        return {"ok": False, "error": "OpenAI not available or API key missing. Set OPENAI_API_KEY or pass api_key."}

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(thesis=thesis.strip())},
            ],
            max_tokens=1000,
            temperature=0.3,
        )
        text = response.choices[0].message.content or ""
        data = _extract_json(text)
        if not data:
            return {"ok": False, "error": "Could not parse analyst response as JSON."}

        attrs = data.get("suggested_attributes")
        heuristics = data.get("heuristics")

        if not isinstance(attrs, dict):
            attrs = {}
        if not isinstance(heuristics, str):
            heuristics = ""

        # Normalize funding_stage to list
        if "funding_stage" in attrs and isinstance(attrs["funding_stage"], str):
            stages = [s.strip() for s in re.split(r"[,;]+", attrs["funding_stage"]) if s.strip()]
            attrs["funding_stage"] = stages if stages else ["Seed", "Series A", "Series B"]

        return {
            "ok": True,
            "suggested_attributes": attrs,
            "heuristics": heuristics.strip(),
        }
    except Exception as e:
        logger.exception("VC Analyst suggest_from_thesis failed")
        return {"ok": False, "error": str(e)}
