#! /usr/bin/env python
"""
The terminal just accepts pings from the timer app
"""
import os
import time
## www.pubnub.com - PubNub Real-time push service in the cloud.
# coding=utf8

## PubNub Real-time Push APIs and Notifications Framework
## Copyright (c) 2010 Stephen Blum
## http://www.pubnub.com/

## -----------------------------------
## PubNub 3.0 Real-time Push Cloud API
## -----------------------------------
import datetime

try: import json
except ImportError: import simplejson as json

import hashlib
import urllib2
import uuid

class Pubnub():
    def __init__(
        self,
        publish_key,
        subscribe_key,
        secret_key = None,
        ssl_on = False,
        origin = 'pubsub.pubnub.com',
        pres_uuid = None
    ) :
        """
        #**
        #* Pubnub
        #*
        #* Init the Pubnub Client API
        #*
        #* @param string publish_key required key to send messages.
        #* @param string subscribe_key required key to receive messages.
        #* @param string secret_key optional key to sign messages.
        #* @param boolean ssl required for 2048 bit encrypted messages.
        #* @param string origin PUBNUB Server Origin.
        #* @param string pres_uuid optional identifier for presence (auto-generated if not supplied)
        #**

        ## Initiat Class
        pubnub = Pubnub( 'PUBLISH-KEY', 'SUBSCRIBE-KEY', 'SECRET-KEY', False )

        """
        self.origin        = origin
        self.limit         = 1800
        self.publish_key   = publish_key
        self.subscribe_key = subscribe_key
        self.secret_key    = secret_key
        self.ssl           = ssl_on

        if self.ssl :
            self.origin = 'https://' + self.origin
        else :
            self.origin = 'http://'  + self.origin

        self.uuid = pres_uuid or str(uuid.uuid4())

        if not isinstance(self.uuid, basestring):
            raise AttributeError("pres_uuid must be a string")

    def publish( self, args ) :
        """
        #**
        #* Publish
        #*
        #* Send a message to a channel.
        #*
        #* @param array args with channel and message.
        #* @return array success information.
        #**

        ## Publish Example
        info = pubnub.publish({
            'channel' : 'hello_world',
            'message' : {
                'some_text' : 'Hello my World'
            }
        })
        print(info)

        """
        ## Fail if bad input.
        if not (args['channel'] and args['message']) :
            return [ 0, 'Missing Channel or Message' ]

        ## Capture User Input
        channel = str(args['channel'])
        message = json.dumps(args['message'], separators=(',',':'))

        ## Sign Message
        if self.secret_key :
            signature = hashlib.md5('/'.join([
                self.publish_key,
                self.subscribe_key,
                self.secret_key,
                channel,
                message
            ])).hexdigest()
        else :
            signature = '0'

        ## Send Message
        return self._request([
            'publish',
            self.publish_key,
            self.subscribe_key,
            signature,
            channel,
            '0',
            message
        ]) or [ 0, "Not Sent", "0" ]


    def subscribe( self, args ) :
        """
        #**
        #* Subscribe
        #*
        #* This is BLOCKING.
        #* Listen for a message on a channel.
        #*
        #* @param array args with channel and callback.
        #* @return false on fail, array on success.
        #**

        ## Subscribe Example
        def receive(message) :
            print(message)
            return True

        pubnub.subscribe({
            'channel'  : 'hello_world',
            'callback' : receive
        })

        """

        ## Fail if missing channel
        if not 'channel' in args :
            raise Exception('Missing Channel.')
            return False

        ## Fail if missing callback
        if not 'callback' in args :
            raise Exception('Missing Callback.')
            return False

        ## Capture User Input
        channel   = str(args['channel'])
        callback  = args['callback']
        subscribe_key = args.get('subscribe_key') or self.subscribe_key

        ## Begin Subscribe
        while True :

            timetoken = 'timetoken' in args and args['timetoken'] or 0
            try :
                ## Wait for Message
                response = self._request(self._encode([
                    'subscribe',
                    subscribe_key,
                    channel,
                    '0',
                    str(timetoken)
                ])+['?uuid='+self.uuid], encode=False)

                messages          = response[0]
                args['timetoken'] = response[1]

                ## If it was a timeout
                if not len(messages) :
                    continue

                ## Run user Callback and Reconnect if user permits.
                for message in messages :
                    if not callback(message) :
                        return

            except Exception:
                time.sleep(1)

        return True

    def presence( self, args ) :
        """
        #**
        #* presence
        #*
        #* This is BLOCKING.
        #* Listen for presence events on a channel.
        #*
        #* @param array args with channel and callback.
        #* @return false on fail, array on success.
        #**

        ## Presence Example
        def pres_event(message) :
            print(message)
            return True

        pubnub.presence({
            'channel'  : 'hello_world',
            'callback' : receive
        })
        """

        ## Fail if missing channel
        if not 'channel' in args :
            raise Exception('Missing Channel.')
            return False

        ## Fail if missing callback
        if not 'callback' in args :
            raise Exception('Missing Callback.')
            return False

        ## Capture User Input
        channel   = str(args['channel'])
        callback  = args['callback']
        subscribe_key = args.get('subscribe_key') or self.subscribe_key

        return self.subscribe({'channel': channel+'-pnpres', 'subscribe_key':subscribe_key, 'callback': callback})


    def here_now( self, args ) :
        """
        #**
        #* Here Now
        #*
        #* Load current occupancy from a channel.
        #*
        #* @param array args with 'channel'.
        #* @return mixed false on fail, array on success.
        #*

        ## Presence Example
        here_now = pubnub.here_now({
            'channel' : 'hello_world',
        })
        print(here_now['occupancy'])
        print(here_now['uuids'])

        """
        channel = str(args['channel'])

        ## Fail if bad input.
        if not channel :
            raise Exception('Missing Channel')
            return False

        ## Get Presence Here Now
        return self._request([
            'v2','presence',
            'sub_key', self.subscribe_key,
            'channel', channel
        ]);


    def history( self, args ) :
        """
        #**
        #* History
        #*
        #* Load history from a channel.
        #*
        #* @param array args with 'channel' and 'limit'.
        #* @return mixed false on fail, array on success.
        #*

        ## History Example
        history = pubnub.history({
            'channel' : 'hello_world',
            'limit'   : 1
        })
        print(history)

        """
        ## Capture User Input
        limit   = args.has_key('limit') and int(args['limit']) or 10
        channel = str(args['channel'])

        ## Fail if bad input.
        if not channel :
            raise Exception('Missing Channel')
            return False

        ## Get History
        return self._request([
            'history',
            self.subscribe_key,
            channel,
            '0',
            str(limit)
        ]);

    def detailedHistory(self, args) :
        """
        #**
        #* Detailed History
        #*
        #* Load Detailed history from a channel.
        #*
        #* @param array args with 'channel', optional: 'start', 'end', 'reverse', 'count'
        #* @return mixed false on fail, array on success.
        #*

        ## History Example
        history = pubnub.detailedHistory({
            'channel' : 'hello_world',
            'count'   : 5
        })
        print(history)

        """
        ## Capture User Input
        channel = str(args['channel'])

        params = []
        count = 100

        if args.has_key('count'):
            count = int(args['count'])

        params.append('count' + '=' + str(count))

        if args.has_key('reverse'):
            params.append('reverse' + '=' + str(args['reverse']).lower())

        if args.has_key('start'):
            params.append('start' + '=' + str(args['start']))

        if args.has_key('end'):
            params.append('end' + '=' + str(args['end']))

        ## Fail if bad input.
        if not channel :
            raise Exception('Missing Channel')
            return False

        ## Get History
        return self._request([
            'v2',
            'history',
            'sub-key',
            self.subscribe_key,
            'channel',
            channel,
        ],params=params);

    def time(self) :
        """
        #**
        #* Time
        #*
        #* Timestamp from PubNub Cloud.
        #*
        #* @return int timestamp.
        #*

        ## PubNub Server Time Example
        timestamp = pubnub.time()
        print(timestamp)

        """
        return self._request([
            'time',
            '0'
        ])[0]


    def _encode( self, request ) :
        return [
            "".join([ ' ~`!@#$%^&*()+=[]\\{}|;\':",./<>?'.find(ch) > -1 and
                hex(ord(ch)).replace( '0x', '%' ).upper() or
                ch for ch in list(bit)
            ]) for bit in request]


    def _request( self, request, origin = None, encode = True, params = None ) :
        ## Build URL
        url = (origin or self.origin) + '/' + "/".join(
            encode and self._encode(request) or request
        )
        ## Add query params
        if params is not None and len(params) > 0:
            url = url + "?" + "&".join(params)

        ## Send Request Expecting JSONP Response
        try:
            try: usock = urllib2.urlopen( url, None, 200 )
            except TypeError: usock = urllib2.urlopen( url, None )
            response = usock.read()
            usock.close()
            return json.loads( response )
        except:
            return None


