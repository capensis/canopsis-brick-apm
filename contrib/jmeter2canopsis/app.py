#!bin/python
#--------------------------------
# copyright (c) 2011 "capensis" [http://www.capensis.com]
#
# this file is part of canopsis.
#
# canopsis is free software: you can redistribute it and/or modify
# it under the terms of the gnu affero general public license as published by
# the free software foundation, either version 3 of the license, or
# (at your option) any later version.
#
# canopsis is distributed in the hope that it will be useful,
# but without any warranty; without even the implied warranty of
# merchantability or fitness for a particular purpose.  see the
# gnu affero general public license for more details.
#
# you should have received a copy of the gnu affero general public license
# along with canopsis.  if not, see <http://www.gnu.org/licenses/>.
# ---------------------------------

import sys, os, subprocess, csv, json, amqp, re, kombu, glob, socket, time, hashlib, random, multiprocessing, logging

from multiprocessing import Pool
from random import randint
#from config import CMD_JMETER, PATH_JAVA, PATH_JMETER, BIN_JMETER, CSV_PATH, CNTXT_OS, CNTXT_BROWSER, CNTXT_LOCATION, CANOPSIS_AMQP_HOST, CANOPSIS_AMQP_PORT, CANOPSIS_AMQP_USER, CANOPSIS_AMQP_PASS, CANOPSIS_AMQP_VHOST, DEBUG, JMX_PATH, NBR_PROCESS, PROCESS_PARALLEL

from kombu import Connection, Exchange, Queue, Producer

from daemon import runner

#debug = DEBUG

def unwrap_self_processing(arg, **kwarg):
    return App.processing(*arg, **kwarg)

