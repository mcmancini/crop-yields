'''
setup.py
========

Author: Mattia Mancini
Created: 01-November-2022
--------------------------

Set the data, databases and routines needed to run the WOFOST crop yield model 
in GB based on predictions of daily weather from the CHESS-SCAPE UKCP18 1km gridded 
data from CEH and the Met-Office.
This setup consists of the following steps:
    1 - Download and store the CHESS-SCAPE data
    2 - Rechunk the CHESS-SCAPE data downloaded in 1.
    3 - Create and postgreSQL database with the required tables and associated
        relationships
    4 - Load parcel and farm data to the relevant table in the SQL database
    5 - Process and load topographic data to the relevant table in the SQL database
    6 - Process and load soil data to the relevant table in the SQL database
'''
import argparse

def section1():
    print("Running section 1")

def section2():
    print("Running section 2")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--section', help='Which section to run', choices=['section1', 'section2'])
    args = parser.parse_args()

    if args.section == 'section1':
        section1()
    elif args.section == 'section2':
        section2()