from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import requests
import argparse
from datetime import datetime
import hashlib
from languagegame.models import GenRequest
from fastapi.responses import JSONResponse

import csv
from typing import List, Dict
import os



app = FastAPI()
templates = Jinja2Templates(directory="templates")

logfile = "frontend.log"
# if it doesnt exist, make it
if not os.path.exists(logfile):
    with open(logfile, "w") as f:
        f.write("")

def log(msg):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(logfile, "a") as f:
        f.write(f"[{current_time}] {msg}\n")

log("Starting frontend server...")

def read_leaderboard() -> List[Dict]:
    leaderboard_data = []
    try:
        with open('nodups_leaderboard.txt', 'r') as f:
            reader = csv.DictReader(f)
            leaderboard_data = list(reader)
    except FileNotFoundError:
        pass  # Handle the case when the file doesn't exist
    return leaderboard_data

@app.get("/leaderboard")
def get_leaderboard():
    log('Getting leaderboard...')
    leaderboard_data = read_leaderboard()
    log('Leaderboard data retrieved.')
    return JSONResponse(content=leaderboard_data)

def inference_call(req: GenRequest, API_URL, num_tokens=50):
    log('Making inference call...')
    response = requests.post(API_URL, json=req.model_dump())
    if response.status_code == 200:
        log('Inference call successful.')
        return response.json()
    else:
        log(f'Inference call error {response.status_code}: {response.text}')
        print(f"Error {response.status_code}: {response.text}")
        return None

def loss_call(context_string, corpus_string, API_URL):
    log('Making loss call...')
    data = {
        "context_string": context_string,
        "corpus_string": corpus_string
    }
    response = requests.post(API_URL, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None



def get_client_ip(request: Request):
    if "X-Forwarded-For" in request.headers:
        ip_address = request.headers["X-Forwarded-For"]
    elif "X-Real-IP" in request.headers:
        ip_address = request.headers["X-Real-IP"]
    else:
        ip_address = request.client.host
    return ip_address

@app.get("/")
def home(request: Request):
    ip_address = get_client_ip(request)
    log(f"Page request '/' from {ip_address}")
    return templates.TemplateResponse("index.html", {"request": request})

def hash(str_in): 
    """md5 hash 
    """
    return hashlib.md5(str_in.encode()).hexdigest()

@app.post("/generate")
async def generate(request: Request):
    form_data = await request.form()
    system_prompt = form_data.get("system_prompt", "")
    input_string = form_data.get("input_string", "")
    desired_output = form_data.get("desired_output", "")
    num_tokens = int(form_data.get("num_tokens", 50))
    nickname = form_data.get("nickname", "anonymous")
    log(f'Generation request from ip {get_client_ip(request)} with nickname {nickname}...')

    req = GenRequest(
        system_prompt=system_prompt,
        input_string=input_string,
        num_tokens=num_tokens
    )
    result = inference_call(req, "http://localhost:4444/generate", num_tokens)

    # compute CE loss too 
    context = system_prompt + input_string
    future = desired_output
    print("prior: ", context)
    print("posterior: ", future)
    ce_loss = loss_call(context, future, "http://localhost:4444/ce_loss")

    if result:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # save to telemetry/current_time+hash(form_data)
        hash_str = str(hash(f"{system_prompt}{input_string}{desired_output}{num_tokens}"))
        with open(f"telemetry/{current_time}_{hash_str}.txt", "w") as f:
            f.write(f"Nickname: {nickname}\n")
            f.write(f"System Prompt: {system_prompt}\n")
            f.write(f"Input String: {input_string}\n")
            f.write(f"Desired Output: {desired_output}\n")
            f.write(f"Generated Text: {result['generated']}\n")
            f.write(f"IP of request: {request.client.host}\n")
            f.write(f"Time of request: {current_time}\n")
            f.write(f"CE Loss: {ce_loss['loss']}\n")
        generated_text = result["generated"]
        return {f"generated {current_time}": generated_text, "ce_loss": ce_loss['loss']}
    else:
        return {"generated": "Error occurred during inference."}


@app.post("/ce_loss")
async def ce_loss(request: Request):
    form_data = await request.form()
    context_string = form_data.get("context_string", "")
    corpus_string = form_data.get("corpus_string", "")

    result = loss_call(context_string, corpus_string, "http://localhost:4444/ce_loss")

    if result:
        return {"initial_request": result["initial_request"], "loss": result["loss"]}
    else:
        return {"error": "Error occurred during loss computation."}
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host address")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    args = parser.parse_args()

    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)
