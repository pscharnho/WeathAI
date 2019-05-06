from Data import get_historical_data_ncei
import torch
import torch.utils.data
import datetime
import requests
import json


class TempLowDataset(torch.utils.data.Dataset):
    def __init__(self, df):
        super().__init__()
        


def generate_training_samples():
    df = get_historical_data_ncei()


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

        if city == 'Magdeburg':
            return (x_data, [21.1,24.5,19.2],[12.9,14.4,8.7])
        elif city == 'Lausanne':
            return (x_data, [25.4,23.7,27.5],[15.3,14.9,16.6])
        else:
            return (x_data, [0,0,0],[0,0,0])