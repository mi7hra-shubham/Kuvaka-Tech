from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import csv
import io

app = FastAPI()

#storing the input from /offer and /leads in the memory for now
STATE = {
    "offer": None,
    "leads": []
}


class ProductOffer(BaseModel):
    name: str
    value_props: list[str]
    ideal_use_cases: list[str]

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

#Checking if the data is being stored locally
@app.get("/offer")
async def get_offer():
    if not STATE["offer"]:
        return {"offer": None, "message": "No offer uploaded yet"}
    return STATE["offer"]


@app.get("/leads")
async def get_leads():
    if not STATE["leads"]:
        return {"leads": [], "message": "No leads uploaded yet"}
    return STATE["leads"]



#Rule based scoring
DECISION_MAKER_KEYWORDS = ["head", "vp", "vice", "director", "chief", "cto", "ceo", "cxo", "founder", "owner", "manager"]
INFLUENCER_KEYWORDS = ["lead", "senior", "principal", "engineer", "architect", "analyst", "specialist", "advisor"]

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
    # Exact match
    for icp in offer_icps:
        if icp.strip().lower() == li:
            return 20
    # Adjacent match (substring check)
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


#Testing the rule based scoring
@app.post("/score")
async def run_rule_scoring():
    offer = STATE.get("offer")
    leads = STATE.get("leads", [])
    if not offer:
        raise JSONResponse(status_code=400, content="No offer uploaded. Use POST /offer first.")
    if not leads:
        raise JSONResponse(status_code=400, content="No leads uploaded. Use POST /leads/upload first.")

    results = []
    for lead in leads:
        role_score = classify_role_relevance(lead["role"])
        industry_score = classify_industry_match(lead["industry"], offer["ideal_use_cases"])
        completeness_score = data_completeness_score(lead)

        rule_score = role_score + industry_score + completeness_score

        results.append({
            "name": lead["name"],
            "role": lead["role"],
            "company": lead["company"],
            "industry": lead["industry"],
            "score": rule_score,
            "rule_breakdown": {
                "role": role_score,
                "industry": industry_score,
                "completeness": completeness_score
            }
        })

    STATE["results"] = results
    return {"status": "ok", "count": len(results)}
