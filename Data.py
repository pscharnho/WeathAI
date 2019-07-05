import pandas as pd
import numpy as np
import requests
import json
import datetime
import os
import zipfile
from ftplib import FTP
import sqlite3
from sqlite3 import Error
#from sklearn.utils import shuffle
import sklearn


def create_connection(db_file):
    """ create a database connection to a SQLite database """
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)
    finally:
        conn.close()


def initialize_db(db_file):
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute(""" CREATE TABLE IF NOT EXISTS Magdeburg (
                                       date INTEGER PRIMARY KEY,
                                       min_temp REAL,
                                       max_temp REAL
                                   ); """)
    c.execute(""" CREATE TABLE IF NOT EXISTS Berlin (
                                       date INTEGER PRIMARY KEY,
                                       min_temp REAL,
                                       max_temp REAL
                                   ); """)
    c.execute(""" CREATE TABLE IF NOT EXISTS Muenchen (
                                       date INTEGER PRIMARY KEY,
                                       min_temp REAL,
                                       max_temp REAL
                                   ); """)
    c.execute(""" CREATE TABLE IF NOT EXISTS Hamburg (
                                       date INTEGER PRIMARY KEY,
                                       min_temp REAL,
                                       max_temp REAL
                                   ); """)
    c.execute(""" CREATE TABLE IF NOT EXISTS Lausanne (
                                       date INTEGER PRIMARY KEY,
                                       min_temp REAL,
                                       max_temp REAL
                                   ); """)
    conn.close()


def get_historical_data_ncei():
    base = "https://www.ncei.noaa.gov/access/services/data/v1"
    dataset = "daily-summaries"
    station_magdeburg = "GME00102252"
    start_date = "2012-01-01"
    end_date = datetime.date.today().strftime('%Y-%m-%d')  # "2019-04-20"
    units = "metric"
    formate = "json"

    # "https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries&stations=GME00102252&startDate=2012-01-01&endDate=2019-04-20&units=metric&format=json"
    request_string = base + "?dataset=" + dataset + "&stations=" + station_magdeburg + "&startDate=" + \
        start_date + "&endDate=" + end_date + "&units=" + units + "&format=" + formate

    result = requests.get(request_string)

    df_md = pd.DataFrame(result.json())

    df_md.to_csv('Data/hist_ncei.csv')

    df_md.PRCP = df_md.PRCP.astype(float).fillna(0.0)
    df_md.TMAX = df_md.TMAX.astype(float).fillna(0.0)
    df_md.TMIN = df_md.TMIN.astype(float).fillna(0.0)
    df_md.SNWD = df_md.SNWD.astype(float).fillna(0.0)

    print("Maximum Precipitation: {}".format(df_md.PRCP.max()))
    print("Maximum Temperature: {}".format(df_md.TMAX.max()))
    print("Minimum Temperature: {}".format(df_md.TMIN.min()))
    return df_md


def get_new_data(city):
    if has_data_yesterday_today(city):
        for _, _, files in os.walk('Data/'+city+'/'):
            for name in files:
                if 'produkt_klima_tag' in name:
                    print(name)
                    dat = pd.read_csv('Data/'+city+'/'+name,
                                      sep=';', skipinitialspace=True)
                    return dat
    else:
        for _, _, files in os.walk('Data/'+city+'/'):
            for name in files:
                os.remove('Data/'+city+'/'+name)
        ###########
        # Try
        ###########
        ftp = FTP("opendata.dwd.de")  # ftp://ftp-cdc.dwd.de/pup/CDC
        ftp.login()
        ftp.cwd(
            "/climate_environment/CDC/observations_germany/climate/daily/kl/recent/")  # /
        if city == 'Magdeburg':
            city_id = '3126'
        elif city == 'Berlin':
            city_id = '0433'
        elif city == 'Muenchen':
            city_id = '3379'
        elif city == 'Hamburg':
            city_id = '1981'
        else:
            return None
        filename = 'tageswerte_KL_0'+city_id+'_akt.zip'
        tempfile = 'Data/'+city+'.zip'
        with open(tempfile, 'wb') as f:
            ftp.retrbinary("RETR " + filename, f.write)
        ftp.quit()
        with zipfile.ZipFile(tempfile, 'r') as zip:
            zip.extractall(path='Data/'+city+'/')
        for _, _, files in os.walk('Data/'+city+'/'):
            for name in files:
                if 'produkt_klima_tag' in name:
                    print(name)
                    dat = pd.read_csv('Data/'+city+'/'+name,
                                      sep=';', skipinitialspace=True)
                    return dat
    return None


def insert_temps(db_file, table_name, date, mintemp, maxtemp, conn=None):
    if conn == None:
        conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute(" INSERT INTO " + table_name +
              "(date, min_temp, max_temp) VALUES(?,?,?) ", (date, mintemp, maxtemp))
    conn.commit()
    # conn.close()


def has_data_yesterday_today(city):
    yesterday = (datetime.date.today() -
                 datetime.timedelta(days=1)).strftime('%Y%m%d')
    today = datetime.date.today().strftime('%Y%m%d')
    for _, _, files in os.walk('Data/'+city):
        for name in files:
            if yesterday in name or today in name:
                return True
    return False


def update_db(db_file, table_name):
    if not has_data_yesterday_today(table_name):
        df = get_new_data(table_name)
        conn = sqlite3.connect(db_file)
        c = conn.cursor()
        c.execute(" SELECT MAX(date) FROM " + table_name+";")
        max_date = c.fetchone()[0]
        if not isinstance(max_date, int):
            update_db_step(df, conn, table_name)
        elif df.loc[df.MESS_DATUM == max_date].empty:
            update_db_step(df, conn, table_name)
        else:
            df_slice = df.loc[df.MESS_DATUM > max_date]
            update_db_step(df_slice, conn, table_name)


def update_db_step(df, conn, table_name):
    for _, row in df.iterrows():
        insert_temps(None, table_name,
                     row['MESS_DATUM'], row['TNK'], row['TXK'], conn=conn)
    conn.close()


def get_training_test_data(db_file, table_name):
        ###########
        # Try
        ###########
    update_db(db_file, table_name)
    conn = sqlite3.connect(db_file)
    df = pd.read_sql_query("SELECT * FROM " + table_name, conn)
    collected_max = []
    collected_min = []
    targets_max = []
    targets_min = []
    for i in range(df['date'].idxmax()-9):
        collected_max.append(df['max_temp'][i:i+10].values)
        collected_min.append(df['min_temp'][i:i+10].values)
        targets_max.append(df['max_temp'][i+10])
        targets_min.append(df['min_temp'][i+10])

    collected_max, targets_max = sklearn.utils.shuffle(
        collected_max, targets_max)
    collected_min, targets_min = sklearn.utils.shuffle(
        collected_min, targets_min)

    return (collected_min, targets_min, collected_max, targets_max)


def get_current_temperature(city_id, user_key):
        ###########
        # Try
        ###########
    result = requests.get("http://api.openweathermap.org/data/2.5/weather?id=" +
                          str(city_id)+"&units=metric&APPID="+user_key)
    return result.json()['main']['temp']
