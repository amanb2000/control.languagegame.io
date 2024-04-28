from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import requests
import argparse
from datetime import datetime
import hashlib
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

def loss_call(context_string, corpus_string, API_URL):
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

@app.get("/")
def home(request: Request):
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

    req = GenRequest(
        system_prompt=system_prompt,
        input_string=input_string,
        num_tokens=num_tokens
    )
    result = inference_call(req, "http://localhost:4444/generate", num_tokens)

    if result:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # save to telemetry/current_time+hash(form_data)
        hash_str = str(hash(f"{system_prompt}{input_string}{desired_output}{num_tokens}"))
        with open(f"telemetry/{current_time}_{hash_str}.txt", "w") as f:
            f.write(f"System Prompt: {system_prompt}\n")
            f.write(f"Input String: {input_string}\n")
            f.write(f"Desired Output: {desired_output}\n")
            f.write(f"Generated Text: {result['generated']}\n")
            f.write(f"IP of request: {request.client.host}\n")
            f.write(f"Time of request: {current_time}\n")
        generated_text = result["generated"]
        return {f"generated {current_time}": generated_text}
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