import requests
import datetime
import pytz
import math
from urllib.parse import urlencode
from dateutil import parser
from os import error
from django.shortcuts import render
from timezonefinder import TimezoneFinder

# Create your views here.
tf = TimezoneFinder()

def index(request):

    #form inputs
    end_point = request.POST.get('end_point')
    start_point = request.POST.get('start_point')
    sun = request.POST.get('sun')

    #if a trip was attempted
    if end_point:
        route = getRoute(start_point, end_point)
        #if error
        if route == 'error':
            context = {'status': 'fail'}
            #invalid request
            return render(request, 'display/display.html',context)
        #else plan trip
        travel = getTravelTime(route['time'])
        mapURL = getMapURL(route['start_lat'], route['start_lng'], route['dest_lat'], route['dest_lng'])
        golden_hour = getGoldenHour(route['dest_lng'], route['dest_lat'], sun)
        itenirary = getItinerary(golden_hour['utc'], route['time'], route['start_lng'], route['start_lat'])

        #if doesn't have city name, ignore weather
        if route['city'] != '':
            weather = getWeather(route['city'], sun)
        else:
            weather = {
                'temperature': '',
                'description': '',
                'icon': ''
            }

        context = {
            'status': 'success',
            'sun': sun,
            'golden_hour': golden_hour['string'],
            'temperature': weather['temperature'],
            'description': weather['description'],
            'icon': weather['icon'],
            'mapURL': mapURL,
            'city': route['city'] or end_point.capitalize(),
            'leave': itenirary,
            'travel': travel
        }

        return render(request, 'display/display.html',context)
    
    return render(request, 'display/display.html')

def getWeather(end_point, sun):

    #get api information
    url = 'https://community-open-weather-map.p.rapidapi.com/forecast'

    querystring = {
        'q':end_point,
        'lang':'en',
        'units':'imperial'
        }
    
    headers = {
        'x-rapidapi-key': '779f6795f5msh9d7a1e22add6089p1a5c79jsn2d6263f76e85',
        'x-rapidapi-host': 'community-open-weather-map.p.rapidapi.com'
        }

    response = requests.request('GET', url, headers=headers, params=querystring).json()

    #determine weather at golden hour
    if (sun == 'Sunset'):
        timestamp = response['city']['sunset']
    else:
        timestamp = response['city']['sunrise']

    for x in response['list']:
        if x['dt'] >= timestamp:
            weather_info = x
            break

    icon = "http://openweathermap.org/img/w/" + weather_info['weather'][0]['icon'] + ".png"

    weather_dict = {
        'temperature': weather_info['main']['temp'],
        'description': weather_info['weather'][0]['description'],
        'icon': icon
    }

    return(weather_dict)

def getRoute(start_point, end_point):
    
    #get api information
    querystring = {
        'key': 'GKhP8fA6ETrEYmL18jh2kl6g3Lf4NoJ0',
        'from': start_point,
        'to': end_point
    }

    url = 'http://open.mapquestapi.com/directions/v2/route'

    response = requests.request('GET', url, params=querystring).json()

    print(response)
    print(start_point)
    print(end_point)
    #if invalid data entry
    if response['route']['routeError']['errorCode'] > 0 or response['route']['distance'] <= 0:
        return 'error'
    
    travel_time_minutes = response['route']['time'] / 60
    destination_city = response['route']['locations'][1]['adminArea5']
    dest_longitude = response['route']['locations'][1]['displayLatLng']['lng']
    dest_latitude = response['route']['locations'][1]['displayLatLng']['lat']
    start_longitude = response['route']['locations'][0]['displayLatLng']['lng']
    start_latitude = response['route']['locations'][0]['displayLatLng']['lat']

    route = {
        'time': travel_time_minutes,
        'city': destination_city,
        'dest_lng': dest_longitude,
        'dest_lat': dest_latitude,
        'start_lng': start_longitude,
        'start_lat': start_latitude
    }

    return route

def getTravelTime(minutes):
    
    hours = 0

    if (minutes > 60):
        hours = math.floor(minutes / 60)
        minutes = math.floor(minutes % 60)
        return 'The trip will take {} hours and {} minutes.'.format(hours,minutes)
    
    return 'The trip will take {} minutes.'.format(math.floor(minutes))

def getMapURL(start_lat, start_lng, dest_lat, dest_lng):
    
    #get api information
    querystring = {
        'key': 'GKhP8fA6ETrEYmL18jh2kl6g3Lf4NoJ0',
        'start': str(start_lat) + ',' + str(start_lng),
        'end': str(dest_lat) + ',' + str(dest_lng)
    }

    url = 'https://open.mapquestapi.com/staticmap/v5/map?' + urlencode(querystring)

    return url

def getGoldenHour(lng, lat, sun):

    #get api information
    querystring = {
        'lat': lat,
        'lng': lng,
        'date': 'tomorrow'
    }

    url = 'https://api.sunrise-sunset.org/json?'

    response = requests.request('GET', url, params=querystring).json()

    #constants
    destination_timezone = pytz.timezone(tf.timezone_at(lng=lng, lat=lat))

    #sunset workflow
    if (sun == 'Sunset'):
        sunset = response['results']['sunset']
        sunset_utc = parser.parse(sunset)
        sunset_utc = (pytz.utc).localize(sunset_utc)
        sunset_destination = sunset_utc.astimezone(destination_timezone)
        golden_hour = {
            'string': sunset_destination.strftime('%I:%M %p'),
            'datetime': sunset_destination,
            'utc': sunset_utc
        }
        return golden_hour
    
    #sunrise workflow
    sunrise = response['results']['sunrise']
    sunrise_utc = parser.parse(sunrise)
    sunrise_utc = (pytz.utc).localize(sunrise_utc)
    sunrise_destination = sunrise_utc.astimezone(destination_timezone)
    golden_hour = {
            'string': sunrise_destination.strftime('%I:%M %p'),
            'datetime': sunrise_destination,
            'utc': sunrise_utc
        }
    return golden_hour

def getItinerary(golden_hour, minutes, lng, lat):
    
    #determine time to leave local time to get there an hour early
    start_timezone = pytz.timezone(tf.timezone_at(lng=lng, lat=lat))
    travel_time = datetime.timedelta(minutes=(minutes+60))
    leave_by = golden_hour - travel_time
    leave_by = leave_by.astimezone(start_timezone)
    return leave_by.strftime('%I:%M %p')