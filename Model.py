from Data import get_training_test_data, update_db
import torch
import torch.utils.data
import datetime
import requests
import json
import pickle
import sklearn.linear_model
import sqlite3


class TempLowDataset(torch.utils.data.Dataset):
    def __init__(self, df):
        super().__init__()


def train_model(database, city, model):
    (X_min, y_min, X_max, y_max) = get_training_test_data(database, city)
    if model == "SGDReg":
        mod_min = sklearn.linear_model.SGDRegressor()
        mod_max = sklearn.linear_model.SGDRegressor()
    if model == "Ridge":
        mod_min = sklearn.linear_model.Ridge()
        mod_max = sklearn.linear_model.Ridge()
    mod_min.fit(X_min, y_min)
    mod_max.fit(X_max, y_max)
    filename_min = 'Models/'+model+city+'min.sav'
    pickle.dump(mod_min, open(filename_min, 'wb'))
    filename_max = 'Models/'+model+city+'max.sav'
    pickle.dump(mod_max, open(filename_max, 'wb'))

        


def get_model(city):
    pass



#def get_forecast(city, sample):
#    model = get_model(city)
#    return model(sample)

def get_forecast(city, model, city_id, user_key):
    if model == "OWM" and city_id != None:
        result = requests.get("http://api.openweathermap.org/data/2.5/forecast?id="+str(city_id)+"&units=metric&APPID="+user_key)
        temps_max = [d['main']['temp_max'] for d in result.json()['list']]
        temps_min = [d['main']['temp_min'] for d in result.json()['list']]
        x = [d['dt_txt'] for d in result.json()['list']]
        return (x,temps_max,temps_min)
    else:
        tomorrow = (datetime.date.today() + datetime.timedelta(days = 1)).strftime('%A')
        ttomorrow = (datetime.date.today() + datetime.timedelta(days = 2)).strftime('%A')
        tttomorrow = (datetime.date.today() + datetime.timedelta(days = 3)).strftime('%A')
        x_data = [tomorrow, ttomorrow, tttomorrow]

        filename_min = 'Models/'+model+city+'min.sav'
        filename_max = 'Models/'+model+city+'max.sav'
        model_min = pickle.load(open(filename_min, 'rb'))
        model_max = pickle.load(open(filename_max, 'rb'))

        if city == 'Magdeburg':
            update_db('Data/weather_data.db', city)
            conn = sqlite3.connect('Data/weather_data.db')
            c = conn.cursor()
            c.execute(" SELECT min_temp, max_temp FROM "+ city +" ORDER BY date DESC LIMIT 10;")
            temps = c.fetchall()
            temps_min = [[temp[0] for temp in reversed(temps)]]
            temps_max = [[temp[1] for temp in reversed(temps)]]
            res_min = []
            res_max = []
            for i in range(3):
                min_pred = model_min.predict(temps_min)
                max_pred = model_max.predict(temps_max)
                res_min.append(min_pred.item())
                res_max.append(max_pred.item())
                temps_min[0].append(min_pred[0])
                temps_min = [temps_min[0][1:]]
                temps_max[0].append(max_pred[0])
                temps_max = [temps_max[0][1:]]

            return (x_data, res_max,res_min)
        elif city == 'Lausanne':
            return (x_data, [25.4,23.7,27.5],[15.3,14.9,16.6])
        else:
            return (x_data, [0,0,0],[0,0,0])