import os
import requests
import json
from datetime import date, datetime
from os.path import join
from multiprocessing import Pool, cpu_count
from bs4 import BeautifulSoup



def check_username(username):
    '''Check if the input username exists and has Diary Settings set to Public'''
    if not username:
        return False
    url = 'https://www.myfitnesspal.com/food/diary/' + username + '?date=' + datetime.strftime(date.today(), '%Y-%m-%d')
    s = requests.Session()
    if s.get(url).status_code == 200:
        try:
            html = BeautifulSoup(s.get(url).content, 'html.parser')
            div = html.find('div', attrs={'id': 'main', 'p': None}).contents
            text = [x for x in div][1].text.strip()

            if text == 'This user maintains a private diary.' or text == 'Username ' + username + ' can not be found.':
                return False
            else:
                return True
        except:
            return False
    else: 
        return False

def is_public(username):
    print('Checking: %s' % username)
    if check_username(username):
        return username
    else:
        return None

def only_public_members():
    '''
    Expected directory structure to search:
    ~/webscraper/
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
    for root, dirs, files in os.walk(join(os.getcwd(), '../data')): 
        json_files[root] = files
    # Remove Key on top level directory
    del json_files[join(os.getcwd(), 'data')]
    
    public_json = {}
    s = requests.Session()
    for page_dir, json_page_list in json_files.items():
        for json_page in json_page_list:
            with open(join(page_dir, json_page)) as f:
                json_data = json.load(f)
                print(join(page_dir, json_page))

                with Pool(cpu_count()-1) as p:
                    public_profiles = p.map(is_public, json_data['Members'])
                p.close()
                p.join()
                
                # Remove all None values (Private Accounts)
                public_profiles = list(filter(None, public_profiles))
                
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
    inputs:
        page_dir (str): Path to the directory
        json_page (str): Filename
        data (dict): Dict to dump into the json file
    '''
    with open(join(page_dir, 'public_%s' % (json_page)), 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == '__main__':
    import time
    start = time.time()
    check_username('djbiega2')
    end = time.time()
    print('DONE!\n')
    print('Your function took %s seconds to run' % (end-start))
