#!/usr/bin/env python
import ConfigParser
from common import *
import random
import shlex
import sys

def spam(c):
    if r.randrange(0, sample_factor) == 0:
        sys.stdout.write(c)

def keep_score(config_name, low, high, test, category):
    f = open('results-%s/%s/scorecard' % (config_name, category), 'a+')
    if low:
        f.write('%.02f\t%s\n' % ((float(high) - float(low)) / float(low), test.hash))
    else:
        f.write('Infty\t%s\n' % test.hash)

if __name__ == '__main__':
    # Load configuration
    if len(sys.argv) < 2:
        print "Usage: cation.py <config>"
        sys.exit(1)

    defaults = {
        'driver-script' : 'driver.js',
        'generator-options' : '',
        'script-timeout' : '1',
        'a-options' : '',
        'b-options' : '',
        'sample-factor' : '1'
        }
    config = ConfigParser.RawConfigParser(defaults, dict, True)
    if not config.read(sys.argv[1]):
        print "Failed to open/parse config file"
        sys.exit(1)

    # Build relevant global objects from config
    try:
        r = random.Random()
        sample_factor = config.getint('cation', 'sample-factor')
        config_name = config.get('cation', 'config-name')
        a_shell = JsShell(config.get('cation', 'a-binary'),
                          shlex.split(config.get('cation', 'a-options')),
                          config.get('cation', 'driver-script'))
        b_shell = JsShell(config.get('cation', 'b-binary'),
                            shlex.split(config.get('cation', 'b-options')),
                            config.get('cation', 'driver-script'))
        generator = TestGenerator(config.get('cation', 'generator-binary'),
                                  shlex.split(config.get('cation', 'generator-options')),
                                  config.get('cation', 'script-timeout'))
        keyword = config.get('cation', 'keyword')
    except ConfigParser.NoOptionError as opt:
        print "Missing configuration option '%s' in section '%s'" % (opt.option, opt.section)
        sys.exit(1)

    # Run a bunch of tests
    try:
        while True:
            test = generator.generate()
            (a_code, a_output) = a_shell.run_test(test)
            if not (a_code == 0 or a_code == -9 or a_code == 6):
                spam('x')
                continue
            (b_code, b_output) = b_shell.run_test(test)
            if not (b_code == 0 or b_code == -9 or b_code == 6):
                spam('x')
                continue
            
            a_count = len([x for x in a_output if ("CATION:%s" % keyword) == x])
            b_count = len([x for x in b_output if ("CATION:%s" % keyword) == x])
            if a_count < b_count:
                spam('-')
                save_testcase(config_name, test, 'loss')
                keep_score(config_name, a_count, b_count, test, 'loss')
            elif a_count == b_count:
                spam('=')
            else:
                spam('+')
                save_testcase(config_name, test, 'win')
                keep_score(config_name, b_count, a_count, test, 'win')
    except KeyboardInterrupt:
        pass
