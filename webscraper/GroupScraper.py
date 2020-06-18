import requests
import json
import re
import os
from multiprocessing import Pool, cpu_count
from bs4 import BeautifulSoup

class GroupScraper:

    def __init__(self):
        '''
        Collect usernames from the most popular groups in MyFitnessPal as shown on
        https://community.myfitnesspal.com/en/groups/browse/popular

        instance variables:
            pages (int) -- The number of top (X) number of pages scraped from the MyFitnessPal forums. Default: 10
            url_list (list of str) -- list of the urls for the top (X) pages to scrape in the forums
            data (dict) -- dictionary with the following key-value structure:
                'MyFitnessPal Group Name': {'Group': value, 'URL': value, 'Member_count: value, 'Members': value}                    
        '''
        self._s = requests.Session()
        self.pages = 10
        self.url_list=[]
        for pg in range(1,self.pages+1):
            self.url_list = 'https://community.myfitnesspal.com/en/groups/browse/popular?Page=p%s?filter=members' % spg
        self._make_data_dirs()
        self.data = {}
        self._get_groups()

    def _make_data_dirs(self):
        '''Make directories to store each page all the groups from each forum page'''
        for i in range(1, self.pages+1):
            try:
                os.makedirs('../data/page_%s' % i)
            except FileExistsError:
                pass

    def _get_groups(self):
        '''
        Parses out all usernames from the groups within url_list. 
        The function will maintain a dictionary 'data' which contains 
        the Group Name, URL to the group page, Number of Members, and List of all members.
        Each group will be output to its own respective .json file.
        '''
        page_no = 0        
        for url in self.url_list:
            page_no+=1
            page_html = BeautifulSoup(self._s.get(url).content, 'html.parser')
            group_ids = page_html.find_all('li', attrs={'id': re.compile('Group_\d+')})
            group_no = 1

            for g in group_ids:
                group_type = g.find_all('span', attrs={'class': re.compile('^MItem$')})[-1].contents[0].strip()
                if group_type != 'Private Group':
                    group = g.find_all('a', attrs={'href': re.compile('^//')})[-1].contents[0].strip()
                    link = 'https:' + g.find_all('a', attrs={'href': re.compile('^//'), 'class':None})[0]['href']
                    
                    members_link = link.rsplit('/', 1)[0] + '/members/' + link.rsplit('/', 1)[1]
                    members_count = g.find_all('span', attrs={'class': 'MItem Hidden DiscussionCountNumber Number MItem-Count'})[0].contents[0].strip()
                    members = self._get_members(group, members_count, members_link)
                    
                    # Store the data in a json-friendly format
                    self.data[group] = {
                        'Group': group,
                        'URL': members_link, 
                        'Member_Count': members_count, 
                        'Members': members
                    }

                    # Dump the group to its own json file
                    self._to_json(group, page_no, group_no)
                    group_no+=1
            
    def _get_members(self, group, members_count, members_link):
        '''
        Return all usernames from the input group

        inputs: 
            group (str): MyFitnessPal Group
            members_count (str): Number of members in the MyFitnessPal Group
            members_link (str): URL of the Page 1 of the list of members in a group

        outputs: 
            member_list (list): list of strings of all members in the group
        '''
        page_count = int(members_count) // 30
        page_list = []
        for pg in range(1, page_count+1):
            url = '%s/p/%s/?filter=members' % (members_link, pg)
            page_list.append(url)

        # Multiprocessing
        with Pool(cpu_count()-1) as p:
            member_list = p.map(self._get_members_on_page, page_list)
        p.close()
        p.join()

        # Flatten list of lists of members from each page into a single list of members
        member_list = [member for page_list in member_list for member in page_list]
        return member_list

    def _get_members_on_page(self, url):
        '''
        Function to get all group members on the input url

        parameters: 
            url (string) -- Group Member URL to scrape
        '''
        print(f'Scraping %s' % url)
        if self._s.get(url).status_code == 200:
            page_html = BeautifulSoup(self._s.get(url).content, 'html.parser')
            user_ids = page_html.find_all('a', attrs={'class': 'Title', 'href': re.compile('\/en\/profile\/usercard\/\d+')})
            member_list = [user_ids[i].contents[0].strip() for i in range(len(user_ids))]
        else:
            pass
        return member_list

    def _to_json(self, group, page_no, group_no):
        '''
        Dump input group data into a .json file
        inputs:
            group (Dict): Dictionary of MyFitnessPal Groups
            group_no (int): Index term used for tracking groups
        '''
        with open('../data/page_%s/group_%s.json' % (page_no, group_no), 'w') as f:
            json.dump(self.data[group], f, indent=4)


if __name__ == '__main__':
    import time
    start = time.time()
    scraper = GroupScraper()
    end = time.time()
    print('DONE!\n')
    print('Your function took %s seconds to run' % (end-start))