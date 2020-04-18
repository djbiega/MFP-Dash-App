import sys

# add your project directory to the sys.path
project_home = u'/home/djbiega/MFP-Dash'

if project_home not in sys.path:
    sys.path = [project_home] + sys.path

from app import server as application

if __name__ == '__main__':
    application.run()