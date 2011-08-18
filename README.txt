This is known to work on Fedora 15 or newer (read: the versions of all relevant
utilities that the author happened to have installed). The shell scripts
extensively use bash extensions (some requiring as new as bash >= 4.2), so a
modern distro is likely required.

To use, read the "config options" of driver.sh, produce a configuration file
with appropriate paths, and run ./multidriver.sh <configfile> <n> to run n
instances of the fuzzer in parallel. Results will show up in
results-<configname>, organized by failure mode and signature hash.

The test generator API is as simple as it gets. Just produce valid JavaScript on
standard out (the fuzz driver will choke if it gets invalid testcases). There's
a simple but surprisingly effective general purpose generator included, and
writing special case generators is both productive and easy.
