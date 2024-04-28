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
from datetime import datetime

MAX_LEN=32

script_dir = os.path.dirname(os.path.abspath(__file__))
telemetry_folder = os.path.join(script_dir, 'telemetry')
leaderboard_file = os.path.join(script_dir, 'leaderboard.txt')
logfile = os.path.join(script_dir, 'recompute_leaderboard.log')

# add an entry to the logfile 
def log(msg):
    with open(logfile, 'a') as f:
        f.write(f'{datetime.now()}: {msg}\n')

# write a message saying that we recomputed... 
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
log('Recomputing leaderboard at {current_time}...')

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
        'CE Loss': None
    }

    for line in lines:
        key, value = line.strip().split(': ', 1)
        telemetry_data[key] = value

    # Crop all entries to MAX_LEN chars
    for key in telemetry_data:
        if telemetry_data[key] is not None:
            if len(telemetry_data[key]) > MAX_LEN:
                telemetry_data[key] = telemetry_data[key][:MAX_LEN]
                # add [...]
                telemetry_data[key] += '[...]'

    return telemetry_data

def process_telemetry_folder(folder_path):
    leaderboard_entries = []

    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(folder_path, filename)
            telemetry_data = read_telemetry_file(file_path)

            nickname = telemetry_data['Nickname']
            control_input = telemetry_data['System Prompt']
            num_control_chars = len(control_input)
            generated_text = telemetry_data['Generated Text']
            desired_output = telemetry_data['Desired Output'].rstrip().lower()
            time_of_request = datetime.strptime(telemetry_data['Time of request'], '%Y-%m-%d %H:%M:%S')
            reached_desired_output = generated_text.rstrip().lower().startswith(desired_output)

            leaderboard_entries.append({
                'nickname': nickname,
                'control input': control_input,
                'ce loss': telemetry_data['CE Loss'],
                'num control chars': num_control_chars,
                'generated text': generated_text,
                'desired output': desired_output,
                'time of request': time_of_request,
                'reached desired output': reached_desired_output
            })

    leaderboard_entries.sort(key=lambda x: (x['reached desired output'] == False, x['num control chars']))

    # if there are any entries with reached\ desired\ output = True, then we 
    # remove all entries with reached desired output = False
    if any(entry['reached desired output'] for entry in leaderboard_entries):
        leaderboard_entries = [entry for entry in leaderboard_entries if entry['reached desired output']]

    with open(leaderboard_file, 'w', newline='') as f:
        f.write('nickname,control input,ce loss,num control chars,generated text,desired output,time of request,reached desired output\n')
        for entry in leaderboard_entries:
            f.write(f"{entry['nickname']},{entry['control input']},{entry['ce loss']},{entry['num control chars']},{entry['generated text']},{entry['desired output']},{entry['time of request']},{entry['reached desired output']}\n")

if __name__ == '__main__':
    process_telemetry_folder(telemetry_folder)