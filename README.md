# APM Brick

The Application Performance Manager brick provides tools for advanced checks in Canopsis.

To install all tools provided by the APM brick :

     # sudo make all install

## Widgets

### Scheduler

This widget allows the user to visualize scheduled checks.
It needs the engine ``event_link`` to be enabled and at least Highstock 1.3.7

     # sudo make -C widgets scheduler-install

## Contrib

The following tools aren't installed by the global procedure.
They are entirely optionals.

### sikulitest

Provide a ``Scenario`` class similar to the ``unittest.TestCase`` class, in order to ease the development
of Sikuli test scenarios.

This package contains 4 classes, in the module ``scenario`` :

- Scenario : returns the performance data as a dict
- ScenarioNagios : display the performance data in a Nagios plugin compatible format
- ScenarioNSCA : display the performance data in a NSCA compatible format
- ScenarioCanopsis : send the performance data to the AMQP bus of Canopsis

To use it, you need to include the package to your Sikuli project.

