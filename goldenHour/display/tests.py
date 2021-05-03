from . import views
from django.test import TestCase
import json

# Create your tests here.
class TestIndex(TestCase):

    def test_home_page_status_code(self):
        response = self.client.get('/')
        self.assertEquals(response.status_code, 200) 
    
    def test_weather_city(self):
        response = 'Chicago'

        self.assertEquals(response, views.getWeather('Chicago')['city'])

    def test_weather_typo(self):
        response = 'city not found'

        self.assertEquals(response, views.getWeather('chacigo')['city'])