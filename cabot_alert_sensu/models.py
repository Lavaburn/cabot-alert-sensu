from django.db import models
from cabot.cabotapp.alert import AlertPlugin, AlertPluginUserData

class SensuAlert(AlertPlugin):
    name = "Sensu"
    author = "Nicolas Truyens"

    def send_alert(self, service, users, duty_officers):
        """TODO"""
        
        
        
        
        
        return

class SkeletonAlertUserData(AlertPluginUserData):
    name = "Sensu Plugin"
    #favorite_bone = models.CharField(max_length=50, blank=True)

