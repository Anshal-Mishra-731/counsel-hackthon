import json
import logging
import time
import warnings

import feedparser
import requests
from google import genai
from google.genai import types

from src.config import settings


logging.getLogger("google.genai").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

client = genai.Client(api_key=settings.gemini_api_key)


def fetch_corridor_headlines(corridor: str) -> str:
    """Fetch up to 10 headlines using Finlight or Google News RSS fallback."""

    headlines = []

    # -----------------------------
    # 1. Finlight
    # -----------------------------
    if settings.finlight_api_key:
        try:
            url = "https://api.finlight.me/v2/articles"

            headers = {
                "accept": "application/json",
                "Content-Type": "application/json",
                "X-API-KEY": settings.finlight_api_key,
            }

            payload = {
                "query": corridor,
                "language": "en",
                "pageSize": 10,
            }

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=8,
            )

            if response.status_code == 200:
                articles = response.json().get("articles", [])

                headlines = [
                    article.get("title", "")
                    for article in articles
                    if article.get("title")
                ]

        except Exception:
            # Silently fallback to RSS
            pass

    # -----------------------------
    # 2. Google News RSS fallback
    # -----------------------------
    if not headlines:
        query = corridor.replace(" ", "+")

        url = (
            f"https://news.google.com/rss/search?"
            f"q={query}+shipping+OR+oil+OR+attack"
            f"&hl=en-US&gl=US&ceid=US:en"
        )

        try:
            feed = feedparser.parse(url)

            headlines = [
                entry.title
                for entry in feed.entries[:10]
            ]

        except Exception as e:
            print(
                f"RSS fallback failed for {corridor}: {e}"
            )

    return (
        "\n".join(headlines)
        if headlines
        else "No recent news available."
    )


def calculate_global_risk(corridors: list[str]) -> dict:

    corridor_news_map = {}

    # -----------------------------
    # Fetch news
    # -----------------------------
    for corridor in corridors:

        safe_key = (
            corridor.lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

        corridor_news_map[safe_key] = {
            "name": corridor,
            "headlines": fetch_corridor_headlines(corridor),
        }

    # -----------------------------
    # Build Gemini prompt
    # -----------------------------
    news_prompt_block = "\n\n".join(
        f"--- CORRIDOR KEY: {key} "
        f"({data['name']}) ---\n"
        f"{data['headlines']}"
        for key, data in corridor_news_map.items()
    )

    prompt = f"""
Analyze recent news headlines for these global shipping corridors
and evaluate their threat levels.

{news_prompt_block}

For EACH corridor key, evaluate:

1. "kinetic_threat_level":
   Integer from 1 to 5.

   1 = Diplomatic tension
   2 = Elevated tension
   3 = Military posturing / escorts
   4 = Serious military activity / disruption risk
   5 = Physical attack / strikes

2. "traffic_halted":
   Boolean true/false indicating whether shipping
   is actively blocked, paused, or majorly diverted.

3. "summary":
   A single concise sentence explaining the situation.

Return ONLY a JSON object where each key matches
the corridor keys provided.
"""

    parsed_evaluations = {}

    max_retries = 2

    # -----------------------------
    # Gemini
    # -----------------------------
    for attempt in range(max_retries):

        try:

            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )

            parsed_evaluations = json.loads(response.text)

            break

        except Exception as e:

            error_msg = str(e)

            if (
                "429" in error_msg
                or "RESOURCE_EXHAUSTED" in error_msg
            ):

                wait_time = 35

                print(
                    f"⚠️ Google API free-tier cooldown hit. "
                    f"Pausing for {wait_time} seconds..."
                )

                time.sleep(wait_time)

            else:

                print(
                    f"LLM parsing failed: {e}"
                )

                break

    # -----------------------------
    # Final risk report
    # -----------------------------
    final_report = {}

    for key, data in corridor_news_map.items():

        eval_data = parsed_evaluations.get(key, {})

        threat_level = eval_data.get(
            "kinetic_threat_level",
            1,
        )

        traffic_halted = eval_data.get(
            "traffic_halted",
            False,
        )

        summary = eval_data.get(
            "summary",
            "Normal maritime traffic.",
        )

        score = (
            threat_level * 10
            + (30 if traffic_halted else 0)
        )

        final_score = min(score, 100)

        final_report[key] = {
            "name": data["name"],
            "risk_score": final_score,
            "threat_level": threat_level,
            "traffic_halted": traffic_halted,
            "summary": summary,
            "raw_headlines": data["headlines"],
        }

    return final_report


# ==========================================
# RUN EVERYTHING
# ==========================================

if __name__ == "__main__":

    master_routes = [
        "Strait of Hormuz",
        "Red Sea",
        "Cape of Good Hope",
        "Strait of Malacca",
        "Chennai Vladivostok Maritime Corridor",
        "International North South Transport Corridor",
    ]

    print(
        "Evaluating all corridors in a single batch..."
    )

    result = calculate_global_risk(master_routes)

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )