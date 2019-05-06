import pandas as pd
import requests
import json
import datetime
import os
import zipfile
from ftplib import FTP

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
    ftp = FTP("ftp-cdc.dwd.de")
    ftp.login()
    ftp.cwd("/pub/CDC/observations_germany/climate/daily/kl/recent/")
    filename = "tageswerte_KL_03126_akt.zip"
    tempfile = 'Data/md.zip'
    with open(tempfile, 'wb') as f:
        ftp.retrbinary("RETR " + filename ,f.write)
    ftp.quit()
    with zipfile.ZipFile(tempfile, 'r') as zip: 
        zip.extractall()
    for _, _, files in os.walk('Data/'):
        for name in files:
            if 'produkt_klima_tag' in name:
                dat = pd.read_csv(name, sep=';', skipinitialspace=True)
                return dat
    return None

def has_data_yesterday():
    yesterday = (datetime.date.today()- datetime.timedelta(days = 1)).strftime('%Y%m%d')
    for _, _, files in os.walk('Data/'):
        for name in files:
            if yesterday in name:
                return True
    return False

#print(has_data_yesterday())

def get_current_temperature(city_id, user_key):
    result = requests.get("http://api.openweathermap.org/data/2.5/weather?id="+str(city_id)+"&units=metric&APPID="+user_key)
    return result.json()['main']['temp']
