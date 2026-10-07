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

# --- MASTER CORRIDORS LIST ---
master_routes = [
    "Strait of Hormuz",
    "Red Sea",
    "Cape of Good Hope",
    "Strait of Malacca",
    "Chennai Vladivostok Maritime Corridor",
    "International North South Transport Corridor"
]

# --- STANDING GEOPOLITICAL BASELINES ---
# The permanent memory of the engine. News and scenarios calculate the 'delta' against these states.
STRUCTURAL_BASELINES = {
    "strait_of_hormuz": {"base_threat": 3, "base_halted": False, "context": "Elevated war-risk premiums and naval patrols active, but physical transit remains open."},
    "red_sea": {"base_threat": 4, "base_halted": True, "context": "Houthi anti-ship ballistic missile campaign maintains widespread commercial rerouting."},
    "cape_of_good_hope": {"base_threat": 1, "base_halted": False, "context": "Safe alternate deep-water routing, operating normally."},
    "strait_of_malacca": {"base_threat": 1, "base_halted": False, "context": "Major commercial chokepoint operating normally under regional naval patrols."},
    "chennai_vladivostok_maritime_corridor": {"base_threat": 1, "base_halted": False, "context": "Pacific-Arctic route operating without kinetic disruption."},
    "instc": {"base_threat": 2, "base_halted": False, "context": "Overland and Caspian route faces political friction but remains physically open."},
    "international_north_south_transport_corridor": {"base_threat": 2, "base_halted": False, "context": "Overland and Caspian route faces political friction but remains physically open."}
}

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
    results = {}
    kinetic_keywords = ["missile", "drone", "houthi", "sink", "sank", "explosion", "seize", "seized", "blast", "clash", "strike"]
    blockage_keywords = ["strait closed", "canal blocked", "traffic halted", "blockade", "navigational shutdown"]

    scenario_lower = (custom_scenario or "").lower()
    
    disrupted_suppliers = []
    supplier_names = [
        "iraq", "saudi arabia", "uae", "united arab emirates", "kuwait", 
        "qatar", "oman", "russia", "algeria", "egypt", "nigeria", 
        "angola", "united states", "usa", "brazil", "gabon", "norway", 
        "malaysia", "indonesia", "australia", "iran", "kazakhstan"
    ]
    for s in supplier_names:
        if s in scenario_lower:
            disrupted_suppliers.append(s.title())

    corridor_keywords = {
        "strait_of_hormuz": ["hormuz", "persian gulf", "iranian waters"],
        "red_sea": ["red sea", "bab-el-mandeb", "bab el mandeb", "suez", "houthi"],
        "cape_of_good_hope": ["cape of good hope", "south africa", "atlantic corridor"],
        "strait_of_malacca": ["malacca", "singapore strait"],
        "chennai_vladivostok_maritime_corridor": ["vladivostok", "sea of japan", "luzon"],
        "instc": ["instc", "caspian", "chabahar"],
        "international_north_south_transport_corridor": ["instc", "caspian", "chabahar"]
    }

    for key, data in corridor_news_map.items():
        # 1. Load the permanent baseline state
        baseline = STRUCTURAL_BASELINES.get(key, {"base_threat": 1, "base_halted": False, "context": "Operating normally."})
        threat = baseline["base_threat"]
        halted = baseline["base_halted"]
        summary = baseline["context"]

        headlines_text = data["headlines"].lower()
        tokens = corridor_keywords.get(key, [key.replace("_", " ")])
        is_corridor_targeted = any(t in scenario_lower for t in tokens) if custom_scenario else False

        # 2. Apply Delta (Escalate or Resolve based on news/scenario)
        if is_corridor_targeted:
            threat = 5
            halted = True
            summary = "CORRIDOR CLOSED: Injected scenario physically halts passage."
        else:
            k_matches = sum(1 for w in kinetic_keywords if w in headlines_text)
            b_matches = sum(1 for w in blockage_keywords if w in headlines_text)

            if b_matches > 0 and k_matches > 0:
                threat = max(threat, 4)
                halted = True
                summary = "Active kinetic blockade detected from live maritime news feeds."
            elif k_matches > 0:
                threat = max(threat, 2)
                summary = "Elevated regional security vigilance in effect based on live feeds."

        results[key] = {
            "kinetic_threat_level": threat,
            "traffic_halted": halted,
            "summary": summary
        }

    return {"corridors": results, "disrupted_suppliers": disrupted_suppliers}

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

    baseline_prompt_block = "\n".join(
        f"- {k}: {v['context']} (Threat Level: {v['base_threat']}, Halted: {v['base_halted']})"
        for k, v in STRUCTURAL_BASELINES.items()
    )

    scenario_instruction = ""
    if custom_scenario and custom_scenario.strip():
        scenario_instruction = f"""
        ======================================================================
        CRITICAL OPERATIONAL OVERRIDE - INJECTED "WHAT-IF" SCENARIO:
        "{custom_scenario.strip()}"
        
        STRICT ISOLATION PROTOCOL:
        1. PHYSICAL PASSAGE vs SOVEREIGN EMBARGO: Differentiate between a physical sea lane blockade (mines, missile strikes, canal obstruction) and a sovereign nation refusing/halting crude exports.
        2. IF A NATION HALTS CRUDE EXPORTS:
           - Do NOT set "traffic_halted": true on any maritime corridor unless that specific strait is under kinetic attack.
           - Add the exporter nation name to the "disrupted_suppliers" array.
        3. IF A CORRIDOR CHOKEPOINT IS ATTACKED:
           - Set "traffic_halted": true ONLY for the geographically targeted corridor.
        ======================================================================
        """

    prompt = f"""
    You are an AI maritime risk analyst. Evaluate threat levels for Indian crude oil tankers.
    
    STANDING GEOPOLITICAL BASELINES (Start your evaluation from these known states):
    {baseline_prompt_block}

    {scenario_instruction}

    LIVE MARITIME NEWS FEEDS (Use these to escalate or resolve the baselines):
    {news_prompt_block}

    For EACH corridor key, evaluate the DELTA against its baseline:
    1. "kinetic_threat_level": Integer from 1 to 5 (1=Peaceful, 3=Escorts/Drones, 5=Direct strike/Blockade).
    2. "traffic_halted": Boolean (true/false) indicating if shipping through this specific physical sea lane is physically shut down.
    3. "summary": A concise one-sentence situational report.

    Additionally, identify if any sovereign crude exporter countries are refusing to export or offline, and list them in "disrupted_suppliers".

    Return ONLY a JSON object matching this exact structure:
    {{
      "corridors": {{
        "<corridor_key>": {{
          "kinetic_threat_level": 1,
          "traffic_halted": false,
          "summary": "..."
        }}
      }},
      "disrupted_suppliers": []
    }}
    """

    parsed_evaluations = {}
    disrupted_suppliers = []
    
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
                    temperature=0.0
                )
            )

            raw_text = response.text.strip()
            full_response = json.loads(raw_text)

            if isinstance(full_response, dict) and "corridors" in full_response:
                parsed_evaluations = full_response["corridors"]
                disrupted_suppliers = full_response.get("disrupted_suppliers", [])
            else:
                parsed_evaluations = full_response
                disrupted_suppliers = []

            if isinstance(parsed_evaluations, list):
                dict_evals = {}
                for item in parsed_evaluations:
                    c_key = item.get("corridor") or item.get("key") or item.get("name") or "unknown"
                    c_key = c_key.lower().replace(" ", "_").replace("-", "_")
                    dict_evals[c_key] = item
                parsed_evaluations = dict_evals
            else:
                dict_evals = {}
                for k, v in parsed_evaluations.items():
                    c_key = k.lower().replace(" ", "_").replace("-", "_")
                    dict_evals[c_key] = v
                parsed_evaluations = dict_evals

            if parsed_evaluations:
                break

        except Exception as e:
            print(f"Endpoint '{model_name}' unavailable ({e}). Testing next model...")
            continue

    if not parsed_evaluations:
        print("Using local RSS/NLP fallback engine for corridor threat modeling.")
        fallback_res = _fallback_heuristic_evaluator(corridor_news_map, custom_scenario)
        parsed_evaluations = fallback_res["corridors"]
        disrupted_suppliers = fallback_res["disrupted_suppliers"]

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

    final_report["_disrupted_suppliers"] = disrupted_suppliers

    return final_report

if __name__ == "__main__":
    print("Evaluating all corridors...")
    result = calculate_global_risk(master_routes)
    print(json.dumps(result, indent=2))