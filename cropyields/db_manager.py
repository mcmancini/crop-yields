from cropyields import db_parameters, dem_parameters
import psycopg2
import numpy as np
from psycopg2.extensions import register_adapter, AsIs
psycopg2.extensions.register_adapter(np.int64, AsIs)
psycopg2.extensions.register_adapter(np.int32, AsIs)
psycopg2.extensions.register_adapter(np.float32, AsIs)
from cropyields.utils import osgrid2lonlat, nearest

# Create a database
def create_db():
    '''Create database with name \'db_name\''''
    
    db_name = db_parameters['db_name']
    db_user = db_parameters['db_user']
    db_password = db_parameters['db_password']

    try:
        # establishing the connection
        conn = psycopg2.connect(user=db_user,
                                password=db_password, 
                                host='127.0.0.1', 
                                port= '5432')
        conn.autocommit = True
        
        # check if postgis extension exists
        ext_check = 'SELECT * FROM pg_extension WHERE extname=\'postgis\';'

        # Create a cursor
        cur = conn.cursor()
        # Execute sql statement
        cur.execute(ext_check)      
        if cur.fetchall() is None:
            sql = (f'CREATE DATABASE {db_name};',
                    'CREATE EXTENSION postgis;')
            for command in sql:
                cur.execute(command)
        else:
            sql = (f'CREATE DATABASE {db_name};')
            cur.execute(sql)     
        
        # close communication with the PostgreSQL database server
        cur.close()
        print(f'Database \'{db_name}\' created successfully!')    
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

# Drop a database
def drop_db():
    '''Drop database with name \'db_name\''''

    db_name = db_parameters['db_name']
    db_user = db_parameters['db_user']
    db_password = db_parameters['db_password']

    sql = f'DROP DATABASE {db_name};'    
    try:
        conn = psycopg2.connect(user=db_user,
                                password=db_password, 
                                host='127.0.0.1', 
                                port= '5432')
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(sql)      
        cur.close()
        print(f'Database \'{db_name}\' deleted successfully!')
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


# Create tables and relations
def create_db_tables():
    '''Create structure of the database with tables and relations'''
    
    db_name = db_parameters['db_name']
    db_user = db_parameters['db_user']
    db_password = db_parameters['db_password']

    sql_parcels = '''
        CREATE TABLE IF NOT EXISTS parcels (
        parcel_id BIGINT UNIQUE PRIMARY KEY,
        farm_id BIGINT NOT NULL,
        nat_grid_ref VARCHAR(12) NOT NULL
        );
    ''' 
    sql_topography = '''
        CREATE TABLE IF NOT EXISTS topography (
        parcel_id BIGINT UNIQUE PRIMARY KEY,
        elevation DOUBLE PRECISION NOT NULL,
        slope DOUBLE PRECISION NOT NULL,
        aspect VARCHAR(2) NOT NULL
        );
    '''  
    sql_soil = '''
        CREATE TABLE IF NOT EXISTS soil (
        parcel_id BIGINT UNIQUE PRIMARY KEY,
        bdod DOUBLE PRECISION,
        cec DOUBLE PRECISION,
        cfvo DOUBLE PRECISION,
        clay DOUBLE PRECISION,
        nitrogen DOUBLE PRECISION,
        phh2o DOUBLE PRECISION,
        sand DOUBLE PRECISION,
        silt DOUBLE PRECISION,
        soc DOUBLE PRECISION,
        ocs DOUBLE PRECISION,
        ocd DOUBLE PRECISION
        );
    '''  
    sql_dict = {'parcels': sql_parcels,
                'topography': sql_topography,
                'soil': sql_soil}
    try:
        conn = psycopg2.connect(user=db_user,
                                password=db_password, 
                                database=db_name, 
                                host='127.0.0.1', 
                                port= '5432')
        conn.autocommit = True
        for sql in sql_dict:
            cur = conn.cursor()
            cur.execute(sql_dict[sql])
            cur.close()
            print(f'Table \'{db_name}.{sql}\' successfully created')
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

# drop selected tables
def drop_table(table_name):
    '''Drop table with name \'table_name\''''

    db_name = db_parameters['db_name']
    db_user = db_parameters['db_user']
    db_password = db_parameters['db_password']

    # Preparing query to create a database
    sql = f'DROP TABLE IF EXISTS {table_name} CASCADE;'
    try:
        conn = psycopg2.connect(user=db_user,
                                password=db_password, 
                                database=db_name, 
                                host='127.0.0.1', 
                                port= '5432')
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(sql)
        print(f'Table \'{table_name}\' deleted successfully!')
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

# Fill database with data
def add_to_table(table_name, records):
    '''
    Add records contained in \'records\' to the sql database table
    \'table_name\'. This function makes also sure that no data is 
    duplicated. The \'records\' argument is a Numpy record array, 
    which can be created from a Pandas dataframe using the 
    \'DataFrame.to_records()\' method.
    '''
    pass

