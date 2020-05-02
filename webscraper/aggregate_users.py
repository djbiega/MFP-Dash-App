import sys
import os
import json

def concatenate_json(data_dir):
    '''
    Concatenate all json files following the pattern "public_group*" into
    a single list
    '''
    dirlist = [filename for filename in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir,filename))]
    result = list()

    for folder in dirlist:
        sub_dir = (os.path.join(data_dir, folder))
        for filename in os.listdir(sub_dir):
            if 'public' in filename:
                with open(os.path.join(sub_dir, filename), 'r', encoding='UTF8') as f:
                    data = json.load(f)
                    result.append(data)
    return result

def to_json(json_list):
    '''Dump list of dicts into a single json file'''
    with open(os.path.join(data_dir, 'usernames.json'), 'w') as fout:
        for dic in json_list:
            json.dump(dic, fout, indent=4)
            fout.write('\n')

if __name__=='__main__':
    abs_path = os.path.abspath(os.path.dirname(__file__))
    data_dir = os.path.join(os.path.split(abs_path)[0], 'data')
    result = concatenate_json(data_dir)
    to_json(result)