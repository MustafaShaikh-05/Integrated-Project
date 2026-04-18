"""
Agentic insurance workflow without CrewAI/LangChain.

Three separate Groq calls model distinct “agents”: plans JSON, hospitals JSON,
and a comparison write-up split into comparison + one-line recommendation.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

GROQ_MODEL = "llama-3.1-8b-instant"

FALLBACK_PLANS: list[dict[str, Any]] = [
    {
        "name": "Star Health",
        "premium": "₹4,500/yr",
        "coverage": "₹5 Lakh",
        "benefits": ["Cashless treatment", "9000+ hospitals", "No claim bonus"],
        "recommended": False,
    },
    {
        "name": "HDFC ERGO",
        "premium": "₹5,200/yr",
        "coverage": "₹7 Lakh",
        "benefits": ["Cashless treatment", "10000+ hospitals", "Free health checkup"],
        "recommended": True,
    },
    {
        "name": "Niva Bupa",
        "premium": "₹3,800/yr",
        "coverage": "₹3 Lakh",
        "benefits": ["Cashless treatment", "6000+ hospitals", "Daily cash benefit"],
        "recommended": False,
    },
]

FALLBACK_HOSPITALS: list[dict[str, Any]] = [
    {
        "name": "Apollo Hospitals",
        "rating": 4.6,
        "distance_km": 2.4,
        "cashless": True,
        "beds": 450,
        "speciality": "Multi-speciality",
    },
    {
        "name": "Fortis Healthcare",
        "rating": 4.4,
        "distance_km": 5.1,
        "cashless": True,
        "beds": 320,
        "speciality": "Cardiac & oncology",
    },
    {
        "name": "Max Super Speciality",
        "rating": 4.7,
        "distance_km": 7.8,
        "cashless": False,
        "beds": 280,
        "speciality": "Orthopaedics & neurology",
    },
]


def _get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set. Add it to your .env file.")
    return Groq(api_key=api_key)


def _groq_text(system: str, user: str) -> str:
    client = _get_groq_client()
    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.4,
    )
    return (completion.choices[0].message.content or "").strip()


def _extract_json_array(text: str) -> Any | None:
    """Try to parse a JSON array from model output, tolerating markdown fences."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    # Sometimes the model wraps extra prose; attempt to locate first [...] block.
    start, end = text.find("["), text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            data = json.loads(text[start : end + 1])
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            return None
    return None


def _normalize_plans(raw: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in raw[:3]:
        if not isinstance(item, dict):
            continue
        benefits = item.get("benefits") or []
        if isinstance(benefits, str):
            benefits = [benefits]
        out.append(
            {
                "name": str(item.get("name", "Plan")),
                "premium": str(item.get("premium", "—")),
                "coverage": str(item.get("coverage", "—")),
                "benefits": [str(b) for b in benefits][:3],
                "recommended": bool(item.get("recommended", False)),
            }
        )
    return out


def _normalize_hospitals(raw: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in raw[:3]:
        if not isinstance(item, dict):
            continue
        out.append(
            {
                "name": str(item.get("name", "Hospital")),
                "rating": float(item.get("rating", 4.0)),
                "distance_km": float(item.get("distance_km", 0.0)),
                "cashless": bool(item.get("cashless", False)),
                "beds": int(item.get("beds", 100)),
                "speciality": str(item.get("speciality", "General")),
            }
        )
    return out


def _parse_comparison_and_recommendation(text: str) -> tuple[str, str]:
    """
    Split Agent 3 output into comparison body and a one-line recommendation.

    Expects optional markers; falls back to heuristics if absent.
    """
    t = text.strip()
    if "RECOMMENDATION:" in t.upper():
        parts = re.split(r"(?i)RECOMMENDATION:\s*", t, maxsplit=1)
        comparison = parts[0].replace("COMPARISON:", "").strip()
        recommendation = parts[1].strip().splitlines()[0] if len(parts) > 1 else ""
        return comparison or t, recommendation or "See comparison above."
    lines = [ln.strip() for ln in t.splitlines() if ln.strip()]
    if len(lines) >= 2:
        return "\n\n".join(lines[:-1]), lines[-1]
    return t, "Review the comparison and pick the plan that fits your priorities."


def run_insurance_agents(
    age: int,
    city: str,
    budget: int,
    insurance_type: str,
) -> dict[str, Any]:
    """
    Run three Groq-backed steps and return structured UI payload.

    On JSON parse failure for plans or hospitals, deterministic fallbacks are used
    so demos never break.
    """
    # --- Agent 1: Insurance Finder ---
    agent1_user = (
        f"You are an insurance advisor. Suggest 3 realistic {insurance_type} "
        f"insurance plans in India for a {age} year old with budget "
        f"₹{budget}/year in {city}. "
        "Return ONLY a JSON array with exactly 3 objects, each having: "
        "name, premium, coverage, benefits (list of 3 strings), "
        "recommended (true for best one only). "
        "No explanation, only valid JSON."
    )
    plans: list[dict[str, Any]]
    try:
        raw_plans = _extract_json_array(_groq_text("You output only JSON.", agent1_user))
        if not raw_plans:
            raise ValueError("empty plans")
        plans = _normalize_plans(raw_plans)
        if len(plans) < 3:
            raise ValueError("not enough plans")
        if not any(p.get("recommended") for p in plans):
            plans[0]["recommended"] = True
    except Exception:
        plans = [dict(p) for p in FALLBACK_PLANS]

    plans_json = json.dumps(plans, ensure_ascii=False)

    # --- Agent 2: Hospital Finder ---
    agent2_user = (
        f"Generate 3 realistic hospitals in {city}, India. "
        "Return ONLY a JSON array with exactly 3 objects, each having: "
        "name, rating (float between 3.5 to 5.0), distance_km (float), "
        "cashless (true/false), beds (integer), speciality (string). "
        "Make them sound like real hospitals with real Indian names. "
        "No explanation, only valid JSON."
    )
    hospitals: list[dict[str, Any]]
    try:
        raw_h = _extract_json_array(_groq_text("You output only JSON.", agent2_user))
        if not raw_h:
            raise ValueError("empty hospitals")
        hospitals = _normalize_hospitals(raw_h)
        if len(hospitals) < 3:
            raise ValueError("not enough hospitals")
    except Exception:
        hospitals = [dict(h) for h in FALLBACK_HOSPITALS]

    # --- Agent 3: Comparison ---
    agent3_user = (
        "You are an insurance comparison expert. Compare these 3 plans:\n"
        f"{plans_json}\n"
        "Give a 2 paragraph comparison and a clear recommendation of which plan "
        "is best and why. Be specific.\n"
        "Format EXACTLY like this (including labels on their own lines):\n"
        "COMPARISON:\n"
        "<two paragraphs here>\n"
        "RECOMMENDATION:\n"
        "<single line: best plan name and reason>\n"
    )
    agent3_text = _groq_text(
        "You follow formatting instructions precisely.",
        agent3_user,
    )
    comparison, recommendation = _parse_comparison_and_recommendation(agent3_text)

    return {
        "plans": plans,
        "hospitals": hospitals,
        "comparison": comparison,
        "recommendation": recommendation,
    }
