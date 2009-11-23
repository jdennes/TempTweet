
"""
TempTweet is a little app which tweets temperatures from the Bureau of 
Meteorology website using the latest weather observations for the Sydney area.

If no weather station is specified, the default used is "Sydney - Observatory Hill".

Usage: TempTweet.py [options]

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -s STATION, --station=STATION
                        The weather station to use (defaults to "Sydney - Observatory Hill")
  -u USERNAME, --username=USERNAME
                        Twitter username
  -p PASSWORD, --password=PASSWORD
                        Twitter password
"""

import os
import sys
from optparse import OptionParser
import getpass
import re
import urllib
import urllib2
import base64
from BeautifulSoup import BeautifulSoup

TEMP_TWEET_VERSION = '0.1'

class TempEntry:
    time = ''
    value = ''

    def __init__(self, time, value):
        self.time = time
        self.value = value

class TempTweeter:
    degree_symbol = unichr(176).encode("latin-1")
    data_url = 'http://www.bom.gov.au/products/IDN60900.shtml'
    data_link = 'http://bit.ly/AluLc'
    weather_station = ''
    auth_enc = ''
    raw_data = None

    def __init__(self, weather_station, username, password):
        self.weather_station = weather_station
        self.auth_enc = base64.b64encode('{0}:{1}'.format(username, password))
        try:
            response = urllib2.urlopen(self.data_url)
            soup = BeautifulSoup(response.read())
            rows = soup.findAll('tr', { 'class' : 'rowleftcolumn' })
            for r in rows:
                link = BeautifulSoup(str(r)).find('a')
                if link.string.strip().lower() == self.weather_station.lower():
                    self.raw_data = r.findAll('td')
                    break
        except:
            self.raw_data = None
            self.err("Couldn't connect to {0}".format(self.data_url))

    def get_most_recent_low(self):
        if self.raw_data != None:
            low_temp_pattern = r'<td>(.*)<br /><small>(.*)</small></td>'
            m = re.match(low_temp_pattern, str(self.raw_data[14]))
            if m != None:
                return TempEntry(m.group(2), m.group(1))
        return None

    def get_most_recent_high(self):
        if self.raw_data != None:
            high_temp_pattern = r'<td>(.*)<br /><small>(.*)</small></td>'
            m = re.match(high_temp_pattern, str(self.raw_data[15]))
            if m != None:
                return TempEntry(m.group(2), m.group(1))
        return None

    def get_current(self):
        if self.raw_data != None:
            current_time_pattern = r'<td>.*/(.*)</td>'
            current_temp_pattern = r'<td>(.*)</td>'
            m1 = re.match(current_time_pattern, str(self.raw_data[1]))
            m2 = re.match(current_temp_pattern, str(self.raw_data[2]))
            if m1 != None and m2 != None:
                return TempEntry(m1.group(1), m2.group(1))
        return None

    def tweet_most_recent_high(self):
        high = self.get_most_recent_high()
        if high != None:
            self.tweet('Most recent high ({0}): {1}{2}C'
                       .format(high.time, high.value, self.degree_symbol))
        else:
            self.err("Couldn't retrieve most recent high temperature")

    def tweet_most_recent_low(self):
        low = self.get_most_recent_low()
        if low != None:
            self.tweet('Most recent low ({0}): {1}{2}C'
                       .format(low.time, low.value, self.degree_symbol))
        else:
            print "Error: Couldn't retrieve most recent low temperature"

    def tweet_most_recent_high_low_current(self):
        high = self.get_most_recent_high()
        low = self.get_most_recent_low()
        current = self.get_current()
        if high != None and low != None and current != None:
            self.tweet('Most recent high ({1}): {2}{0}C; Most recent low ({3}): {4}{0}C; Current ({5}): {6}{0}C {7}'
                       .format(self.degree_symbol, high.time, high.value, low.time, low.value, current.time, current.value, self.data_link))
        else:
            self.err("Couldn't retrieve most recent high, low and current temperatures")

    def tweet(self, contents):
        tweet_url = 'http://twitter.com/statuses/update.json'
        print 'Attempting to tweet:\n{0}'.format(contents)
        try:
            headers = { 'Authorization' : 'Basic {0}'.format(self.auth_enc) }
            data = urllib.urlencode({ 'status' : contents })
            request = urllib2.Request(tweet_url, data, headers)
            response = urllib2.urlopen(request)
            print 'Response:\n{0}'.format(response.read())
        except:
            self.err("Couldn't connect to Twitter ({0})".format(tweet_url))

    def err(self, msg):
        print 'Error: {0}'.format(msg)

def main():
    weather_station, username, password = '', '', ''
    parser = OptionParser(usage="usage: %prog [options]", version="%prog " + TEMP_TWEET_VERSION)
    parser.add_option("-s", "--station", action="store", dest="station", 
                      default="Sydney - Observatory Hill", help="The weather station to use (defaults to \"Sydney - Observatory Hill\"")
    parser.add_option("-u", "--username", action="store", dest="username", 
                      help="Twitter username")
    parser.add_option("-p", "--password", action="store", dest="password", 
                      help="Twitter password")
    (opts, args) = parser.parse_args()
    weather_station = opts.station
    if opts.username == None or opts.username.strip() == '':
        username = raw_input('Twitter username: ')
    else:
        username = opts.username
    if opts.password == None or opts.password.strip() == '':
        password = getpass.getpass('Twitter password: ')
    else:
        opts.password

    t = TempTweeter(weather_station, username, password)
    t.tweet_most_recent_high_low_current()

if __name__ == '__main__':
    main()
