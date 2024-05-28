# control.languagegame.io

control.languagegame.io -- interface for GPT-2 demo of control game, GCG prompt hacking interface. 

## Setup
Run these from `~/control.languagegame.io/`
```bash
# create virtual environment 
python3 -m venv venv 

# activate 
source venv/bin/activate 

pip3 install wheel 

# install the minference/languagegame package 
# clone from https://github.com/amanb2000/minference
# to ../minference relative to the root of 
# control.langaugegame.io/
pip3 install -e ../minference 
pip3 install -r ../minference/requirements.txt

# install control.languagegame.io dependencies
pip3 install -r requirements.txt

# install uvicorn 
sudo apt install uvicorn
```


## Run Frontend
```bash 
# start inference server -- gpt2 
python3 ../minference/languagegame/inference_server/main.py \
	--config ../minference/configs/min_gpt2.json \
	--port 4444

# run front-end 
uvicorn app:app --reload --port 8000
```
