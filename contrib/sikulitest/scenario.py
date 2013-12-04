# -*- coding: utf-8 -*-

import time
import sys
import pynsca

class Scenario(object):
    """
        Describe a sikuli scenario.
        All test case must start with 'test_'.
    """

    def __init__(self, name="Sikuli"):
        """
            Initialize scenario.

            :param name: Scenario's name (default: "Sikuli").
            :type name: basestring
        """

        self.data = {
            'name': name,
            'status': 0,
            'message': 'Passed',
            'stats': {}
        }

        # Get testsuite
        self.tests = []

        tests = [method for method in dir(self) if method.startswith('test_')]
        tests.sort()

        for test in tests:
            self.tests.append(getattr(self, test))

    def init(self):
        """
            Initialize data for scenario.
        """

        pass

    def release(self):
        """
            Release data initialized in scenario.
        """

        pass

    def setUp(self):
        """
            Called before each tests.
        """

        pass

    def tearDown(self):
        """
            Called after each tests.
        """

        pass

    def main(self):
        """
            Run the test-suite.

            This function exit the program with code 0 or the code returned
            by a failed test.
        """

        self.init()

        # Start testsuite
        starttime = time.time()

        for test in self.tests:
            testname = test.__name__[5:]
            fail = False

            # init test
            self.setUp()

            # run test
            test_starttime = time.time()

            status = test()

            test_endtime = time.time()

            if status and status != 0:
                self.data['status'] = status
                self.data['message'] = "Test '%s' failed" % testname

                fail = True

            # tear down test
            if not fail:
                self.tearDown()

            # Generate stats for this test
            self.data['stats'][testname] = {
                'timeperiod': test_endtime - test_starttime,
                'status': status
            }

        endtime = time.time()

        # End of testsuite

        self.data['stats']['global'] = {
            'timeperiod': endtime - starttime,
            'status': self.data['status']
        }

        self.print_output(self.data)

        sys.exit(self.data['status'])

    def print_output(self, data):
        """
            Print output.
            This function has to be implemented in child classes.

            The data sent to this function has the following structure :

                {
                    'name': <scenario's name>,
                    'status': <scenario's return code>,
                    'message': <error message or success message>,
                    'stats': {
                        'global': {
                            'timeperiod': <amount of time passed on scenario execution>,
                            'status': <scenario's status>
                        },
                        '<testname>': {
                            'timeperiod': <amout of time passed on a single test execution>,
                            'status': <step's status>
                        },
                        ...
                    }
                }

            :param data: Dictionnary containing data to output.
            :type data: dict
        """

        print data

class ScenarioNagios(Scenario):
    """
        Describe a sikuli scenario with Nagios compatible output.
    """

    statusmap = ['OK', 'WARNING', 'CRITICAL', 'UNKNOWN']

    def print_output(self, data):
        # Generate message

        if data['status'] >= len(self.statusmap):
            data['status'] = 3

        output = '%s %s: %s' % (
            data['name'],
            self.statusmap[data['status']],
            data['message'])

        if data['stats']:
            output += '|'

            for key in data['stats']:
                output += '%s=%.3fs ' % (key, data['stats'][key]['timeperiod'])

            # remove last space
            output = output[:-1]

        print output


