import hashlib
import os
import shutil
from subprocess import Popen, check_output, PIPE, STDOUT
import tempfile

class JsShell(object):
    def __init__(self, bin, opts, driver):
        self.command = [bin] + opts
        self._driver = self.command + [driver]
        self._process = None
        self._spawn()

    def _spawn(self):
        self._process = Popen(self._driver, bufsize=1,
                              stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        while True:
            line = self._process.stdout.readline()
            if not line:
                # Really unexpected EOF encountered
                raise Exception("I start the driver and I keep dying")
            line = line.rstrip()
            if line == "DRIVER:READY":
                break

    def _respawn(self):
        self._process.kill()
        code = self._process.wait()
        self._spawn()
        return code

    def run_test(self, f):
        assert self._process
        self._process.stdin.write(f.name + "\n")

        code = 0
        output = []
        while True:
            line = self._process.stdout.readline()
            if not line:
                # Unexpected EOF encountered
                code = self._respawn()
                break
            line = line.rstrip()
            if line == "Script runs for too long, terminating.":
                # Test timed out
                code = self._respawn()
                break
            if line == "DRIVER:OK":
                # Test completed successfully
                code = 0
                break
            output.append(line)
        return (code, output)

class TestGenerator(object):
    def __init__(self, bin, opts, timeout):
        self._args = [bin] + opts
        self._timeout = timeout

    def generate(self):
        tmp = tempfile.NamedTemporaryFile()
        tmp.write("timeout(%s);\n" % self._timeout)
        tmp.flush()
        process = Popen(self._args, bufsize=-1, stdout=tmp.fileno())
        process.wait()
        tmp.seek(0)
        m = hashlib.md5()
        m.update(tmp.read())
        tmp.hash = m.hexdigest()
        return tmp

def dump(f, s):
    f = open(f, 'w+')
    f.write(s)
    f.close()

def save_crash(config_name, triage_binary, shell, test, output, category):
    triage = check_output([triage_binary] + shell.command + [test.name])
    if len(output):
        triage = output[-1] + '\n' + triage
    m = hashlib.md5()
    m.update(triage)
    signature = m.hexdigest()
    dirname = 'results-%s/%s/%s' % (config_name, category, signature)
    try:
        os.makedirs(dirname)
        result = True
        dump('%s/signature' % dirname, triage)
    except OSError:
        result = False
    shutil.copy(test.name, '%s/%s.js' % (dirname, test.hash))
    return result

def save_output(config_name, test, output, ref_output, category):
    dirname = 'results-%s/%s' % (config_name, category)
    try:
        os.makedirs(dirname)
    except OSError:
        pass
    shutil.copy(test.name, '%s/%s.js' % (dirname, test.hash))
    dump('%s/%s.out' % (dirname, test.hash), '\n'.join(output))
    dump('%s/%s.ref' % (dirname, test.hash), '\n'.join(ref_output))

def save_testcase(config_name, test, category):
    dirname = 'results-%s/%s' % (config_name, category)
    try:
        os.makedirs(dirname)
    except OSError:
        pass
    shutil.copy(test.name, '%s/%s.js' % (dirname, test.hash))

def ignore_assertion(output):
    if len(output):
        return "NYI" in output[-1] or "implement" in output[-1]
    return False
