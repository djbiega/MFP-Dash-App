import psycopg2
import json
import sys

from os import path
from datetime import date, datetime

module_path = path.abspath(path.join(path.dirname( __file__ ), '..'))
sys.path.append(module_path)

from config import config
from webscraper.user_data import MFP_User

def get_data():
    '''Get and return scraped data'''
    basepath = path.dirname(__file__)
    filepath = path.abspath(path.join(basepath, "..", "data/usernames.json"))
    f = open(filepath, "r")
    data = json.load(f)
    return data

def get_groups(data):
    '''Return Groups from input data'''
    groups = [group['Group'] for group in data]
    return groups

def get_users(data):
    '''Return Users from input data'''
    users = [user for group in data for user in group['Members']]
    return users    
    
def get_users_groups(data):
    '''Returns all groups each user belongs to in a dict'''
    user_groups = {}
    for d in data:
        members = d["Members"]
        for m in members:
            user_groups.setdefault(m, []).append(d["Group"])    
    return user_groups

def execute_sql(sql, *argv):
    '''Execute the input SQL statement on the postgreSQL database'''
    conn = None
    id = None
    try:
        # Load config parameters from database.ini
        params = config()

        # Connect to the PostgreSQL server
        conn = psycopg2.connect(**params)

        # Create new cursor
        cur = conn.cursor()

        # Execute the SQL command
        if len(argv)>0:
            for arg in argv:
                [cur.execute(sql, (i,)) for i in arg] 
        else:
            cur.execute(sql)

        # commit the changes
        conn.commit()

        # close communication with the PostgreSQL database server
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def insert_users(users):
    '''Populate all tables with the scraped username data from usernames.json'''
    sql = '''
    INSERT INTO users (mfp_username)
    VALUES (%s);
    '''
    execute_sql(sql, users)

def insert_groups(groups):
    '''Populate all tables with the scraped group data from usernames.json'''
    sql = '''
    INSERT INTO groups (group_name)
    VALUES (%s);
    '''
    execute_sql(sql, groups)

def insert_group_user_relations(user_groups):
    '''Create relation between groups and users'''
    conn = None
    id = None
    # Load config parameters from database.ini
    params = config()
    # Connect to the PostgreSQL server
    conn = psycopg2.connect(**params)
    # Create new cursor
    cur = conn.cursor()

    for user, groups in user_groups.items():
        for group in groups:
            sql = '''
            INSERT INTO group_users (mfp_username, group_name)
            VALUES (%s, %s);
            '''        
            try:
                cur.execute(sql, (user, group))
            except (Exception, psycopg2.DatabaseError) as error:
                print(error)

    # commit the changes
    conn.commit()
    # close communication with the PostgreSQL database server
    conn.close()
    cur.close()

def insert_nutrition(users):
    '''
    Collect all nutrition data from every user over the last 5 years
    and insert into the database
    '''
    conn = None
    id = None
    # Load config parameters from database.ini
    params = config()
    # Connect to the PostgreSQL server
    conn = psycopg2.connect(**params)
    # Create new cursor
    cur = conn.cursor()
    today = datetime.strftime(date.today(), '%Y-%m-%d')
    
    for user in users:
        mfp_user = MFP_User(user, '2016-01-01', today)

        sql = '''
        INSERT INTO nutrition (mfp_username, entry_date, item, \
            calories, protein, carbohydrates, fat, fiber, sugar, saturated_fat, \
            polyunsaturated_fat, monounsaturated_fat, trans_fat, cholesterol, \
            sodium, potassium, vitamin_a, vitamin_c, calcium, iron)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        '''        
        try:
            for day in mfp_user.data['Dates'].keys():
                for item in mfp_user.data['Dates'][day]['Items'].keys():
                    cals = mfp_user.data['Dates'][day]['Items'][item]['Calories']
                    protein = mfp_user.data['Dates'][day]['Items'][item]['Protein']
                    carbs = mfp_user.data['Dates'][day]['Items'][item]['Carbohydrates']
                    fat = mfp_user.data['Dates'][day]['Items'][item]['Fat']
                    fiber = mfp_user.data['Dates'][day]['Items'][item]['Fiber']
                    sugar = mfp_user.data['Dates'][day]['Items'][item]['Sugar']
                    sat_fat = mfp_user.data['Dates'][day]['Items'][item]['Saturated Fat']
                    polyunsat_fat = mfp_user.data['Dates'][day]['Items'][item]['Polyunsaturated Fat']
                    monounsat_fat = mfp_user.data['Dates'][day]['Items'][item]['Monounsaturated Fat']
                    trans_fat = mfp_user.data['Dates'][day]['Items'][item]['Trans Fat']
                    cholesterol = mfp_user.data['Dates'][day]['Items'][item]['Cholesterol']
                    sodium = mfp_user.data['Dates'][day]['Items'][item]['Sodium']
                    potassium = mfp_user.data['Dates'][day]['Items'][item]['Potassium']
                    vitamin_a = mfp_user.data['Dates'][day]['Items'][item]['Vitamin A']
                    vitamin_c = mfp_user.data['Dates'][day]['Items'][item]['Vitamin C']
                    calcium = mfp_user.data['Dates'][day]['Items'][item]['Calcium']
                    iron = mfp_user.data['Dates'][day]['Items'][item]['Iron']

                    cur.execute(sql, (mfp_user.username, day, item, cals, protein, carbs, fat, fiber, sugar,
                        sat_fat, polyunsat_fat, monounsat_fat, trans_fat, cholesterol, sodium, potassium,
                        vitamin_a, vitamin_c, calcium, iron))
                    # commit the changes
                    conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)

    # close communication with the PostgreSQL database server
    conn.close()
    cur.close()

if __name__=='__main__':
    # Get Data
    data = get_data()
    groups = get_groups(data)
    users = get_users(data)
    user_groups = get_users_groups(data)

    # Insert data into database
    insert_users(users)
    insert_groups(groups)
    insert_group_user_relations(user_groups)
    insert_nutrition(users)