class ScenarioNsca(Scenario):
    """
        Describe a sikuli scenario with NSCA compatible output.
    """

    statusmap = [pynsca.OK, pynsca.WARNING, pynsca.CRITICAL, pynsca.UNKNOWN]

    def __init__(self, nagios_host="localhost", nagios_port=5667, host="localhost", service=None, password=None, *args, **kwargs):
        """
            Initialize scenario.

            :param name: Scenario's name (default: "Sikuli").
            :type name: basestring

            :param nagios_host: Nagios hostname (default: "localhost").
            :type nagios_host: basestring

            :param nagios_port: Nagios port (default: 5667).
            :type nagios_port: int

            :param host: Check associated hostname.
            :type host: basestring

            :param service: Check associated service (default: scenario's name).
            :type service: basestring
        """

        super(ScenarioNsca, self).__init__(*args, **kwargs)

        self.nagios_host = nagios_host
        self.nagios_port = nagios_port

        self.host = host
        self.service = service or self.name
        self.password = password

    def print_output(self, data):
        # Generate message
        if data['status'] >= len(self.statusmap):
            data['status'] = 3

        output = data['message']

        if data['stats']:
            output += '|'

            for key in data['stats']:
                output += '%s=%.3fs ' % (key, data['stats'][key]['timeperiod'])

            # remove last space
            output = output[:-1]

        print '%s;%s;%s;%s' % (
            self.host,
            self.service,
            self.statusmap[data['status']],
            output)

        # Send result
        notifier = pynsca.NSCANotifier(self.nagios_host, self.nagios_port, password=self.password)

        notifier.svc_result(
            self.host,
            self.service,
            self.statusmap[data['status']],
            output)


class ScenarioCanopsis(Scenario):
    """
        Describe a sikuli scenario with Canopsis output.
        This scenario will not print anything, it will just send
        output to the Canopsis AMQP bus.
    """

    def __init__(self, host="127.0.0.1", port=5672, user="guest", password="guest", vhost="canopsis", exchange="canopsis.events", *args, **kwargs):
        """
            Initialize scenario.

            NB: The scenario's name is used to generate the event's routing key.

            :param host: RabbitMQ hostname (default: 127.0.0.1).
            :type host: basestring

            :param port: RabbitMQ port (default: 5672).
            :type port: int

            :param user: RabbitMQ username (default: guest).
            :type user: basestring

            :param password: RabbitMQ password for user (default: guest).
            :type password: basestring

            :param vhost: RabbitMQ virtual host (default: canopsis).
            :type vhost: basestring

            :param exchange: RabbitMQ exchange name (default: canopsis.events).
            :type exchange: basestring
        """

        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.vhost = vhost
        self.exchange = exchange

        super(ScenarioCanopsis, self).__init__(*args, **kwargs)

    def event_get_rk(self, event):
        """
            Generate routing key for event.

            @param event AMQP event.
            @type event dict

            @return Routing Key (as basestring)
        """

        rk = "%s.%s.%s.%s.%s" % (event['connector'], event['connector_name'], event['event_type'], event['source_type'], event['component'])

        if event['source_type'] == 'resource':
            rk += '.%s' % event['resource']

        return rk

    def send_event(self, event):
        """
            Send event to AMQP bus.

            @param event AMQP event to send.
            @type event dict
        """

        from kombu import Connection
        from kombu.pools import producers

        conn = Connection(hostname=self.host, userid=self.user, virtual_host=self.vhost)

        producer = producers[conn].acquire(block=True)
        producer.publish(
            event,
            serializer='json',
            exchange=self.exchange,
            routing_key=self.event_get_rk(event)
        )
        producer.release()

        conn.release()


    def print_output(self, data):
        import time

        # Send the component
        event = {
            'timestamp': int(time.time()),
            'connector': 'sikuli',
            'connector_name': data['name'],
            'component': 'scenario',
            'source_type': 'component',
            'event_type': 'check',
            'state': data['status'],
            'output': data['message'],
        }

        print '-- Send event: ', event
        self.send_event(event)

        # Send all statistics
        for stat in data['stats']:
            state = data['stats'][stat]['status']
            timeperiod = data['stats'][stat]['timeperiod']
            output = 'Passed' if state == 0 else 'Failed'

            event = {
                'timestamp': int(time.time()),
                'connector': 'sikuli',
                'connector_name': data['name'],
                'component': 'scenario',
                'source_type': 'resource',
                'resource': stat,
                'event_type': 'check',
                'state': state,
                'output': output,
                'perf_data_array': [
                    {'metric': 'timeperiod', 'value': timeperiod, 'type': 'GAUGE'},
                ]
            }
        
            print '-- Send event: ', event
            self.send_event(event)
