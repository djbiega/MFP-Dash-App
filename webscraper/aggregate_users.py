import sys
import os
import json

def concatenate_json(data_dir):
    '''
    Concatenate and return all json files following the pattern "public_group*" into
    a single list of dictionaries formatted as json.

    parameters:
        data_dir (str) -- Input path to the top level directory where all the scraped json
            files have been output.

    Expected directory structure to search:
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

    # Get a list of all subdirectories within the top-level directory
    dirlist = []
    for filename in os.listdir(data_dir):
        if os.path.isdir(os.path.join(data_dir,filename)):
            dirlist.append(filename)

    # only search the json files containing usernames with public diary settings
    result = []
    for folder in dirlist:
        folder_path = (os.path.join(data_dir, folder))
        for filename in os.listdir(folder_path):
            if 'public' in filename:
                with open(os.path.join(folder_path, filename), 'r', encoding='UTF8') as f:
                    data = json.load(f)
                    result.append(data)
    return result

def to_json(json_list):
    '''
    Dump list of dicts into a single json file
    
    parameters:
        json_list (list) -- A list of dictionaries formatted as json.
    '''

    with open(os.path.join(data_dir, 'usernames.json'), 'w') as fout:
        json.dump(json_list, fout, indent=4)

if __name__=='__main__':
    abs_path = os.path.abspath(os.path.dirname(__file__))
    data_dir = os.path.join(os.path.split(abs_path)[0], 'data')
    result = concatenate_json(data_dir)
    to_json(result)