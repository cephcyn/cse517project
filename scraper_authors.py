import urllib.request, json
import pandas as pd
from pandas.io.json import json_normalize
import numpy as np
import json
import time
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--csv_file_name", required=True, help="Filename of the Reddit-scrape-data CSV we want author data for")
parser.add_argument("--output", required=False, default='data/authorsubs.json', help="Filename to save to")
args = parser.parse_args()
print(' reading from', args.csv_file_name)
print('outputting to', args.output)

df_posts = pd.read_csv(args.csv_file_name)

def getAllType(username, contentType):
    n_posts = 500
    with urllib.request.urlopen(f"https://api.pushshift.io/reddit/search/{contentType}/?author={username}&sort=asc&size={n_posts}") as url:
        data = json.loads(url.read().decode())
        data = data['data']
    df_content = pd.DataFrame.from_dict(json_normalize(data), orient='columns')
    if len(df_content) == 0:
        return df_content
    created_utc_last = df_content.tail(1)['created_utc'].copy().reset_index()
    created_utc_last = created_utc_last['created_utc'][0]
    while len(data) > 0:
        with urllib.request.urlopen(f"https://api.pushshift.io/reddit/search/{contentType}/?author={username}&sort=asc&size={n_posts}&after={created_utc_last}") as url:
            data = json.loads(url.read().decode())
            data = data['data']
        df_content = df_content.append(pd.DataFrame.from_dict(json_normalize(data), orient='columns'))
        created_utc_last = df_content.tail(1)['created_utc'].copy().reset_index()
        created_utc_last = created_utc_last['created_utc'][0]
    return df_content

t0 = time.process_time()

# Build subreddit mappings
sub_mappings = {}

for username in set(df_posts['author']):
    with open(args.output, 'r') as fp:
        sub_mappings = json.load(fp)
    try:
        if username not in sub_mappings:
            df_comment = getAllType(username, 'comment').reset_index()
            df_submission = getAllType(username, 'submission').reset_index()
            df_comment_set = list(set(df_comment['subreddit'])) if len(df_comment) > 0 else []
            df_submission_set = list(set(df_submission['subreddit'])) if len(df_submission) > 0 else []
            sub_mappings[username] = {
                'comment': df_comment_set,
                'submission': df_submission_set
            }
    except:
        print('failed to read', username)
    finally:
        # save what we have so far if the last read attempt failed
        with open(args.output, 'w') as fp:
            json.dump(sub_mappings, fp)

#     print('got subreddits for', username)

print('PROCESS TIME ELAPSED (s)', time.process_time() - t0)

with open(args.output, 'w') as fp:
    json.dump(sub_mappings, fp)
