from cropyields import db_parameters, dem_parameters, whsd_parameters
import psycopg2
import numpy as np
from psycopg2.extensions import register_adapter, AsIs
psycopg2.extensions.register_adapter(np.int64, AsIs)
psycopg2.extensions.register_adapter(np.int32, AsIs)
psycopg2.extensions.register_adapter(np.float32, AsIs)
from cropyields.utils import osgrid2lonlat, nearest
from sqlalchemy import create_engine
from shapely.geometry import Point
import pandas as pd
import geopandas as gpd

# Create a database
def create_db():
    '''Create database with name \'db_name\''''
    
    db_name = db_parameters['db_name']
    db_user = db_parameters['db_user']
    db_password = db_parameters['db_password']

    try:
        # Establish a connection to the PostgreSQL server without specifying the database
        conn = psycopg2.connect(user=db_user,
                                password=db_password, 
                                host='127.0.0.1', 
                                port='5432')
        conn.autocommit = True

        # Create a cursor to execute SQL statements
        cur = conn.cursor()

        # Check if the target database exists
        cur.execute(f"SELECT datname FROM pg_catalog.pg_database WHERE datname = '{db_name}';")
        exists = cur.fetchone()

        if not exists:
            # Create the target database
            cur.execute(f'CREATE DATABASE {db_name};')
            print(f'Database \'{db_name}\' created successfully!')

        # Close the cursor and the connection to the PostgreSQL server
        cur.close()
        conn.close()

        # Connect to the target database
        conn = psycopg2.connect(database=db_name,
                                user=db_user,
                                password=db_password,
                                host='127.0.0.1',
                                port='5432')
        conn.autocommit = True

        # Create a cursor to execute SQL statements in the target database
        cur = conn.cursor()

        # Check if the postGIS extension exists in the target database
        cur.execute('SELECT * FROM pg_extension WHERE extname=\'postgis\';')
        exists = cur.fetchone()

        if not exists:
            # Enable the postGIS extension in the target database
            cur.execute('CREATE EXTENSION postgis;')
            print('postGIS extension enabled successfully!')

        # Close the cursor and the connection to the target database
        cur.close()
        conn.close()
        
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

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
        nat_grid_ref VARCHAR(12) NOT NULL,
        geometry geometry(Polygon, 4326)
        );
    ''' 
    sql_topography = '''
        CREATE TABLE IF NOT EXISTS topography (
        parcel_id BIGINT UNIQUE,
        elevation DOUBLE PRECISION NOT NULL,
        slope DOUBLE PRECISION NOT NULL,
        aspect VARCHAR(2) NOT NULL,
        FOREIGN KEY (parcel_id) REFERENCES parcels(parcel_id)
        );
    '''  
    # sql_soil = '''
    #     CREATE TABLE IF NOT EXISTS soil (
    #     parcel_id BIGINT UNIQUE PRIMARY KEY,
    #     bdod DOUBLE PRECISION,
    #     cec DOUBLE PRECISION,
    #     cfvo DOUBLE PRECISION,
    #     clay DOUBLE PRECISION,
    #     nitrogen DOUBLE PRECISION,
    #     phh2o DOUBLE PRECISION,
    #     sand DOUBLE PRECISION,
    #     silt DOUBLE PRECISION,
    #     soc DOUBLE PRECISION,
    #     ocs DOUBLE PRECISION,
    #     ocd DOUBLE PRECISION
    #     );
    # '''  
    sql_dict = {'parcels': sql_parcels,
                'topography': sql_topography}
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

    INPUT ARGUMENTS     
    :param parcel_OS_code: the OS Grid Code of the parcel for which
           data is required.
    :param col_list: list of column names to query (i.e., the data needed)
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
            SELECT parcels.parcel_id, parcels.nat_grid_ref, topography.{to_get}
            FROM parcels
            INNER JOIN topography ON parcels.parcel_id = topography.parcel_id
            WHERE parcels.nat_grid_ref = '{parcel_OS_code}';
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

