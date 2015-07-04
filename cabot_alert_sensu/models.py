from django.db import models
#from django.conf import settings
#from django.template import Context, Template

from cabot.cabotapp.alert import AlertPlugin, AlertPluginUserData

from os import environ as env

#import requests

sensu_port = env['SENSU_PORT'] or '3030'

class SensuAlert(AlertPlugin):
    name = "Sensu"
    author = "Nicolas Truyens"

    def send_alert(self, service, users, duty_officers):
        parts = service.name.split("_")
        if (len(parts) == 1 or len(parts) == 2):
             if (len(parts) == 1):
                source = 'network'
                check = service.name
             else:
                source = parts[0]
                check = parts[1]
        else:
            print "The service name should contain 1 underscore to split up source and check name."
            # TODO - RAISE ERROR ?
            return
            
        if service.overall_status == service.PASSING_STATUS:
            status = 0
        elif service.overall_status == service.WARNING_STATUS:
            status = 1
        elif service.overall_status == service.CRITICAL_STATUS:
            status = 2
        elif service.overall_status == service.ERROR_STATUS:
            status = 3
        
        output = check.last_result().raw_data
        
        for user in users:
            userdata = SensuAlertUserData.objects.get(user=user, title=SensuAlertUserData.name)
            handlers = userdata.handlers
        
            send_sensu_alert(source=source, check=check, status=status, output=output, handlers=handlers)
        
        return
    
    def send_sensu_alert(source, check, status, output, handlers):
        #fo = open("/dev/tcp/localhost/3030", "w")
        fo = open("/tmp/cabot_sensu", "w")        
        
        fo.write( '{"name": "'+check+'", "source": "'+source+'", "status": '+status+', "output": "'+output+'", "handlers": ['+handlers+'] }' );
            #echo '{"name": "app_01", "output": "could not connect to mysql", "status": 1}' > 
            
        fo.close()

class SensuAlertUserData(AlertPluginUserData):
     name = "Sensu Plugin"
     
     handlers = models.CharField(max_length=250, blank=True)
