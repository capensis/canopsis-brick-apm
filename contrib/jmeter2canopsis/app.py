#!/opt/canopsis-brick-apm/contrib/jmeter2canopsis/bin/python
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

import sys, os, subprocess, csv, json, amqp, re, kombu, glob, socket, time, hashlib, random, multiprocessing

from multiprocessing import Pool
from random import randint
from config import CMD_JMETER, PATH_JAVA, PATH_JMETER, BIN_JMETER, CSV_PATH, CNTXT_OS, CNTXT_BROWSER, CNTXT_LOCATION, CANOPSIS_AMQP_HOST, CANOPSIS_AMQP_PORT, CANOPSIS_AMQP_USER, CANOPSIS_AMQP_PASS, CANOPSIS_AMQP_VHOST, DEBUG, JMX_PATH, NBR_PROCESS, PROCESS_PARALLEL

from kombu import Connection, Exchange, Queue, Producer

debug = DEBUG

def canopsis_escape_string( str ):
	return re.sub( r"%", ".", re.sub( r"\s+", "-", re.sub( r"(\.|-|\"|\'|http:\/\/)", "", str ) ) )

def publish2amqp( document ):
	amqp_uri = "amqp://%s:%s@%s:%s/%s" % ( CANOPSIS_AMQP_USER, CANOPSIS_AMQP_PASS, CANOPSIS_AMQP_HOST, CANOPSIS_AMQP_PORT, CANOPSIS_AMQP_VHOST )
	if debug:
		print document
	
	if debug:
		"AMQP URI => %s" % amqp_uri
	
	rk = "%s.%s.%s.%s.%s.%s" % ( document['connector'], document['connector_name'], document['event_type'], document['source_type'], document['component'], document['resource'] )
	if debug:
		print rk
	
	conn = Connection(amqp_uri)
	conn.connect()
	channel = conn.channel()
	exch = Exchange("canopsis.events", "topic", durable=True, auto_delete=False)
	producer = Producer(channel, exchange=exch, serializer="json")
	producer.publish( document, routing_key=rk, serializer="json")
	time.sleep(500 / 1000000.0)

