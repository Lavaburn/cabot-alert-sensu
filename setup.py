#!/usr/bin/env python

from setuptools import setup

setup(name='cabot-alert-sensu',
      version='1.2.6',
      description='A Cabot alert plugin for Sensu',
      author='Nicolas Truyens',
      author_email='nicolas@truyens.com',
      url='https://github.com/Lavaburn/cabot-alert-sensu/',
      packages=[
      	'cabot_alert_sensu'
      ],
      download_url= 'https://github.com/Lavaburn/cabot-alert-sensu/archive/master.zip'
     )
