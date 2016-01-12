# Cabot Alert Plugin - Sensu
# --------------------------
# * Currently only works for Graphite Checks
# * Supposes you name the service as NAME@HOST so HOST can be used as source in Sensu
# 
# Nicolas Truyens <nicolas@truyens.com>

from django.db import models

from cabot.cabotapp.alert import AlertPlugin, AlertPluginUserData

from os import environ as env

import socket
import sys
import json

sensu_port = env.get('SENSU_PORT') or 3030              # Integer required !!!
sensu_host = env.get('SENSU_HOST') or 'localhost'
graphite_api = env.get('GRAPHITE_API') or 'http://localhost/'
graphite_from = env.get('GRAPHITE_FROM') or '-10min'
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
            
        # Host & Check
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
        
        # Status            
        if service.overall_status == service.PASSING_STATUS:
            status = '0'
        elif service.overall_status == service.WARNING_STATUS:
            status = '1'
        elif service.overall_status == service.CRITICAL_STATUS:
            status = '2'
        elif service.overall_status == service.ERROR_STATUS:
            status = '3'
            
        output = 'Service '+service.name+': '+self.xstr(service.overall_status)
        
        # Extra Info
        graphs = list()
        extra_info = dict()
        for check in service.all_failing_checks():
            result = check.last_result()
            for raw_data_row in json.loads(result.raw_data):
                datapoints = list()
                
                try:     
                    datapoints_arr = raw_data_row['datapoints']

                    for datapoint in datapoints_arr:
                        datapoints.append(datapoint[0])
                except:
                    if DEBUG:
                        debug.write( 'datapoints is not a valid key? Raw Data: '+self.xstr(raw_data_row)+'\n' )
            
            url = graphite_api+'render?from='+graphite_from+'&until=now&width=500&height=200&target='+check.metric+'&uchiwa_force_image=.jpg'
            graphs.append('"graph_'+check.name+'": "'+url+'"')
            
            extra_info[check.name] = { 'metric': check.metric, 'took': str(result.took)+' ms', 'error': result.error }  #, 'graph': url, 'datapoints': datapoints 
       
        # Tags
        tags = list()    
        tags.append(source)
        tags.append(checkname)
                
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
        
        # Service URL
        service_url = service.url
        
        if DEBUG:
            debug.write( 'source: ' + source + ' - name: ' + checkname + ' - status: ' + status + ' - output: ' + output + '\n' )
            debug.write( 'extra_info: ' + json.dumps(extra_info) + '\n' )
            debug.write( 'graphs: ' + json.dumps(graphs) + '\n' )
            debug.write( 'service_url: ' + service_url + ' - tags: ' + json.dumps(tags) + '\n' )
                     
        # Combine Extra Data
        extra = list()
        extra.push('"extra_info": '+json.dumps(extra_info))
        extra.push('"tags": '+json.dumps(tags))        
        extra.push('"service_url": "'+service_url+'"')
        
        if graphs.length > 0:
            extra.push(graphs.join(','))
            
        if extra.length > 0: 
            extra_data = ", " + extra.join(',')
        else:
            extra_data = "" 
        
        if DEBUG:
            debug.write( 'extra_data: ' + extra_data + '\n' )
        
        # Handlers
        handlerList = list()
        
        try:           
            userdataset = SensuAlertUserData.objects.filter(user__user__in=users)
        except:
            userdataset = list()
            if DEBUG:
                debug.write( 'Error while getting userdata for users '+self.xstr(users)+'\n' )
        
        for userdata in userdataset:            
            try:            
                userhandlers = userdata.handlers
                parts = userhandlers.split(",")
                for part in parts:
                    handlerList.append('"'+part+'"')
            except:
                if DEBUG:
                    debug.write( 'Error while getting handlers (userdata): '+self.xstr(userdata)+'\n' )
            
        uniqueHandlerList = set(handlerList)
        handlers = "[" + ",".join(uniqueHandlerList) + "]"

        if DEBUG:
            debug.write( 'handlers: ' + handlers + '\n' )        
            debug.close()
            
        # Push
        self._send_sensu_alert(source=source, check=checkname, status=status, output=output, handlers=handlers, extra_data=extra_data)
                
        return
    
    def _send_sensu_alert(self, source, check, status, output, handlers, extra_data=''):
        try: 
            port = int(sensu_port)
        except ValueError:
            port = sensu_port
                
        ADDR = (sensu_host, port)
        DATA = '{"name": "'+check+'", "source": "'+source+'", "status": '+status+', "output": "'+output+'", "handlers": '+handlers+extra_data+' }'
        
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
