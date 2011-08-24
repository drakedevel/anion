#!/usr/bin/env python
import ConfigParser
from common import *
import random
import shlex
import sys

def spam(c):
    if r.randrange(0, sample_factor) == 0:
        sys.stdout.write(c)

def alert(s):
    sys.stdout.write('!\n%s\n' % s)

if __name__ == '__main__':
    # Load configuration
    if len(sys.argv) < 2:
        print "Usage: anion.py <config>"
        sys.exit(1)

    defaults = {
        'driver-script' : 'driver.js',
        'triage-binary' : './triage.sh',
        'generator-options' : '',
        'script-timeout' : '1',
        'test-options' : '',
        'ref-options' : '',
        'sample-factor' : '1'
        }
    config = ConfigParser.RawConfigParser(defaults, dict, True)
    if not config.read(sys.argv[1]):
        print "Failed to open/parse config file"
        sys.exit(1)

    # Build relevant global objects from config
    try:
        r = random.Random()
        sample_factor = config.getint('anion', 'sample-factor')
        config_name = config.get('anion', 'config-name')
        test_shell = JsShell(config.get('anion', 'test-binary'),
                             shlex.split(config.get('anion', 'test-options')),
                             config.get('anion', 'driver-script'))
        ref_shell = JsShell(config.get('anion', 'ref-binary'),
                            shlex.split(config.get('anion', 'ref-options')),
                            config.get('anion', 'driver-script'))
        triage_binary = config.get('anion', 'triage-binary')
        generator = TestGenerator(config.get('anion', 'generator-binary'),
                                  shlex.split(config.get('anion', 'generator-options')),
                                  config.get('anion', 'script-timeout'))
    except ConfigParser.NoOptionError as opt:
        print "Missing configuration option '%s' in section '%s'" % (opt.option, opt.section)
        sys.exit(1)

    # Run a bunch of tests
    try:
        while True:
            test = generator.generate()
            (code, output) = test_shell.run_test(test)
            if code == 0 or code == -9 or code == 6:
                # Test completed successfully or ilooped
                (_, ref_output) = ref_shell.run_test(test)
                if output == ref_output:
                    if code == 0:
                        spam('.')
                    else:
                        spam('z')
                        save_testcase(config_name, test, 'sleepy')
                else:
                    alert('Wrong answer')
                    save_output(config_name, test, output, ref_output, 'divergences')
            elif code == -6:
                # Died with SIGABRT
                if ignore_assertion(output):
                    spam('-')
                elif save_crash(config_name, triage_binary, test_shell, test, output, 'assertions'):
                    if len(output):
                        alert(output[-1])
                    else:
                        alert('Silent abort')
                else:
                    spam('+')
            elif code == -11:
                # Died with SIGSEGV
                if save_crash(config_name, triage_binary, test_shell, test, output, 'segfaults'):
                    alert('Segmentation fault')
                else:
                    spam('+')
            else:
                # Died with something strange
                alert('Unexpected exit code %d' % code)
                if code < 0:
                    save_testcase(config_name, test, 'signal-%d' % -code)
                else:
                    save_testcase(config_name, test, 'exit-%d' % code)
    except KeyboardInterrupt:
        pass