# Get WHSD data from database for any parcel
def get_whsd_data(parcel_OS_code, vars):
    '''
    Retrieve from the SEER NEV database soil data on the 2km SEER grid
    from the World Harmonized Soil Database

    INPUT ARGUMENTS     
    :param parcel_OS_code: the OS Grid Code of the parcel for which
           data is required.
    :param vars: list of variables to query (i.e., the data needed)
           Default variables required are % Sand, % silt and % clay
    '''
    db_name = whsd_parameters['db_name']
    db_user = whsd_parameters['db_user']
    db_password = whsd_parameters['db_password']
    db_schema = whsd_parameters['schema']
    conn = None    
    try:
        conn = psycopg2.connect(user=db_user,
                                password=db_password, 
                                database=db_name, 
                                host='127.0.0.1', 
                                port= '5432')
        conn.autocommit = True
        cur = conn.cursor()
        seer_soilvars = ['adj' + x for x in vars]
        to_get = str(seer_soilvars).replace('[\'', '').replace('\']', '')
        x, y = osgrid2lonlat(parcel_OS_code)
        sql = '''
            SELECT {to_get}
            FROM {db_schema}.seer_soil
            JOIN {db_schema}.seer_regions ON seer_soil.new2kid = seer_regions.new2kid
            ORDER BY SQRT(POWER(seer_regions.xmn + 1000 - {x}, 2) + POWER(seer_regions.ymn + 1000 - {y}, 2))
            LIMIT 1;
            '''.format(to_get=to_get.replace("'", ""), db_schema=db_schema, x=x, y=y)
        cur.execute(sql)
        t = cur.fetchall()[0]
        t = [int(x) for x in t]
        parcel_dict = {key:val for (key, val) in zip(vars, t)}
        return parcel_dict
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def find_farm(OSGrid_code):
    """
    Find farm managing the parcel at 'OSGrid code' location
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
        conn.autocommit = True
        cur = conn.cursor()

        # Create a Shapely Point object from the lon-lat pair
        lon, lat = osgrid2lonlat(OSGrid_code, EPSG=4326)
        point = Point(lon, lat)

        # Use ST_Contains to find the parcel that contains the point
        query = """
            SELECT p.parcel_id, p.farm_id
            FROM parcels p
            WHERE ST_Contains(p.geometry, ST_GeomFromText(%s, 4326))
        """

        # Execute the query with the lon-lat pair as a parameter
        cur.execute(query, (point.wkt,))
        parcel, farm = cur.fetchall()[0]
        return {'parcel': parcel, 'farm':farm}
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def get_farm_data(identifier):
    """
    Retrieve farm data from the database.
    
    :param identifier: either a parcel centroid in the OSGrid code form, or a farm 
           identifier (farm_id) in the RPA database or derived. If a centroid OSGrid code
           is passed, then the farm identifier of the parcel referring to that location 
           is retrieved. NB: farm IDs are integers, OSGrid codes are strings starting
           with two letters (e.g. SX)
    
    Returns all parcels belonging to the farm.
    """
    if not isinstance(identifier, int):
        farm = find_farm(identifier)['farm']
    else:
        farm = identifier

    engine = None    
    try:
        database_url = f"postgresql://{db_parameters['db_user']}:{db_parameters['db_password']}@localhost/{db_parameters['db_name']}"
        engine = create_engine(database_url)
        sql = f"SELECT parcel_id, farm_id, nat_grid_ref, ST_AsText(geometry) as geometry FROM parcels;"
        df = pd.read_sql(sql, engine)
    
        # Convert the WKT representation to a geospatial object
        df['geometry'] = gpd.GeoSeries.from_wkt(df['geometry'])
        df = gpd.GeoDataFrame(df, geometry='geometry')
        return df
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if engine is not None:
            engine.dispose()