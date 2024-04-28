from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import requests
import argparse
from languagegame.models import GenRequest

app = FastAPI()
templates = Jinja2Templates(directory="templates")

def inference_call(req: GenRequest, API_URL, num_tokens=50):
    response = requests.post(API_URL, json=req.model_dump())
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

@app.get("/inference")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/inference/generate")
async def generate(request: Request):
    form_data = await request.form()
    system_prompt = form_data.get("system_prompt", "")
    input_string = form_data.get("input_string", "")
    num_tokens = int(form_data.get("num_tokens", 50))

    req = GenRequest(
        system_prompt=system_prompt,
        input_string=input_string,
        num_tokens=num_tokens
    )
    result = inference_call(req, "http://localhost:4444/generate", num_tokens)

    if result:
        return {"generated": result["generated"]}
    else:
        return {"generated": "Error occurred during inference."}