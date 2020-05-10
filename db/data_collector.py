import psycopg2
from config import config

def create_tables():
    '''Create initial tables for the PostgreSQL database'''
    commands = [
        '''
        CREATE TABLE users (
            user_id SERIAL PRIMARY KEY,
            mfp_username VARCHAR(50) NOT NULL
        )
        ''',
        '''
        CREATE TABLE groups (
            group_id SERIAL PRIMARY KEY,
            group_name VARCHAR(50)
        )
        ''',
        '''
        CREATE TABLE group_users (
            id SERIAL,
            user_id INTEGER NOT NULL,
            group_id INTEGER NOT NULL,
            PRIMARY KEY (id, user_id, group_id),
            FOREIGN KEY (user_id)
                REFERENCES users (user_id)
                ON UPDATE CASCADE ON DELETE CASCADE,
            FOREIGN KEY (group_id)
                REFERENCES groups (group_id)
                ON UPDATE CASCADE ON DELETE CASCADE
        )
        ''',
        '''
        CREATE TABLE nutrition (
            id SERIAL,
            user_id INTEGER NOT NULL,
            PRIMARY KEY (id, user_id),
            FOREIGN KEY (user_id)
                REFERENCES users (user_id)
                ON UPDATE CASCADE ON DELETE CASCADE,
            entry_date DATE,
            item VARCHAR(250) NOT NULL,
            protein INTEGER NOT NULL,
            carbs INTEGER NOT NULL,
            fat INTEGER NOT NULL,
            fiber INTEGER NOT NULL,
            sugar INTEGER NOT NULL,
            calories INTEGER NOT NULL
        )
        ''']
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

# def insert_user(user):
#     '''Populate all tables with the scraped username data from usernames.json'''
#     sql = '''INSERT INTO users (mfp_username)
#             VALUES (%s);'''
#     conn = None
#     id = None
#     try:
#         # Load config parameters from database.ini
#         params = config()
#         # Connect to the PostgreSQL server
#         conn = psycopg2.connect(**params)
#         # Create new cursor
#         cur = conn.cursor()
#         # Insert the user
#         cur.execute(sql, (user,))
#         # commit the changes
#         conn.commit()
#         # close communication with the PostgreSQL database server
#         cur.close()

if __name__ == '__main__':
    create_tables()