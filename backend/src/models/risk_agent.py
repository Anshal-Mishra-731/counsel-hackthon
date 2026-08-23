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
    if settings.finlight_api_key:
        try:
            url = "https://api.finlight.me/v2/articles"
            headers = {
                "accept": "application/json",
                "Content-Type": "application/json",
                "X-API-KEY": settings.finlight_api_key
            }
            payload = {"query": corridor, "language": "en", "pageSize": 10}
            response = requests.post(url, headers=headers, json=payload, timeout=8)
            if response.status_code == 200:
                articles = response.json().get("articles", [])
                headlines = [a.get("title", "") for a in articles if a.get("title")]
        except Exception as e:
            pass

    if not headlines:
        query = corridor.replace(" ", "+")
        url = f"https://news.google.com/rss/search?q={query}+shipping+OR+oil+OR+attack&hl=en-US&gl=US&ceid=US:en"
        try:
            feed = feedparser.parse(url)
            headlines = [entry.title for entry in feed.entries[:10]]
        except Exception as e:
            print(f"RSS fallback failed for {corridor}: {e}")

    return "\n".join(headlines) if headlines else "No recent news available."

def calculate_global_risk(corridors: list[str] = None) -> dict:
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
        
    prompt = f"""
    Analyze recent news headlines for these global shipping corridors and evaluate their threat levels.

    {news_prompt_block}

    For EACH corridor key, evaluate:
    1. "kinetic_threat_level": Integer from 1 to 5 (1=Diplomatic tension, 3=Military posturing/escorts, 5=Physical attack/strikes).
    2. "traffic_halted": Boolean (true/false) indicating if shipping is actively blocked, paused, or majorly diverted.
    3. "summary": A single concise sentence explaining the situation.

    Return ONLY a JSON object where each key matches the corridor keys provided.
    """

    parsed_evaluations = {}
    max_retries = 2
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-3.5-flash-lite',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            
            # Use response.text directly, no cleaned_json!
            parsed_evaluations = json.loads(response.text)
            
            # Safely convert if Gemini returned a List instead of a Dict
            if isinstance(parsed_evaluations, list):
                dict_evals = {}
                for item in parsed_evaluations:
                    c_key = item.get("corridor") or item.get("name") or "unknown"
                    c_key = c_key.lower().replace(" ", "_")
                    dict_evals[c_key] = item
                parsed_evaluations = dict_evals
                
            break 
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                wait_time = 35
                print(f"⚠️ Rate limit hit. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"LLM parsing error: {e}")
                break

    final_report = {}
    for key, data in corridor_news_map.items():
        eval_data = parsed_evaluations.get(key, {})
        threat_level = eval_data.get("kinetic_threat_level", 1)
        traffic_halted = eval_data.get("traffic_halted", False)
        summary = eval_data.get("summary", "Normal maritime traffic.")

        score = (threat_level * 10) + (30 if traffic_halted else 0)
        final_score = min(score, 100)

        final_report[key] = {
            "name": data["name"],
            "risk_score": final_score,
            "threat_level": threat_level,
            "traffic_halted": traffic_halted,
            "summary": summary,
            "raw_headlines": data["headlines"]
        }

    return final_report

if __name__ == "__main__":
    print("Evaluating all corridors in a single batch...")
    result = calculate_global_risk(master_routes)
    print(json.dumps(result, indent=2))