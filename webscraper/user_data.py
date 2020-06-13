import requests
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta, datetime
from bs4 import BeautifulSoup


class MFP_User:
    '''
    Represents any MyFitnessPal User and their associated nutrition data
    '''
    def __init__(self, username, 
                date_start=datetime.strftime(date.today()-timedelta(6), '%Y-%m-%d'), 
                date_end=datetime.strftime(date.today(), '%Y-%m-%d')):
        self.username = username
        self.data = {'Dates': {}}
    
        date_start = datetime.strptime(date_start, '%Y-%m-%d').date()
        date_end = datetime.strptime(date_end, '%Y-%m-%d').date()
        assert (date_end - date_start).days >= 0, 'date_end must be before date_start'
        print('Scraping %s for %s through %s' % (self.username, date_start, date_end))       
        date_list = self._get_dates_to_check(date_start, date_end)
        url_list = self._get_urls(date_list)
        s = requests.Session()

        if (date_end - date_start).days > 30:
            date_list = self._filter_dates(url_list)
            url_list = self._filter_urls(date_list)
            
        with ThreadPoolExecutor(max_workers=1) as executor:
            processes = [executor.submit(self._scrape_urls(s, url, date_list.pop())) for url in url_list[::-1]]

        # return all dates without entires as empty dictionaries
        delta = date_end-date_start
        for i in range(delta.days+1):
            d = datetime.strftime((date_start+timedelta(days=i)), '%Y-%m-%d')
            if d not in self.data['Dates'].keys():
                self.data['Dates'][d] = {}

    def _get_dates_to_check(self, date_start, date_end):
        '''
        Return a list of all dates that need to be checked as a list of strings.
        The returned list will be determined by the output. If the range of dates
        extend past 1 month, the list will only return the 5th, 15th, and 25th
        day for every month within the range. These dates are to serve as checks
        to see if the user has actively logged nutrition data in these months.

        If the start date and end date are within the same month, a list of all
        dates between them will be returned
        '''
        date_list = []
        if date_start.year != date_end.year:
            years = [y for y in (date_start.year, date_end.year)]
            months = [m for m in range(1,13)]
            days = [5, 15, 25]
            for y in years:
                for m in months:
                    for d in days:
                        date_list.append(str(y) + "-" + str(m) + "-" + str(d))
        elif date_start.month != date_end.month:
            months = [m for m in range(1,13)]
            days = [5, 15, 25]
            for m in months:
                for d in days:
                    date_list.append(str(date_start.year) + "-" + str(m) + "-" + str(d))
        else:
            days = [d for d in range(date_start.day, date_end.day)]
            for d in days:
                date_list.append(str(date_start.year) + "-" + str(date_start.month) + "-" + str(d))
        return date_list

    def _get_urls(self, date_list):
        '''Get a list of all urls'''
        url_list = []
        for date in date_list:
            url = ('https://www.myfitnesspal.com/food/diary/' + self.username + '?date=' + date)
            url_list.append(url)
        return url_list

    def _filter_dates(self, url_list):
        '''
        Refine the list of urls such that if the user has logged any data
        on the 5th, 15th, or 25th of any month, then every day of that
        month will be scraped.
        '''
        s = requests.Session()
        new_date_list = []
        for url in url_list:
            date = url.split('=')[1]
            self._scrape_urls(s, url, date)
            if self.data['Dates'][date]['Items']:
                y = date.split('-')[0]
                m = date.split('-')[1]
                [new_date_list.append(y+'-'+m+'-'+str(d)) for d in range(1,29) if d not in [5, 15, 25]]
            else:
                del self.data['Dates'][date]

        new_date_list = set(list(new_date_list))
        return new_date_list

    def _filter_urls(self, new_date_list):
        return self._get_urls(new_date_list)

    def _scrape_urls(self, s, url, date):
        '''
        Scrapes My Fitness Pal Website on all dates specified in the range of the input
        start date and end date
        '''
        self.diary_html = BeautifulSoup(s.get(url).content, 'html.parser')
        self.data['Dates'][date] = {'Items': self.get_nutrition()}   

    # Dictionary of all the logged nutrition data for each food in the diary on the input date
    def get_nutrition(self):
        '''Returns a dictionary of all of the nutrition values'''
        self._get_nutrients_available()
        self.nutrition = {  food: {
                                calories: cal_value,
                                protein: protein_value,
                                carb: carb_value,
                                fat: fat_value,
                                fiber: fiber_value,
                                sugar: sugar_value,
                                sat_fat: sat_fat_value,
                                polyunsat_fat: polyunsat_fat_value,
                                monounsat_fat: monounsat_fat_value,
                                trans_fat: trans_fat_value,
                                cholesterol: cholesterol_value,
                                sodium: sodium_value,
                                potassium: potassium_value,
                                vit_a: vit_a_value,
                                vit_c: vit_c_value,
                                calcium: calcium_value,
                                iron: iron_value
                            }   
                            for food, calories, cal_value, protein, protein_value, carb, carb_value, 
                                fat, fat_value, fiber, fiber_value, sugar, sugar_value,
                                sat_fat, sat_fat_value, polyunsat_fat, polyunsat_fat_value,
                                monounsat_fat, monounsat_fat_value, trans_fat, trans_fat_value,
                                cholesterol, cholesterol_value, sodium, sodium_value, 
                                potassium, potassium_value, vit_a, vit_a_value, vit_c, vit_c_value,
                                calcium, calcium_value, iron, iron_value in zip(
                                self.foods(), 
                                ['Calories']*len(self.items), self.get_non_macro_values("Calories"), 
                                ['Protein']*len(self.items), self.get_macro_values("Protein"),
                                ['Carbohydrates']*len(self.items), self.get_macro_values("Carbs"),
                                ['Fat']*len(self.items), self.get_macro_values("Fat"),
                                ['Fiber']*len(self.items), self.get_non_macro_values("Fiber"),
                                ['Sugar']*len(self.items), self.get_non_macro_values("Sugar"),
                                ['Saturated Fat']*len(self.items), self.get_non_macro_values("Sat Fat"),
                                ['Polyunsaturated Fat']*len(self.items), self.get_non_macro_values("Ply Fat"),
                                ['Monounsaturated Fat']*len(self.items), self.get_non_macro_values("Mon Fat"),
                                ['Trans Fat']*len(self.items), self.get_non_macro_values("Trn Fat"),
                                ['Cholesterol']*len(self.items), self.get_non_macro_values("Chol"),
                                ['Sodium']*len(self.items), self.get_non_macro_values("Sodium"),
                                ['Potassium']*len(self.items), self.get_non_macro_values("Potass."),
                                ['Vitamin A']*len(self.items), self.get_non_macro_values("Vit A"),
                                ['Vitamin C']*len(self.items), self.get_non_macro_values("Vit C"),
                                ['Calcium']*len(self.items), self.get_non_macro_values("Calcium"),
                                ['Iron']*len(self.items), self.get_non_macro_values("Iron")
                                )
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

    def _get_nutrients_available(self):
        '''
        Nutrients as defined by MyFitnessPal html:
            Calories, Fat, Carbs, Protein, Fiber, Sugar, Sat Fat, Ply Fat, Mon Fat,
            Trn Fat, Chol, Sodium, Potass., Vit A, Vit C, Calcium, Iron
        '''
        self._nutrients = [td.contents[0].strip() for td in self.diary_html.find_all('td', attrs={"class": "alt nutrient-column"})][:6]

    def macros(self):
        '''Return all nutrition values for Protein, Carbs, and Fat for all foods'''
        tr_tags = self.get_nutrition_html()
        macro_tags=[tag.find_all('span', attrs={'class': 'macro-value'}) for tag in tr_tags]
        macros = [item.contents[0].replace(',','') for j in range(0,len(macro_tags)) for item in macro_tags[j]]
        return macros

    def non_macros(self):
        '''Return all nutrition values for everything but Protein, Carbs, and Fat for all foods'''
        tr_tags = self.get_nutrition_html()
        non_macro_tags = [tag.find_all('td', attrs={'class': None}) for tag in tr_tags]
        non_macros = [item.contents[0].replace(',','') for j in range(0,len(non_macro_tags)) for item in non_macro_tags[j]]
        return [val for val in non_macros if val != '\n']

    def get_macro_values(self, nutrient):
        '''Return the associated nutrient values for the input nutrient (protein/fat/carbs)'''
        macro_order = [macro for macro in self._nutrients if macro in ['Protein', 'Fat', 'Carbs']]
        if nutrient in self._nutrients and nutrient == macro_order[0]:
            return self.macros()[::3]
        elif nutrient in self._nutrients and nutrient == macro_order[1]:
            return self.macros()[1::3]
        elif nutrient in self._nutrients and nutrient == macro_order[2]:
            return self.macros()[2::3]
        else:
            return [None]*len(self.items)

    def get_non_macro_values(self, nutrient):
        '''Return the associated nutrient values for the input nutrient (non-macro/calorie)'''
        non_macro_order = [non_macro for non_macro in self._nutrients if non_macro not in ['Protein', 'Fat', 'Carbs']]
        if nutrient in self._nutrients and nutrient == non_macro_order[0]:
            return self.non_macros()[::3]
        elif nutrient in self._nutrients and nutrient == non_macro_order[1]:
            return self.non_macros()[1::3]
        elif nutrient in self._nutrients and nutrient == non_macro_order[2]:
            return self.non_macros()[2::3]
        else:
            return [None]*len(self.items)

if __name__ == '__main__':
    import json
    import time
    start = time.time()
    user = MFP_User('djbiega2', '2019-06-28')
    print('User:' + user.username)
    print(json.dumps(user.data, indent=1))
    print('=========================================')
    print('Done!\n')  
    print('It took', time.time()-start, 'seconds.')