from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import csv
import io
import requests
import json
import re

app = FastAPI()

# storing the input from /offer and /leads in memory for now
STATE = {
    "offer": None,
    "leads": [],
    "results": []
}

# MODELS
class ProductOffer(BaseModel):
    name: str
    value_props: list[str]
    ideal_use_cases: list[str]


# RULE-BASED SCORING HELPERS
DECISION_MAKER_KEYWORDS = [
    "head", "vp", "vice", "director", "chief", "cto", "ceo","cxo", "founder", "owner", "manager"
]
INFLUENCER_KEYWORDS = [
    "lead", "senior", "principal", "engineer", "architect",  "analyst", "specialist", "advisor"
]

def classify_role_relevance(role: str) -> int:
    if not role:
        return 0
    r = role.lower()
    for kw in DECISION_MAKER_KEYWORDS:
        if kw in r:
            return 20
    for kw in INFLUENCER_KEYWORDS:
        if kw in r:
            return 10
    return 0

def classify_industry_match(lead_industry: str, offer_icps: list[str]) -> int:
    if not lead_industry:
        return 0
    li = lead_industry.strip().lower()
    for icp in offer_icps:
        if icp.strip().lower() == li:
            return 20
    for icp in offer_icps:
        icpl = icp.strip().lower()
        if icpl in li or li in icpl:
            return 10
    return 0

def data_completeness_score(lead: dict) -> int:
    required = ["name","role","company","industry","location","linkedin_bio"]
    for field in required:
        if not lead.get(field):
            return 0
    return 10



def extract_json(raw_output: str):
    # Remove <think> ... </think> blocks
    cleaned = re.sub(r"<think>.*?</think>", "", raw_output, flags=re.DOTALL).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def ai_reasoning_for_lead(offer, lead, rule_score: int) -> dict:
    print("AI call initiated")
    prompt = f"""
You are an SDR assistant.
Here is the product offer:
- Name: {offer.name}
- Value Props: {", ".join(offer.value_props)}
- Ideal ICPs: {", ".join(offer.ideal_use_cases)}

Here is the lead:
- Name: {lead.get('name')}
- Role: {lead.get('role')}
- Company: {lead.get('company')}
- Industry: {lead.get('industry')}
- Location: {lead.get('location')}
- LinkedIn Bio: {lead.get('linkedin_bio')}

Rule-based score: {rule_score} (out of 50)

Task: Classify the lead's buying intent as High, Medium, or Low.
- High = strongly matches ICP, role, and likely buyer intent.
- Medium = partial fit or some doubts.
- Low = weak or unlikely buyer intent.

Respond ONLY in JSON with two fields:
{{
  "intent_label": "High" | "Medium" | "Low",
  "reasoning": "short explanation"
}}
"""

    try:
        # Disable streaming: wait for the full response
        response = requests.post(
            "https://kuvaka-ollama.loca.lt/api/generate",
            json={
                "model": "qwen3:4b",
                "prompt": prompt,
                "stream": False  
            },
            timeout= 600
        )

        # Get the model output
        raw_output = response.json().get("response", "")
        print("AI Response:", raw_output[:200])  # Optional: preview first 200 chars

        # Parse the JSON returned by the model
        parsed = extract_json(raw_output)
        if parsed:
            print("returning from /score")
            return {
                "intent_label": parsed.get("intent_label", "Medium"),
                "reasoning": parsed.get("reasoning", "No reasoning provided")
            }
        else:
            return {
                "intent_label": "Medium",
                "reasoning": f"Could not parse JSON, raw output: {raw_output[:200]}"
            }

    except Exception as e:
        return {
            "intent_label": "Low",
            "reasoning": f"Ollama error: {str(e)}"
        }


# API ENDPOINTS
@app.post("/offer")
async def post_offer(offer: ProductOffer):
    STATE["offer"] = offer
    return {"status": "ok", "offer": STATE["offer"]}

@app.post("/leads/upload")
async def upload_leads(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        return JSONResponse(status_code=400, content={"error": "File must be a CSV"})
    content = file.file.read().decode('utf-8')
    reader = csv.DictReader(io.StringIO(content))
    leads = [row for row in reader]
    STATE["leads"].extend(leads)
    return {"status": "ok", "count": len(STATE["leads"]), "leads": STATE["leads"]}

@app.get("/offer")
async def get_offer():
    return STATE["offer"] or {"message": "No offer uploaded yet"}

@app.get("/leads")
async def get_leads():
    return STATE["leads"] or {"message": "No leads uploaded yet"}

@app.post("/score")
async def run_rule_scoring():
    offer = STATE.get("offer")
    leads = STATE.get("leads", [])
    if not offer:
        return JSONResponse(status_code=400, content="No offer uploaded. Use POST /offer first.")
    if not leads:
        return JSONResponse(status_code=400, content="No leads uploaded. Use POST /leads/upload first.")

    results = []
    for lead in leads:
        role_score = classify_role_relevance(lead.get("role", ""))
        industry_score = classify_industry_match(lead.get("industry", ""), offer.ideal_use_cases)
        completeness_score = data_completeness_score(lead)

        rule_score = role_score + industry_score + completeness_score
        ai_result = ai_reasoning_for_lead(offer, lead, rule_score)

        results.append({
            "name": lead.get("name"),
            "role": lead.get("role"),
            "company": lead.get("company"),
            "industry": lead.get("industry"),
            "score": rule_score,
            "rule_breakdown": {
                "role": role_score,
                "industry": industry_score,
                "completeness": completeness_score
            },
            "ai_intent": ai_result["intent_label"],
            "ai_reasoning": ai_result["reasoning"]
        })

    STATE["results"] = results
    return {"status": "ok", "count": len(results)}

@app.get("/results")
async def get_results():
    return STATE.get("results", [])