class App():
    def __init__(self, path):
        self.path = path
        self.stdin_path = '/dev/null'
        self.stdout_path = '/dev/tty'
        self.stderr_path = '/dev/tty'
        self.pidfile_path = '/var/run/mydaemon.pid'
        self.pidfile_timeout = 5

    def clean_string(self,str):
        return re.sub( r"%", ".", re.sub( r"\s+", "-", re.sub( r"(\.|-|\"|\'|http:\/\/)", "", str ) ) )

    def publish2amqp(self,doc):
        logger.debug( doc )
        
        amqp_uri = "amqp://%s:%s@%s:%s/%s" % ( self.config['AMQP']['USER'], self.config['AMQP']['PASS'], self.config['AMQP']['HOST'], self.config['AMQP']['PORT'], self.config['AMQP']['VHOST'] )
	logger.debug( "AMQP URI => %s" % amqp_uri )
	
	rk = "%s.%s.%s.%s.%s.%s" % ( doc['connector'], doc['connector_name'], doc['event_type'], doc['source_type'], doc['component'], doc['resource'] )
        logger.debug( rk )
	
	conn = Connection(amqp_uri)
	conn.connect()
        if conn.connected:
            channel = conn.channel()
            exch = Exchange("canopsis.events", "topic", durable=True, auto_delete=False)
            producer = Producer(channel, exchange=exch, serializer="json")
            producer.publish( doc, routing_key=rk, serializer="json")
        else:
            logging.error( "AMQP Connection failed" )
            time.sleep(500 / 1000000.0)

    def processing(self,jmx):
        logger.info( multiprocessing.current_process() )

	uniqueKey = hashlib.md5("%f%i" % ( time.time(), randint(100000000,999999999) )).hexdigest()
        logger.debug( "%s" % uniqueKey )
	
        cmd = ("%s" % self.config["CMD_JMETER"]) % (self.config["PATH_JAVA"], ("%s/%s" % (self.config["PATH_JMETER"], self.config["BIN_JMETER"])), jmx )
        logger.debug( cmd )

	file = self.config["CSV_PATH"] + '/' + os.path.splitext(os.path.basename( jmx ))[0] + '.csv'
	if os.path.exists(file):
	    os.remove(file)

	subprocess.call( cmd.split(), stdin=None, stdout=None, stderr=None )

        info = None
	docFeat = None
	docScenar = None
        if os.path.exists(file):
            logging.info( "=> Start Processing %s" % file )
            rows = csv.reader(open(file, "rb"))
            for row in rows:
                logging.debug( row )
   
                if row[0] != 'timeStamp':
                    if info == None:
                        info = {
                            'robot':		row[12] if len(row) > 12 else socket.gethosname(),
                            'app':	        row[4].split('#')[1],
                            'feature':		row[4].split('#')[2],
                            'scenario':		row[4].split('#')[3],
                            'cntxt_env':	row[4].split('#')[0],
                            'cntxt_os':		self.config['CNTXT_OS'],
                            'cntxt_browser':	self.config['CNTXT_BROWSER'],
                            'cntxt_location':	self.config['CNTXT_LOCATION'],
                            'uniqueKey':	str(uniqueKey),
                            'step_ok':		0,
                            'step_nbr':		0,
                        }

                    docFeat =  {
                        'connector':    	'cucumber',
                        'connector_name':	info['robot'],
                        'event_type':	        'eue',
                        'source_type':  	'resource',
                        'component':            info['app'],
                        'resource':		self.clean_string( info['feature'] ),
                        'type_message':	        'feature',
                        'state':		0,
                        'timestamp':	        int(time.time()),
                    }

                    docScenar =  {
                        'connector':            'cucumber',
                        'connector_name':	info['robot'],
                        'event_type':       	'eue',
                        'source_type':      	'resource',
                        'component':    	info['app'],
                        'resource':		self.clean_string( info['feature'] + "%" + info['scenario'] + "%" + info['cntxt_location'] + "%" + info['cntxt_os'] + "%" + info['cntxt_browser'] ),
                        'type_message': 	'scenario',
                        'cntxt_env':    	info['cntxt_env'],
                        'cntxt_os':		info['cntxt_os'],
                        'cntxt_browser':	info['cntxt_browser'],
                        'cntxt_location':	info['cntxt_location'],
                        'state':		0,
                        'uniqueKey':	        info['uniqueKey'],
                        'duration':		0,
                        'perf_data_array':	[{ u'metric': u'duration_scenario', u'value':0, u'label':'Duration ' + info['scenario'] },{ u'metric': u'disponibilite', u'value':0, u'max':2, u'min':0}],
                        'timestamp':	        int(time.time()),
                    }
                    docScenar['child'] = "%s.%s.%s.%s.%s.%s" % ( docScenar['connector'], docScenar['connector_name'], docScenar['event_type'], docScenar['source_type'], docScenar['component'], self.clean_string( info['feature'] ) )

                    docStep =  {
                        'connector':	        'cucumber',
                        'connector_name':	info['robot'],
                        'event_type':	        'eue',
                        'source_type':  	'resource',
                        'component':	        info['app'],
                        'resource':		self.clean_string( info['feature'] + "%" + info['scenario'] + "%" + row[2] + "%" + info['cntxt_location'] + "%" + info['cntxt_os'] + "%" + info['cntxt_browser'] ),
                        'type_message':	        'step',
                        'state':		0 if row[5] == "true" else 2,
                        'uniqueKey':	        info['uniqueKey'],
                        'output':		info['cntxt_location'] + ' - Duration: ' + str(int(row[1])),
                        'perf_data_array':	[{ u'metric': u'duration_'+ unicode(row[2],'utf-8').lower(), u'value':row[1] }],
                        'timestamp':	        int(time.time()),
                    }
                    docStep['child'] = "%s.%s.%s.%s.%s.%s" % ( docStep['connector'], docStep['connector_name'], docStep['event_type'], docStep['source_type'], docStep['component'], self.clean_string( info['feature'] + "%" + info['scenario'] + "%" + info['cntxt_location'] + "%" + info['cntxt_os'] + "%" + info['cntxt_browser'] ) )
                    info['step_nbr'] += 1

                    if row[5] == "false":
                        docScenar['state'] = 2 if docScenar['state'] == 0 else docScenar['state'] 
                        docFeat['state'] = 2 if docFeat['state'] == 0 else docScenar['state']
                    else:
                        info['step_ok'] += 1

                    docScenar['perf_data_array'][0]['value'] += int( row[1] )
                    docScenar['perf_data_array'][1]['value'] = 2-int( docScenar['state'] )
                    docScenar['output'] = info['cntxt_location'] + ' - Duration: ' + str(int(docScenar['perf_data_array'][0]['value'])) + " - Step OK:" + str(info['step_ok']) + '/' + str(info['step_nbr'])
                    docScenar['long_output'] = docScenar['output']

                    self.publish2amqp( docStep )
            self.publish2amqp( docScenar )
            self.publish2amqp( docFeat )
            logging.info( "Finish Processing %s" % file )
        else:
            logging.warning( "%s, File not found" % file )

    def run(self):

        while True:  
            logger.info( "Global process start at %s" % 'to' )

            with open( "%s/%s" % (self.path,'config.json') ) as configJson:
                self.config = json.load(configJson)
                if self.config['PATH_JMETER'][:2] == "./":
                    self.config['PATH_JMETER'] = "%s/%s" % ( self.path, self.config['PATH_JMETER'][2:] )
            logger.debug( self.config )

            if not os.path.exists( "%s/jmx" % self.path ):
                logger.error( "Error the JMX Path: %s/jmx for massive processing does not exist", PATH  )
            else:
                jmxs = []
                for file in glob.glob( "%s/jmx/*.jmx" % self.path ):
                    jmxs.append( file )
                    		
                if self.config["PROCESS_PARALLEL"]:
                    jmxs.sort()
                    pool = Pool(processes=self.config["NBR_PROCESS"])
                    pool.map( unwrap_self_processing, zip([self]*len(jmxs), jmxs) )
                else:
                    for file in jmxs:
                        self.processing(file)	

            #time.sleep(10)

if __name__ == '__main__':
    path = os.path.dirname(os.path.abspath(__file__))
    app = App( path )
    logger = logging.getLogger("DaemonLog")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.FileHandler("/tmp/testdaemon.log")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    daemon_runner = runner.DaemonRunner(app)
    daemon_runner.daemon_context.files_preserve=[handler.stream]
    daemon_runner.do_action()
