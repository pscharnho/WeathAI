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
    c.execute(""" CREATE TABLE IF NOT EXISTS magdeburg (
                                       date INTEGER PRIMARY KEY,
                                       min_temp REAL,
                                       max_temp REAL
                                   ); """)
    c.execute(""" CREATE TABLE IF NOT EXISTS lausanne (
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
    end_date = datetime.date.today().strftime('%Y-%m-%d')#"2019-04-20"
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


def get_new_data():
    if has_data_yesterday_today():
        for _, _, files in os.walk('Data/md/'):
            for name in files:
                if 'produkt_klima_tag' in name:
                    print(name)
                    dat = pd.read_csv('Data/md/'+name, sep=';', skipinitialspace=True)
                    return dat
    else:
        for _, _, files in os.walk('Data/md/'):
            for name in files:
                os.remove('Data/md/'+name)
        ftp = FTP("ftp-cdc.dwd.de")
        ftp.login()
        ftp.cwd("/pub/CDC/observations_germany/climate/daily/kl/recent/")
        filename = "tageswerte_KL_03126_akt.zip"
        tempfile = 'Data/md.zip'
        with open(tempfile, 'wb') as f:
            ftp.retrbinary("RETR " + filename ,f.write)
        ftp.quit()
        with zipfile.ZipFile(tempfile, 'r') as zip: 
            zip.extractall(path="Data/md/")
        for _, _, files in os.walk('Data/md/'):
            for name in files:
                if 'produkt_klima_tag' in name:
                    print(name)
                    dat = pd.read_csv('Data/md/'+name, sep=';', skipinitialspace=True)
                    return dat
    return None


def insert_temps(db_file, dbname, date, mintemp, maxtemp, conn=None):
    if conn == None:
        conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute(" INSERT INTO " + dbname + "(date, min_temp, max_temp) VALUES(?,?,?) ", (date, mintemp, maxtemp))
    conn.commit()
    #conn.close()

def has_data_yesterday_today():
    yesterday = (datetime.date.today()- datetime.timedelta(days = 1)).strftime('%Y%m%d')
    today = datetime.date.today().strftime('%Y%m%d')
    for _, _, files in os.walk('Data/md'):
        for name in files:
            if yesterday in name or today in name:
                return True
    return False


def update_db(db_file, db_name):
    #if not has_data_yesterday_today():
    df = get_new_data()
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute(" SELECT MAX(date) FROM "+ db_name+";")
    max_date = c.fetchone()[0]
    if not isinstance(max_date, int):
        update_db_step(df, conn, db_name)
    elif df.loc[df.MESS_DATUM == max_date].empty:
        update_db_step(df, conn, db_name)
    else:
        df_slice = df.loc[df.MESS_DATUM > max_date]
        update_db_step(df_slice, conn, db_name)


def update_db_step(df, conn, db_name):
    for _, row in df.iterrows():
        insert_temps(None, db_name, row['MESS_DATUM'], row['TXK'], row['TNK'], conn=conn)
    conn.close()



def get_training_test_data(db_file, db_name):
    conn = sqlite3.connect(db_file)
    df = pd.read_sql_query("SELECT * FROM " + db_name, conn)


def get_current_temperature(city_id, user_key):
    result = requests.get("http://api.openweathermap.org/data/2.5/weather?id="+str(city_id)+"&units=metric&APPID="+user_key)
    return result.json()['main']['temp']