__author__ = 'patrickwalsh'


# Pubnub settings
PUBNUB_SUBSCRIBE_KEY = 'sub-c-2c88bc14-4023-11e3-83cf-02ee2ddab7fe'
PUBNUB_PUBLISH_KEY = 'pub-c-906c9ab8-9f24-4779-b7ed-a81c01bb0598'
PUBNUB_SECRET_KEY = 'sec-c-MTQxOTFlMGItZjkzNC00YzdjLWEwMmEtYjUzYWM2MWUwYzY5'
PUBNUB_SSL_ON = False

pubnub = Pubnub(PUBNUB_PUBLISH_KEY, PUBNUB_SUBSCRIBE_KEY, PUBNUB_SECRET_KEY, ssl_on=PUBNUB_SSL_ON)

CHANNEL = 'chan-682471fc-c961-40c7-b69f-a2be23de49c5'

SPRINT_DT = datetime.timedelta(minutes=25)


# database stuff for generating reports
from sqlalchemy import create_engine, Column, String, Integer, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


engine = create_engine('sqlite:///accomplishments.db')
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()


class Accomplishment(Base):
    __tablename__ = 'accomplishment'

    id = Column(Integer, primary_key=True)
    date = Column(Date)
    datetime = Column(DateTime)
    note = Column(String)

    def __init__(self, note):
        self.note = note
        now = datetime.datetime.now()
        self.date = now.date()
        self.datetime = now

    def __repr__(self):
        return '<Accomplishment {}: {}>'.format(self.id, self.note, self.datetime)

