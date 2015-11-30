# Cabot Alert Plugin - Sensu
# --------------------------
# * Currently only works for Graphite Checks
# * Supposes you name the service as NAME@HOST so HOST can be used as source in Sensu
# 
# Nicolas Truyens <nicolas@truyens.com>

from django.db import models
#from django.conf import settings
#from django.template import Context, Template

from cabot.cabotapp.alert import AlertPlugin, AlertPluginUserData

from os import environ as env

import socket
import sys
import json
#import requests

sensu_port = env.get('SENSU_PORT') or 3030              # Integer required !!!
sensu_host = env.get('SENSU_HOST') or 'localhost'
DEBUG = env.get('SENSU_DEBUG') or False

class SensuAlert(AlertPlugin):
    name = "Sensu"
    author = "Nicolas Truyens"
    
    def xstr(self, s):
        if s is None:
            return ''
        return str(s)

    def send_alert(self, service, users, duty_officers):
        if DEBUG:
            debug = open("/var/log/cabot/alert_sensu.log", "a")
            debug.write( 'Sending alert to Sensu.\n' )
            
        parts = service.name.split("@")
        if (len(parts) == 1 or len(parts) == 2):
             if (len(parts) == 1):
                source = 'network'
                checkname = service.name
             else:
                checkname = parts[0]
                source = parts[1]
        else:
            print "The service name should contain 1 @ to split up source and check name."
            if DEBUG:
                debug.write( 'The service name should contain 1 @ to split up source and check name. Name = '+self.xstr(service.name)+'\n' )         
            # TODO - RAISE ERROR ?
            return
        
        tags = list()    
        tags.append(source)
        tags.append(checkname)
            
        if service.overall_status == service.PASSING_STATUS:
            status = '0'
        elif service.overall_status == service.WARNING_STATUS:
            status = '1'
        elif service.overall_status == service.CRITICAL_STATUS:
            status = '2'
        elif service.overall_status == service.ERROR_STATUS:
            status = '3'
                
        extra_info = dict()
        for check in service.all_failing_checks():
            result = check.last_result()
            for raw_data_row in json.loads(result.raw_data):
                datapoints = list()
                
                try:
                    debug.write( 'DEBUG_1A: '+self.xstr(raw_data_row)+'\n' )
                    debug.write( 'DEBUG_1B: '+self.xstr(raw_data_row[0])+'\n' )
                    debug.write( 'DEBUG_1C: '+self.xstr(raw_data_row[0]["datapoints"])+'\n' )
                    
#                     datapoints_arr = raw_data_row[0]["datapoints"]
#                                              
#                     for datapoint in datapoints_arr:
#                         datapoints.push(datapoint[0])
                except:
                    if DEBUG:
                        debug.write( 'datapoints is not a valid key? Raw Data: '+self.xstr(raw_data_row)+'\n' )
                    
            extra_info[check.name] = { 'metric': check.metric, 'took': str(result.took)+' ms', 'error': result.error, 'datapoints': datapoints }
                
        # Other Tags
        
        # REMOVED - Cabot will probably remove instances in newer releases.
#         for linked_instance in service.instances.all():
#             instance_parts = linked_instance.name.split("_")
#             for part in instance_parts:
#                 tags.append(part)
        
        for linked_check in service.status_checks.all():
            check_parts = linked_check.name.split("_")
            for part in check_parts:
                tags.append(part)
        
        hackpad = self.xstr(service.hackpad_id)
        hackpad_parts = hackpad.split(",")
        for part in hackpad_parts:
            tags.append(part)
        
        tags_unique = set(tags) # unique elements
        try:
            tags_unique.remove('')  # make sure there is no empty tag
        except:
            pass
        tags = list(tags_unique)    # Convert back to list (for JSON)
        
        output = 'Service '+service.name+': '+self.xstr(service.overall_status)
        exta_data = ', "extra_info": '+json.dumps(extra_info)+', "service_url": "'+self.xstr(service.url)+'", "tags": '+json.dumps(tags)    # Tags should be represented as array []
        
        if DEBUG:
            debug.write( 'source: ' + source + ' - name: ' + checkname + ' - status: ' + status + ' - output: ' + output + ' - extra_data: ' + exta_data + '\n' )        
        
        handlerList = list()         
        for user in users:
            try:
                if DEBUG:
                    debug.write( 'User found: '+self.xstr(user)+' \n' )
                
                debug.write( 'DEBUG_2A: '+self.xstr(SensuAlertUserData.objects.filter(user__user__in=users)+'\n' )
                debug.write( 'DEBUG_2B: '+self.xstr(SensuAlertUserData.objects.get(user=user, title=SensuAlertUserData.name)+'\n' )
                
#                 userData = SensuAlertUserData.objects.get(user=user, title=SensuAlertUserData.name)
#                 userHandlers = userData.handlers
# 
#                 parts = userHandlers.split(",")
#                 for part in parts:
#                     handlerList.append('"'+part+'"')
            except:
                if DEBUG:
                    debug.write( 'Error while getting userdata for user '+self.xstr(user)+'\n' )
            
        uniqueHandlerList = set(handlerList)
        handlers = "[" + ",".join(uniqueHandlerList) + "]"
                
        if DEBUG:
            debug.write( 'handlers: ' + handlers + '\n' )        
            debug.close()
            
        self._send_sensu_alert(source=source, check=checkname, status=status, output=output, handlers=handlers, exta_data=exta_data)
                
        return
    
    def _send_sensu_alert(self, source, check, status, output, handlers, exta_data=''):
        try: 
            port = int(sensu_port)
        except ValueError:
            port = sensu_port
                
        ADDR = (sensu_host, port)
        DATA = '{"name": "'+check+'", "source": "'+source+'", "status": '+status+', "output": "'+output+'", "handlers": '+handlers+exta_data+' }'
        
        if DEBUG:
            debug = open("/var/log/cabot/alert_sensu.log", "a")
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)                         
            if DEBUG:
                debug.write('Connecting to '+sensu_host+' on port '+str(port)+'\n')
                
            s.connect(ADDR)
            if DEBUG:
                debug.write('Connected!\n')
                    
            s.send(DATA)
            if DEBUG:
                debug.write('Sent Data: '+DATA+'\n')
                            
            s.close()
        except socket.error, msg:
            print('Exception: ' + msg + '\n')
            if DEBUG:
                debug.write('Exception: ' + msg + '\n')                
        
        if DEBUG:
            debug.close() 

class SensuAlertUserData(AlertPluginUserData):
     name = "Sensu Plugin"
     
     handlers = models.CharField(max_length=250, blank=True)
