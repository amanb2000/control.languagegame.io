"""
This script recomputes leaderboard.txt based on the contents of telemetry/ 

The telemetry/ folder is full of .txt files with the format 

```
Nickname: asdf
System Prompt: asdf
Input String: Roger Federer is the 
Desired Output: greatest
Generated Text:  best player in the world
IP of request: 127.0.0.1
Time of request: 2024-04-28 04:30:25
```

The leaderboard.txt file is a CSV with columns 
 - nickname
 - control input (maps to System Prompt)
 - num control chars 
 - generated text: the generated text
 - desired output
 - time of request
 - reached desired output: True or False


We want to rank it so that the ones that did reach (i.e., where generated text starts with the desired output). 
Note that you should use the rstrip and lower() functions to compare the generated text and desired output.
Anyway, the ones that succeeded come first, and in that population, the ones with the shortest num control chars 
wins. 

"""

import os
import re
from datetime import datetime
import pandas as pd
import pdb

MAX_LEN=32
MAX_LEADERBOARD = 1000

script_dir = os.path.dirname(os.path.abspath(__file__))
telemetry_folder = os.path.join(script_dir, 'telemetry')
leaderboard_file = os.path.join(script_dir, 'leaderboard.txt')
full_leaderboard_file = os.path.join(script_dir, 'full_leaderboard.txt')
nodups_leaderboard_file = os.path.join(script_dir, 'nodups_leaderboard.txt')
logfile = os.path.join(script_dir, 'recompute_leaderboard.log')

# add an entry to the logfile 
def log(msg):
    with open(logfile, 'a') as f:
        f.write(f'{datetime.now()}: {msg}\n')

# write a message saying that we recomputed... 
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
log(f'Recomputing leaderboard at {current_time}...')

def read_telemetry_file(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    telemetry_data = {
        'Nickname': None,
        'System Prompt': None,
        'Input String': None,
        'Desired Output': None,
        'Generated Text': None,
        'IP of request': None,
        'Time of request': None, 
        'CE Loss': None, 
        'k': None
    }

    for line in lines:
        key, value = line.strip().split(': ', 1)
        telemetry_data[key] = value

    telemetry_data['k'] = len(telemetry_data['System Prompt'])
    # print("Length of input string: ", telemetry_data['k'])
    # print("Input string: ", telemetry_data['System Prompt'])

    # Crop all entries to MAX_LEN chars
    for key in telemetry_data:
        if telemetry_data[key] is not None:
            try: 
                if len(telemetry_data[key]) > MAX_LEN:
                    telemetry_data[key] = telemetry_data[key][:MAX_LEN]
                    # add [...]
                    telemetry_data[key] += '[...]'
            except: 
                pass
        # ensure commas are escaped 
        try: 
            telemetry_data[key] = telemetry_data[key].replace(',', ';')
        except: 
            pass

    # sort by descending CE loss
    telemetry_data['CE Loss'] = float(telemetry_data['CE Loss'])

    return telemetry_data

def process_telemetry_folder(folder_path):
    leaderboard_entries = []

    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(folder_path, filename)
            try: 
                telemetry_data = read_telemetry_file(file_path)
            except Exception as e: 
                print("Unable to read telemetry data for file: ", file_path)
                print("Exception: ", e)

            nickname = telemetry_data['Nickname']
            control_input = telemetry_data['System Prompt']
            num_control_chars = len(control_input)
            generated_text = telemetry_data['Generated Text']
            desired_output = telemetry_data['Desired Output'].strip().lower()
            time_of_request = datetime.strptime(telemetry_data['Time of request'], '%Y-%m-%d %H:%M:%S')
            #$if nickname == 'Not Aman': 
                #pdb.set_trace()
            generated_text = re.sub(r'\s', ' ', generated_text)
            reached_desired_output = f"{generated_text}".strip().lower().startswith(desired_output)

            leaderboard_entries.append({
                'nickname': nickname,
                'control input': control_input,
                'ce loss': telemetry_data['CE Loss'],
                'k': telemetry_data['k'],
                'generated text': generated_text,
                'desired output': desired_output,
                'time of request': time_of_request,
                'reached desired output': reached_desired_output
            })

    # leaderboard_entries.sort(key=lambda x: (x['reached desired output'] == False, x['ce loss']))
    # leaderboard_entries.sort(key=lambda x: (x['reached desired output'] == False, x['ce loss'], x['k']))
    # Sort the entries first by 'reached desired output' (True first)
    leaderboard_entries.sort(key=lambda x: (x['reached desired output'] == False))

    # Then sort the entries where 'reached desired output' is True by 'k' (ascending)
    true_entries = [entry for entry in leaderboard_entries if entry['reached desired output']]
    true_entries.sort(key=lambda x: x['k'])

    # Sort the entries where 'reached desired output' is False by 'ce loss' (ascending)
    false_entries = [entry for entry in leaderboard_entries if not entry['reached desired output']]
    false_entries.sort(key=lambda x: x['ce loss'])

    # Rebuild the leaderboard_entries list with the sorted entries
    leaderboard_entries = true_entries + false_entries

    # if there are any entries with reached\ desired\ output = True, then we 
    # remove all entries with reached desired output = False
    #if any(entry['reached desired output'] for entry in leaderboard_entries):
        # leaderboard_entries = [entry for entry in leaderboard_entries if entry['reached desired output']]
    cnt=0
    with open(leaderboard_file, 'w', newline='') as f:
        f.write('nickname,control input,ce loss,k,generated text,desired output,time of request,reached desired output\n')
        for entry in leaderboard_entries:
            f.write(f"{entry['nickname']},{entry['control input']},{entry['ce loss']},{entry['k']},{entry['generated text']},{entry['desired output']},{entry['time of request']},{entry['reached desired output']}\n")
            cnt += 1
            if cnt > MAX_LEADERBOARD: 
                break
    
    # now write to the full leaderboard
    with open(full_leaderboard_file, 'w', newline='') as f:
        f.write('nickname,control input,ce loss,k,generated text,desired output,time of request,reached desired output\n')
        for entry in leaderboard_entries:
            f.write(f"{entry['nickname']},{entry['control input']},{entry['ce loss']},{entry['k']},{entry['generated text']},{entry['desired output']},{entry['time of request']},{entry['reached desired output']}\n")



if __name__ == '__main__':
    process_telemetry_folder(telemetry_folder)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{current_time}] Recomputed leaderboard. Check leaderboard.txt for the updated leaderboard.")
    print(f"Now computing nodups_full_leaderboard.txt...")
    # run the script located at compute_nodups_leaderboard.py -- located in the same
    # directory as this script
    nodup_script_path = os.path.join(script_dir, 'compute_nodups_leaderboard.py')
    os.system(f'/home/aman/control.languagegame.io/venv/bin/python3 {nodup_script_path}')
    print(f"[{current_time}] Done computing nodups_full_leaderboard.txt.")
    log(f"{current_time}: Done computing nodups_full_leaderboard.txt, done computing leaderboard.txt")
