import requests
from datetime import date, timedelta, datetime
from multiprocessing import Pool
from bs4 import BeautifulSoup


def check_username(username):
    '''Check if the input username exists and has Diary Settings set to Public'''
    url = 'https://www.myfitnesspal.com/food/diary/' + username + '?date=' + datetime.strftime(date.today(), '%Y-%m-%d')
    s = requests.Session()
    html = BeautifulSoup(s.get(url).content, 'html.parser')
    try:
        div = html.find('div', attrs={'class': 'block-1', 'p': None}).contents
        text = [x for x in div][1].text.strip()
        if text == 'This user maintains a private diary.' or text == 'Username ' + username + ' can not be found.':
            return False
    except:
        return True
    # Complete and implement this function

class MFP_User:
    '''
    Represents any MyFitnessPal User and their associated nutrition data
    '''
    def __init__(self, username, 
                date_start=datetime.strftime(date.today(), '%Y-%m-%d'), 
                date_end=datetime.strftime(date.today()-timedelta(6), '%Y-%m-%d')):
        self.username = username
        self.data = {'Dates': {}}
    
        date_start = datetime.strptime(date_start, '%Y-%m-%d').date()
        date_end = datetime.strptime(date_end, '%Y-%m-%d').date()
        assert (date_start - date_end).days >= 0, 'date_end must be before date_start'
        
        url_list = ['https://www.myfitnesspal.com/food/diary/' + self.username + 
                '?date=' + (date_start-timedelta(days=date)).isoformat() 
                for date in range(((date_start-date_end).days)+1)]
        date_list = [(date_start - timedelta(days=day)).isoformat() \
            for day in range(((date_start-date_end).days)+1)]
        
        s = requests.Session()
        [self._scrape_urls(s, url, date_list.pop()) for url in url_list[::-1]]

    def _scrape_urls(self, s, url, date):
        '''
        Scrapes My Fitness Pal Website on all dates specified in the range of the input
        start date and end date
        '''
        self.diary_html = BeautifulSoup(s.get(url).content, 'html.parser')
        self.data['Dates'][date] = {
                                'Items': self.get_nutrition(),
                                'Total Calories': sum([int(self.nutrition[item]['Calories'])\
                                    for item in self.nutrition.keys()]),
                                'Total Protein': sum([int(self.nutrition[item]['Protein'])\
                                    for item in self.nutrition.keys()]),
                                'Total Carbohydrates': sum([int(self.nutrition[item]['Carbohydrates'])\
                                    for item in self.nutrition.keys()]),
                                'Total Fat': sum([int(self.nutrition[item]['Fat'])\
                                    for item in self.nutrition.keys()]),
                                'Total Fiber': sum([int(self.nutrition[item]['Fiber'])\
                                    for item in self.nutrition.keys()]),
                                'Total Sugar': sum([int(self.nutrition[item]['Sugar'])\
                                     for item in self.nutrition.keys()])
                                    }   


    # Dictionary of all the logged nutrition data for each food in the diary on the input date
    def get_nutrition(self):
        '''Returns a dictionary of all of the nutrition values'''
        self.nutrition = {  food: {
                                calories: cal_value, 
                                protein: protein_value, 
                                carbs: carb_value, 
                                fats: fat_value, 
                                fiber: fiber_value, 
                                sugar: sugar_value
                                }   
                            for food, calories, cal_value, protein, protein_value, carbs, carb_value, 
                                fats, fat_value, fiber, fiber_value, sugar, sugar_value in zip(
                                self.foods(), 
                                ['Calories']*len(self.items), self.calories(), 
                                ['Protein']*len(self.items), self.protein(),
                                ['Carbohydrates']*len(self.items), self.carbs(),
                                ['Fat']*len(self.items), self.fat(),
                                ['Fiber']*len(self.items), self.fiber(),
                                ['Sugar']*len(self.items), self.sugar())
                         }
        return self.nutrition

    def get_nutrition_html(self):
        '''Returns the relevant html which contains all of the nutritional values'''
        return self.diary_html.find_all('tr', attrs={'class': None})

    def foods(self):
        '''Returns list of all foods'''
        tr_tags = self.get_nutrition_html()
        food_tags = [food.find_all('td', attrs={'class': 'first alt'}) for food in tr_tags]
        self.items = [item.contents[0].strip() for i in range(0,len(food_tags)) for item in food_tags[i]]
        return self.items

    def macros(self):
        '''Return all nutrition values for Protein, Carbs, and Fat for all foods'''
        tr_tags = self.get_nutrition_html()
        macro_tags=[tag.find_all('span', attrs={'class': 'macro-value'}) for tag in tr_tags]
        macros = [item.contents[0].replace(',','') for j in range(0,len(macro_tags)) for item in macro_tags[j]]
        return macros

    def protein(self):
        '''Return protein for all foods'''
        return self.macros()[2::3]

    def carbs(self):
        '''Return carbs for all foods'''
        return self.macros()[::3]

    def fat(self):
        '''Return fat for all foods'''
        return self.macros()[1::3]

    def non_macros(self):
        '''Return all nutrition values for everything but Protein, Carbs, and Fat for all foods'''
        tr_tags = self.get_nutrition_html()
        non_macro_tags = [tag.find_all('td', attrs={'class': None}) for tag in tr_tags]
        non_macros = [item.contents[0].replace(',','') for j in range(0,len(non_macro_tags)) for item in non_macro_tags[j]]
        return non_macros

    def calories(self):
        '''Return calories for all foods'''
        return self.non_macros()[::6]

    def fiber(self):
        '''Return fiber for all foods'''
        return self.non_macros()[4::6]

    def sugar(self):
        '''Return sugar for all foods'''
        return self.non_macros()[5::6]


if __name__ == '__main__':
    import json
    import time
    start = time.time()
    user = MFP_User('djbiega2')
    print('User:' + user.username)
    print(json.dumps(user.data, indent=1))
    print('=========================================')
    print('Done!\n')  
    print('It took', time.time()-start, 'seconds.')