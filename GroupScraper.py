import requests
import json
import re
from math import ceil
from multiprocessing import Pool, cpu_count
from bs4 import BeautifulSoup

class GroupScraper:

    def __init__(self):
        '''
        Collect usernames from the most popular groups in MyFitnessPal as shown on
        https://community.myfitnesspal.com/en/groups/browse/popular
        '''
        self._s = requests.Session()
        self.pages = 10
        self.url_list = ['https://community.myfitnesspal.com/en/groups/browse/popular?Page=p' + \
            str(i) + '?filter=members' for i in range(self.pages)]
        self.data = {}
        self._get_groups()

    def _get_groups(self):
        '''
        Parses out all usernames from the groups within url_list. 
        The function will maintain a dictionary 'data' which contains 
        the Group Name, Number of Members, and List of all members.
        Each group will be output to its own respective .json file.
        '''
        for url in self.url_list:
            page_html = BeautifulSoup(self._s.get(url).content, 'html.parser')
            group_ids = page_html.find_all('li', attrs={'id': re.compile('Group_\d+')})
            start = timeit.timeit()
            scraper = GroupScraper()
            end = timeit.timeit()
            for group_no, g in enumerate(group_ids):
                group_type = g.find_all('span', attrs={'class': re.compile('^MItem$')})[-1].contents[0].strip()
                if group_type != 'Private Group':
                    group = g.find_all('a', attrs={'href': re.compile('^//')})[-1].contents[0].strip()
                    link = 'https:' + g.find_all('a', attrs={'href': re.compile('^//'), 'class':None})[0]['href']
                    
                    members_link = link.rsplit('/', 1)[0] + '/members/' + link.rsplit('/', 1)[1]
                    members_count = g.find_all('span', attrs={'class': 'MItem Hidden DiscussionCountNumber Number MItem-Count'})[0].contents[0].strip()
                    members = self._get_members(group, members_count, members_link)
                    
                    # Store the data in a json-friendly format
                    self.data[group] = {
                        'URL': members_link, 
                        'Member_Count': members_count, 
                        'Members': members
                    }

                    # Dump the group to its own json file
                    self._to_json(group, group_no)
            print('DONE!\n')
            print('Your function took %s seconds to run' % (start-end))
                
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
        page_count = ceil(int(members_count) / 30)
        # page_list = [members_link +'/p' + str(pg) + '?filter=members' for pg in range(1, page_count)]
        page_list = [members_link +'/p' + str(pg) + '?filter=members' for pg in range(1, 3)]

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
        inputs: 
            url (string): Group Member URL to scrape
        '''
        print(f'Scraping %s' % url)
        if self._s.get(url).status_code == 200:
            page_html = BeautifulSoup(self._s.get(url).content, 'html.parser')
            user_ids = page_html.find_all('a', attrs={'class': 'Title', 'href': re.compile('\/en\/profile\/usercard\/\d+')})
            member_list = [user_ids[i].contents[0].strip() for i in range(len(user_ids))]
        else:
            pass
        return member_list

    def _to_json(self, group, group_no):
        '''
        Dump input group data into a .json file
        inputs:
            group (Dict): Dictionary of MyFitnessPal Groups
            group_no (int): Index term used for tracking groups
        '''
        with open('group_' + str(group_no) +'.json', 'w') as f:
            json.dump(self.data[group], f, indent=4)


if __name__ == '__main__':
    import timeit
    start = timeit.timeit()
    scraper = GroupScraper()
    end = timeit.timeit()
    print('DONE!\n')
    print('Your function took %s seconds to run' % (start-end))