# commit the table definitions to the db
Base.metadata.create_all(engine)


WORK_ACTIONS = ('work', 'sprint')
REST_ACTIONS = ('rest',)

def notify(title, subtitle, message):
    t = '-title {!r}'.format(title)
    s = '-subtitle {!r}'.format(subtitle)
    m = '-message {!r}'.format(message)
    os.system('terminal-notifier {}'.format(' '.join([m, t, s])))


def receive(message):
    print(message)
    action = message['action']
    seconds = message['length']
    minutes = round(seconds / 60., 2)

    if action.lower() in REST_ACTIONS:
        register_accomplishment()
    try:
        i = 0
        while True:
            print('{} for {} minutes, ctrl+c to confirm.'.format(action, minutes), '\a')
            time.sleep(0.5)
            if i % 10 == 0:
                # send a growl notification every 5 seconds
                notify(
                    title='Work Timer',
                    subtitle=str(action),
                    message='Time to {} for {} minutes!'.format(action, minutes)
                )
            i += 1
    except KeyboardInterrupt:
        print('\n\n{}ing for {} minutes\n\n'.format(action, minutes))

    return True


def register_accomplishment():
    note = raw_input('\nWhat did you accomplish on your last sprint?\n>>> ')
    accomplishment = Accomplishment(note)
    session.add(accomplishment)
    session.commit()
    print('Awesome! Good job!')


def listener(options):
    print('Listening...\n')
    pubnub.subscribe(dict(
        channel=CHANNEL,
        callback=receive
    ))

strf = '%I:%M%p'

def report(options):
    report_date = options.date
    accs = session.query(Accomplishment).filter(Accomplishment.date==report_date).order_by(Accomplishment.datetime).all()
    header = 'Accomplishments for {}'.format(report_date.ctime())
    print '\n\n', header
    print '=' * header.__len__()
    for acc in accs:
        block_end = acc.datetime
        block_start = block_end - SPRINT_DT

        print block_start.time().strftime(strf), '-', block_end.time().strftime(strf), ' ' , acc.note
    print('\n\n')


# actions
LISTEN = 'listen'
REPORT = 'report'

def mkdate(datestring):
    return datetime.datetime.strptime(datestring, '%Y-%m-%d').date()

def mktime(timestring):
    return datetime.datetime.strptime(timestring, '%I:%M%p').time()

def mkdelta(deltatuple):
    return datetime.timedelta(deltatuple)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(prog='TwentyFiveFive')
    parser.add_argument('action', default=LISTEN, nargs='?',
                        help='Action to perform: listen, report')
    parser.add_argument('--date', '-d', default=datetime.datetime.now().date().isoformat(), type=mkdate,
                        help='If reporting, enter the date to report in format: YYYY-MM-DD')

    values = parser.parse_args()
    actions = {
        LISTEN: listener,
        REPORT: report
    }
    method = actions[values.action]
    method(values)
cwd = os.path.dirname(os.path.realpath(__file__))








