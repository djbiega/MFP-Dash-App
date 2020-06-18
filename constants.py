from datetime import timedelta, datetime, date

DB_ONLY_COLS = ['mfp_username', 'entry_date', 'id']
START_SCRAPE_DATE='2016-01-01'
YESTERDAY = datetime.strftime((date.today()-timedelta(1)), '%Y-%m-%d')
TODAY = datetime.strftime(date.today(), '%Y-%m-%d')