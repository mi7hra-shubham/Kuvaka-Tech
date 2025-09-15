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


