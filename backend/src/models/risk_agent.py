import json
import requests
import feedparser
import time
import logging
import warnings
from google import genai
from google.genai import types
from src.config import settings

logging.getLogger("google.genai").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

client = genai.Client(api_key=settings.gemini_api_key)

# --- MASTER CORRIDORS LIST (Module-Level Export) ---
master_routes = [
    "Strait of Hormuz",
    "Red Sea",
    "Cape of Good Hope",
    "Strait of Malacca",
    "Chennai Vladivostok Maritime Corridor",
    "International North South Transport Corridor"
]

def fetch_corridor_headlines(corridor: str) -> str:
    headlines = []
    if getattr(settings, "finlight_api_key", None):
        try:
            url = "https://api.finlight.me/v2/articles"
            headers = {
                "accept": "application/json",
                "Content-Type": "application/json",
                "X-API-KEY": settings.finlight_api_key
            }
            payload = {"query": corridor, "language": "en", "pageSize": 10}
            response = requests.post(url, headers=headers, json=payload, timeout=5)
            if response.status_code == 200:
                articles = response.json().get("articles", [])
                headlines = [a.get("title", "") for a in articles if a.get("title")]
        except Exception:
            pass

    if not headlines:
        query = corridor.replace(" ", "+")
        url = f"https://news.google.com/rss/search?q={query}+shipping+OR+oil+OR+attack&hl=en-US&gl=US&ceid=US:en"
        try:
            feed = feedparser.parse(url)
            headlines = [entry.title for entry in feed.entries[:8]]
        except Exception as e:
            print(f"RSS fallback failed for {corridor}: {e}")

    return "\n".join(headlines) if headlines else "No recent news available."

def _fallback_heuristic_evaluator(corridor_news_map: dict, custom_scenario: str = None) -> dict:
    """
    Offline deterministic NLP parser. Runs if Google GenAI encounters 503 capacity limits.
    Evaluates real RSS headlines and custom scenario strings for kinetic indicators.
    """
    results = {}
    kinetic_keywords = ["attack", "strike", "missile", "drone", "houthi", "sink", "sank", "fire", "explosion", "seize", "seized", "blast", "clash"]
    blockage_keywords = ["halt", "halted", "closed", "blocked", "diverted", "suspends", "suspended", "stoppage", "shut"]

    scenario_lower = (custom_scenario or "").lower()

    for key, data in corridor_news_map.items():
        name_lower = data["name"].lower()
        headlines_text = data["headlines"].lower()

        is_targeted_by_scenario = False
        if custom_scenario and (name_lower in scenario_lower or key in scenario_lower or (key == "red_sea" and ("suez" in scenario_lower or "bab" in scenario_lower))):
            is_targeted_by_scenario = True

        if is_targeted_by_scenario:
            threat = 5
            halted = True
            summary = f"SCENARIO DIRECT HIT: {custom_scenario.strip()}"
        else:
            # Parse live RSS headlines
            k_matches = sum(1 for w in kinetic_keywords if w in headlines_text)
            b_matches = sum(1 for w in blockage_keywords if w in headlines_text)

            if b_matches > 0 and k_matches > 0:
                threat = 4
                halted = True
                summary = "Active kinetic threat detected from live maritime news feeds."
            elif k_matches > 0:
                threat = 3
                halted = False
                summary = "Elevated regional security alerts reported in corridor."
            else:
                threat = 1
                halted = False
                summary = "Commercial shipping channels open and operating normally."

        results[key] = {
            "kinetic_threat_level": threat,
            "traffic_halted": halted,
            "summary": summary
        }
    return results