def proccessing( jmx ):
	if debug:
		print multiprocessing.current_process()

	uniqueKey = hashlib.md5("%f%i" % ( time.time(), randint(100000000,999999999) )).hexdigest()
	if debug:
		print str(uniqueKey)

	cmd = ( "%s" % CMD_JMETER)  % ( PATH_JAVA, ( ( "%s/%s" ) % ( PATH_JMETER, BIN_JMETER ) ), jmx )
	if debug:
		print cmd

	if debug:
		devnull = None
	else:
		devnull = open('/dev/null', 'w')

	file = CSV_PATH + '/' + os.path.splitext(os.path.basename( jmx ))[0] + '.csv'
	if os.path.exists(file):
		os.remove(file)

	subprocess.call( cmd.split(), stdin=devnull, stdout=devnull, stderr=devnull )

	#['timeStamp', 'elapsed', 'label', 'responseCode', 'threadName', 'success', 'bytes', 'grpThreads', 'allThreads', 'Latency', 'SampleCount', 'ErrorCount', 'Hostname']
	info = None
	document_feature = None
	document_scenario = None
	if os.path.exists(file):
		print "=> Start Processing %s" % file
		rows = csv.reader(open(file, "rb"))
		for row in rows:
			if debug:
				print row

			if row[0] != 'timeStamp':
				if info == None:
					info = {
						'robot':			row[12] if len(row) > 12 else socket.gethosname(),
						'app':				row[4].split('#')[1],
						'feature':			row[4].split('#')[2],
						'scenario':			row[4].split('#')[3],
						'cntxt_env':			row[4].split('#')[0],
						'cntxt_os':			CNTXT_OS,
						'cntxt_browser':		CNTXT_BROWSER,
						'cntxt_location':		CNTXT_LOCATION,
						'uniqueKey':			str(uniqueKey),
						'step_ok':			0,
						'step_nbr':			0,
					}

					document_feature =  {
						'connector':			'cucumber',
						'connector_name':		info['robot'],
						'event_type':			'eue',
						'source_type':			'resource',
						'component':			info['app'],
						'resource':			canopsis_escape_string( info['feature'] ),
						'type_message':			'feature',
		
						'state':			0,
						'timestamp':			int(time.time()),
					}

					document_scenario =  {
						'connector':			'cucumber',
						'connector_name':		info['robot'],
						'event_type':			'eue',
						'source_type':			'resource',
						'component':			info['app'],
						'resource':			canopsis_escape_string( info['feature'] + "%" + info['scenario'] + "%" + info['cntxt_location'] + "%" + info['cntxt_os'] + "%" + info['cntxt_browser'] ),
						'type_message':			'scenario',

						'cntxt_env':			info['cntxt_env'],
						'cntxt_os':			info['cntxt_os'],
						'cntxt_browser':		info['cntxt_browser'],
						'cntxt_location':		info['cntxt_location'],
		
						'state':			0,
						'uniqueKey':			info['uniqueKey'],
						'duration':			0,
						'perf_data_array':		[{ u'metric': u'duration_scenario', u'value':0, u'label':'Duration ' + info['scenario'] },{ u'metric': u'disponibilite', u'value':0, u'max':2, u'min':0}],
						'timestamp':			int(time.time()),
					}
					document_scenario['child'] = "%s.%s.%s.%s.%s.%s" % ( document_scenario['connector'], document_scenario['connector_name'], document_scenario['event_type'], document_scenario['source_type'], document_scenario['component'], canopsis_escape_string( info['feature'] ) )
				
				document_step =  {
					'connector':		'cucumber',
					'connector_name':	info['robot'],
					'event_type':		'eue',
					'source_type':		'resource',
					'component':		info['app'],
					'resource':		canopsis_escape_string( info['feature'] + "%" + info['scenario'] + "%" + row[2] + "%" + info['cntxt_location'] + "%" + info['cntxt_os'] + "%" + info['cntxt_browser'] ),
					'type_message':		'step',

					'state':		0 if row[5] == "true" else 2,
					'uniqueKey':		info['uniqueKey'],
					#'duration':		row[1]
					'output':		info['cntxt_location'] + ' - Duration: ' + str(int(row[1])),
					'perf_data_array':	[{ u'metric': u'duration_'+ unicode(row[2],'utf-8').lower(), u'value':row[1] }],
					'timestamp':		int(time.time()),
				}
				document_step['child'] = "%s.%s.%s.%s.%s.%s" % ( document_step['connector'], document_step['connector_name'], document_step['event_type'], document_step['source_type'], document_step['component'], canopsis_escape_string( info['feature'] + "%" + info['scenario'] + "%" + info['cntxt_location'] + "%" + info['cntxt_os'] + "%" + info['cntxt_browser'] ) )
				info['step_nbr'] += 1

				if row[5] == "false":
					document_scenario['state'] = 2 if document_scenario['state'] == 0 else 0 
					document_feature['state'] = 2 if document_feature['state'] == 0 else 0 
				else:
					info['step_ok'] += 1

				#document_scenario['duration'] += int( row[1] )
				document_scenario['perf_data_array'][0]['value'] += int( row[1] )
				document_scenario['perf_data_array'][1]['value'] = 2-int( document_scenario['state'] )
				document_scenario['output'] = info['cntxt_location'] + ' - Duration: ' + str(int(document_scenario['perf_data_array'][0]['value'])) + " - Step OK:" + str(info['step_ok']) + '/' + str(info['step_nbr'])
				document_scenario['long_output'] = document_scenario['output']

				publish2amqp( document_step )
		
		#document_scenario['perf_data_array'] = json.dumps( document_scenario['perf_data_array'] )	
		publish2amqp( document_scenario )
		publish2amqp( document_feature )
		print "=> Finish Processing %s" % file
	else:
		print "%s, File not found" % file

if __name__ == '__main__':
	if len(sys.argv) == 1:
		if not os.path.exists( JMX_PATH ):
			print "Error the JMX Path: %s for massive processing does not exist" % JMX_PATH
		else:
			jmxs = []
			for file in glob.glob( ("%s/*.jmx" % JMX_PATH) ):
				jmxs.append( file )
		
			if PROCESS_PARALLEL:
				jmxs.sort()
				pool = Pool(processes=NBR_PROCESS)
				pool.map( proccessing, jmxs )
			else:
				for file in jmxs:
					proccessing( jmxs )	

	elif len(sys.argv) == 2:
		if not os.path.exists( sys.argv[1] ):
			print "Error the JMX File does not exist"
		else:
			proccessing( sys.argv[1] )
	else:
		print "Error on cli command:"
		print "For multiple processing just create the JMX Path: %s" % JMX_PATH
		print "For mono processing: ./app.py jmxfile"