def populate_table(table_name, records):
    """
    Fill empty table \'table_name\' with records in \'records\'.
    The \'records\' argument is a Numpy record array, 
    which can be created from a Pandas dataframe using the 
    \'DataFrame.to_records()\' method.
    This produces lists of tuples. Each tuple in \'records\'
    represents the values to insert in the colums of the 
    table \'table_name\' in the database. 
    N.B.: if the table already contains data, use the 
    \'add_to_table\' function.
    """
    
    db_name = db_parameters['db_name']
    db_user = db_parameters['db_user']
    db_password = db_parameters['db_password']
    conn = None    
    try:
        conn = psycopg2.connect(user=db_user,
                                password=db_password, 
                                database=db_name, 
                                host='127.0.0.1', 
                                port= '5432')
        cur = conn.cursor()
        cur.execute(f"Select * FROM {table_name} LIMIT 1")
        if cur.fetchall() is None:
            raise SystemExit(f'Table \'{table_name}\' already contains data. Use the function \'add_to_table\' instead!')
        colnames = tuple([desc[0] for desc in cur.description])
        n_cols = len(colnames)
        linestring = '%s' * n_cols
        n_char = 2
        char_f = str(tuple([linestring[i:i+n_char] for i in range(0, len(linestring), n_char)])).replace("'", "")
        char_cols = str(colnames).replace("'", "")
        sql = f"INSERT INTO {table_name} {char_cols} VALUES {char_f}"
        cur.executemany(sql, records)
        conn.commit()
        print(cur.rowcount, f"Records inserted successfully into \'{table_name}\' table")
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

# Query the DTM database based on longitude and latitude to add
# elevation, slope and aspect data to the parcel data
def get_dtm_values(parcel_OS_code):
    '''
    Query the DTM database based on longitude and latitude to add
    elevation, slope and aspect data to the parcel data in the 
    farm yield model. The output of this function is a dictionary
    with the following keys: 'x', 'y', 'elevation', 'slope', 'aspect'
    '''
    db_name = dem_parameters['db_name']
    db_user = dem_parameters['db_user']
    db_password = dem_parameters['db_password']

    conn = None

    # retrieve lon, lat from parcel_OS_code and create a bounding box to 
    # find the closest 50m grid cell in the DEM
    lon, lat = osgrid2lonlat(parcel_OS_code)
    lon_min, lon_max, lat_min, lat_max = lon-50, lon+50, lat-50, lat+50
    try:
        conn = psycopg2.connect(user=db_user,
                                password=db_password, 
                                database=db_name, 
                                host='127.0.0.1', 
                                port= '5432')
        conn.autocommit = True
        cur = conn.cursor()
        sql = '''
            SELECT terrain.x, terrain.y, terrain.val, terrain.slope, terrain.aspect
            FROM dtm.dtm_slope_aspect AS terrain
            WHERE terrain.x BETWEEN {lon_min} AND {lon_max}
            AND terrain.y BETWEEN {lat_min} AND {lat_max};
            '''.format(lon_min=lon_min, lon_max=lon_max, lat_min=lat_min, lat_max=lat_max)
        cur.execute(sql)
        t = cur.fetchall()
        lon_lst = [x[0] for x in t]
        lat_lst = [x[1] for x in t]
        a, b = nearest(lon, lon_lst), nearest(lat, lat_lst)
        ind = [i for i, x in enumerate(t) if x[0:2] == (a, b)]
        dtm_vals = t[ind[0]]
        dict_keys = ['x', 'y', 'elevation', 'slope', 'aspect']
        dtm_dict = {key:val for (key, val) in zip(dict_keys, dtm_vals)}
        print(f'Retrieving topographic data for OS cell \'{parcel_OS_code}\'')
        return dtm_dict
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

# Get topographic data from database for any parcel
def get_parcel_data(parcel_OS_code, col_list):
    '''
    Retrieve from the NEV SQL database data associated with
    a user-defined parcel. 
    Input arguments are the ID of the parcel of interest (OS code)
    and a list containing the names of the columns to retrieve
    '''
    db_name = db_parameters['db_name']
    db_user = db_parameters['db_user']
    db_password = db_parameters['db_password']
    conn = None    
    try:
        conn = psycopg2.connect(user=db_user,
                                password=db_password, 
                                database=db_name, 
                                host='127.0.0.1', 
                                port= '5432')
        conn.autocommit = True
        cur = conn.cursor()
        to_get = str(col_list).replace('[\'', '').replace('\']', '')
        sql = '''
            SELECT parcel_ID, nat_grid_ref, {to_get} 
            FROM parcels
            WHERE nat_grid_ref = '{parcel_OS_code}';
            '''.format(parcel_OS_code=parcel_OS_code, to_get=to_get.replace("'", ""))
        cur.execute(sql)
        t = cur.fetchall()[0]

        cols = [x for x in col_list]
        dict_keys = ['parcel_ID', 'nat_grid_ref'] + cols
        parcel_dict = {key:val for (key, val) in zip(dict_keys, t)}
        return parcel_dict
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()