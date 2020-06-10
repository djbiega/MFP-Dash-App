import psycopg2
from config import config

def create_tables():
    '''Create initial tables for the PostgreSQL database'''
    commands = [
        '''
        CREATE TABLE users (
            user_id serial PRIMARY KEY,
            mfp_username text
        )
        ''',
        '''
        CREATE TABLE groups (
            group_id SERIAL PRIMARY KEY,
            group_name text
        )
        ''',
        '''
        CREATE TABLE group_users (
            id SERIAL PRIMARY KEY,
            mfp_username text,
            group_name text
        )
        ''',
        '''
        CREATE TABLE nutrition (
            id SERIAL PRIMARY KEY,
            mfp_username text,
            entry_date DATE,
            item text,
            calories int,
            fat int,
            polyunsaturated_fat int,
            saturated_fat int,
            monounsaturated_fat int,
            trans_fat int,
            cholesterol int,
            sodium int,
            potassium int,
            carbohydrates int,
            fiber int,
            sugar int,
            protein int,
            vitamin_a int,
            vitamin_c int,
            calcium int,
            iron int
        )
        '''
    ]
    conn=None
    try:
        # Load config parameters from database.ini
        params = config()
        # Connect to the PostgreSQL server
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
        # create table one by one
        for command in commands:
            cur.execute(command)
        # commit the changes
        conn.commit()
        # close communication with the PostgreSQL database server
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


if __name__ == '__main__':
    create_tables()