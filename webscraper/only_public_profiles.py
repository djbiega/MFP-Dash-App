import os
import sys
import requests
import json
from datetime import date, datetime
from multiprocessing import Pool, cpu_count
from bs4 import BeautifulSoup

sys.path.append("../")
from constants import *



def check_username(username):
    '''
    Check if the input username exists and has Diary Settings set to Public
        
    parameters:
        username (str) -- The input username being searched
    '''
    url = 'https://www.myfitnesspal.com/food/diary/%s/?date=%s' % (username, TODAY)
    s = requests.Session()
    if s.get(url).status_code != 200:
        return False

    html = BeautifulSoup(s.get(url).content, 'html.parser')
    # The block-1 tag is only rendered when the username does not exist or the account is private
    div = html.find('div', attrs={'class': "block-1"})
    if not div:
        return True
    else:
        return False

def is_public(username):
    '''
    Intermediary function used for multiprocessing

    parameters:
        username (str) -- The input username being searched
    '''
    print('Checking: %s' % username)
    if check_username(username):
        return username
    else:
        return None

def only_public_members():
    '''
    Search through json files containing scraped MyFitnessPal usernames
    and discard any which do not have their diary settings set to public.

    Expected directory structure to search:
    /webscraper/
        |--/only_public_profiles.py
    /data/
        |--/page_1/
            |--group_1.json
            |--group_2.json
            ...
        |--/page_2/
            |--group_1.json
            |--group_2.json
            ...
    '''
    json_files = {}
    for root, dirs, files in os.walk(os.join(os.getcwd(), '../data')): 
        json_files[root] = files
    # Remove Key on top level directory
    del json_files[os.join(os.getcwd(), 'data')]
    
    public_json = {}
    s = requests.Session()
    for page_dir, json_page_list in json_files.items():
        for json_page in json_page_list:
            with open(os.join(page_dir, json_page)) as f:
                json_data = json.load(f)
                print(os.join(page_dir, json_page))

                # Multiprocessing to speed this up
                with Pool(cpu_count()-1) as p:
                    public_profiles = p.map(is_public, json_data['Members'])
                p.close()
                p.join()
                
                # Remove all None values (Private Accounts)
                public_profiles = list(filter(None, public_profiles))

                # Put the data in an expected format                
                group = json_data['Group']
                
                public_json[group] = {
                    'Group': group,
                    'URL': json_data['URL'],
                    'Member_Count': json_data['Member_Count'],
                    'Members': public_profiles
                }

                to_json(page_dir, json_page, public_json[group])

def to_json(page_dir, json_page, data):
    '''
    Dump input group data into a .json file
    
    parameters:
        page_dir (str) -- Path to the directory
        json_page (str) -- Filename
        data (dict) -- Dict to dump into the json file
    '''
    with open(os.join(page_dir, 'public_%s' % (json_page)), 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == '__main__':
    import time
    start = time.time()
    check_username('dfa')
    end = time.time()
    print('DONE!\n')
    print('Your function took %s seconds to run' % (end-start))
