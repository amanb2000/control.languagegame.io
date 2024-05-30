"""
This script takes full_leaderboard.txt and keeps only the first instance of each 
control input. 

full_leaderboard.txt is actually organized like a CSV: 

nickname,control input,ce loss,k,generated text,desired output,time of request,reached desired output
nathan@sweetlyrational.com,  greatu,2.645308494567871,8, greatest man in the world,greatest,2024-05-29 20:52:25,True
...

The script uses pandas to read the CSV and then uses efficient/reliable in-built 
functionality to remove duplicates. The output is written to nodups_leaderboard.txt.
"""
# %%
import os
import re
from datetime import datetime
import pandas as pd
import pdb
# %%
MAX_LEN = 32
MAX_LEADERBOARD = 800

script_dir = os.path.dirname(os.path.abspath(__file__))
telemetry_folder = os.path.join(script_dir, 'telemetry')
leaderboard_file = os.path.join(script_dir, 'leaderboard.txt')
full_leaderboard_file = os.path.join(script_dir, 'full_leaderboard.txt')
nodups_leaderboard_file = os.path.join(script_dir, 'nodups_leaderboard.txt')
nodups_full_leaderboard_file = os.path.join(script_dir, 'nodups_full_leaderboard.txt')
logfile = os.path.join(script_dir, 'recompute_leaderboard.log')
# %%
# Read the full leaderboard CSV file into a pandas DataFrame
df = pd.read_csv(full_leaderboard_file)
# %%
# Convert the 'time of request' column to datetime
df['time of request'] = pd.to_datetime(df['time of request'])

# %%
# Sort the DataFrame by 'time of request' in ascending order
df_sorted = df.sort_values('time of request')

# %%
# Remove duplicates based on the 'control input' column, keeping the first occurrence
df_nodups = df_sorted.drop_duplicates(subset='control input', keep='first')

# %%
# extract one subset where they achieved the optimization outcome ('reached desired output' == True)
df_nodups_reached = df_nodups[df_nodups['reached desired output'] == True]
# sort these by the number of control characters 'k' -- shortest at the top
df_nodups_reached_sorted = df_nodups_reached.sort_values('k')


# %%
# extract subset where the optimization outcome was not achieved ('reached desired output' == False)
df_nodups_notreached = df_nodups[df_nodups['reached desired output'] == False]
# sort these by ce loss -- smallest at the top 
df_nodups_notreached_sorted = df_nodups_notreached.sort_values('ce loss') 


# %%
# concatenate the two dataframes, save to the nodups_leaderboard_file
df_nodups_sorted = pd.concat([df_nodups_reached_sorted, df_nodups_notreached_sorted])

# truncate to top MAX_LEADERBOARD
df_nodups_sorted_truncated = df_nodups_sorted.head(MAX_LEADERBOARD)

# add 'rank' column 
df_nodups_sorted_truncated['rank'] = range(1, len(df_nodups_sorted_truncated) + 1)



# %%
# Write the resulting DataFrame to the nodups_leaderboard.txt file
df_nodups_sorted_truncated.to_csv(nodups_leaderboard_file, index=False)

# %% 
# write the untruncated version to nodups_full_leaderboard_file
df_nodups_sorted.to_csv(nodups_full_leaderboard_file, index=False)


# %%
