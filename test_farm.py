from cropyields.FarmManager import Farm
import psycopg2
from cropyields import db_parameters
  
# List of parcel codes
conn = psycopg2.connect(user=db_parameters['db_user'],
                        password=db_parameters['db_password'], 
                        database=db_parameters['db_name'], 
                        host='127.0.0.1', 
                        port= '5432')
conn.autocommit = True
cur = conn.cursor()
sql = '''
    SELECT parcel_id, nat_grid_ref 
    FROM parcels;
    '''
cur.execute(sql)
t = cur.fetchall()
parcel_list = [row[0] for row in t]
parcel_os_code = [row[1] for row in t]
if conn is not None:
    conn.close()

a = Farm(parcel_os_code[1])
print(a)
a.plot()

