from django.db import models
#from django.conf import settings
#from django.template import Context, Template

from cabot.cabotapp.alert import AlertPlugin, AlertPluginUserData

from os import environ as env

#import requests

#sb_alert_url = env['STASHBOARD_URI']

class SensuAlert(AlertPlugin):
    name = "Sensu"
    author = "Nicolas Truyens"

    def send_alert(self, service, users, duty_officers):
        """TODO"""
        
        
        
        
        
        return

# class SensuAlertUserData(AlertPluginUserData):
#     name = "Sensu Plugin"
#     #favorite_bone = models.CharField(max_length=50, blank=True)