def calculate_global_risk(corridors: list[str] = None, custom_scenario: str = None) -> dict:
    if corridors is None:
        corridors = master_routes

    corridor_news_map = {}
    for corridor in corridors:
        safe_key = corridor.lower().replace(" ", "_").replace("-", "_")
        corridor_news_map[safe_key] = {
            "name": corridor,
            "headlines": fetch_corridor_headlines(corridor)
        }

    news_prompt_block = "\n\n".join(
        f"--- CORRIDOR KEY: {key} ({data['name']}) ---\n{data['headlines']}"
        for key, data in corridor_news_map.items()
    )

    scenario_instruction = ""
    if custom_scenario and custom_scenario.strip():
        scenario_instruction = f"""
        ======================================================================
        CRITICAL OPERATIONAL OVERRIDE - INJECTED "WHAT-IF" SCENARIO:
        "{custom_scenario.strip()}"
        
        INSTRUCTIONS FOR SCENARIO:
        1. Treat this hypothetical event as ABSOLUTE IMMEDIATE GROUND TRUTH.
        2. Identify which corridor(s) are targeted or transit-blocked by this event.
        3. For targeted corridors:
           - Set "kinetic_threat_level" to 5.
           - Set "traffic_halted" to true.
           - In "summary", explain the disruption caused specifically by this scenario.
        4. Other corridors should be evaluated based on their headlines.
        ======================================================================
        """

    prompt = f"""
    Analyze recent news headlines for these global shipping corridors and evaluate threat levels for Indian crude oil tankers.

    {scenario_instruction}

    {news_prompt_block}

    For EACH corridor key, evaluate:
    1. "kinetic_threat_level": Integer from 1 to 5 (1=Peaceful/Diplomatic, 3=Escorts/Drones, 5=Direct missile strike/Blockage).
    2. "traffic_halted": Boolean (true/false) indicating if shipping is halted, blocked, or heavily rerouted.
    3. "summary": A concise one-sentence situational report.

    Return ONLY a JSON object where each key matches the corridor keys provided:
    {list(corridor_news_map.keys())}
    """

    parsed_evaluations = {}
    
    # Priority cascade of high-throughput production models
    candidate_models = [
        "gemini-3.5-flash-lite",
        "gemini-3.8-flash",
        "gemini-3.1-flash-lite",
    ]

    for model_name in candidate_models:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )

            raw_text = response.text.strip()
            parsed_evaluations = json.loads(raw_text)

            if isinstance(parsed_evaluations, list):
                dict_evals = {}
                for item in parsed_evaluations:
                    c_key = item.get("corridor") or item.get("key") or item.get("name") or "unknown"
                    c_key = c_key.lower().replace(" ", "_").replace("-", "_")
                    dict_evals[c_key] = item
                parsed_evaluations = dict_evals

            if parsed_evaluations:
                break

        except Exception as e:
            print(f"Endpoint '{model_name}' unavailable ({e}). Testing next model...")
            continue

    # Fallback to local heuristic engine if all cloud models are under 503 high-load
    if not parsed_evaluations:
        print("Using local RSS/NLP fallback engine for corridor threat modeling.")
        parsed_evaluations = _fallback_heuristic_evaluator(corridor_news_map, custom_scenario)

    final_report = {}
    for key, data in corridor_news_map.items():
        eval_data = parsed_evaluations.get(key, {})
        threat_level = eval_data.get("kinetic_threat_level", 1)
        traffic_halted = eval_data.get("traffic_halted", False)
        summary = eval_data.get("summary", "Normal maritime traffic.")

        if traffic_halted:
            final_score = max(80, (threat_level * 10) + 35)
        else:
            final_score = threat_level * 10

        final_score = min(final_score, 100)

        final_report[key] = {
            "name": data["name"],
            "risk_score": final_score,
            "threat_level": threat_level,
            "traffic_halted": traffic_halted,
            "summary": summary,
            "reason": summary,
            "raw_headlines": data["headlines"]
        }

    # Alias safeguard for Suez Canal / Red Sea key variations
    if "red_sea" in final_report and "suez_canal_red_sea" not in final_report:
        final_report["suez_canal_red_sea"] = final_report["red_sea"]

    return final_report

if __name__ == "__main__":
    print("Evaluating all corridors...")
    result = calculate_global_risk(master_routes)
    print(json.dumps(result, indent=2))