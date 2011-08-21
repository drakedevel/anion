This is known to work on Fedora 15 or newer (read: the versions of all relevant
utilities that the author happened to have installed). The shell scripts
extensively use bash extensions (some requiring as new as bash >= 4.2), so a
modern distro is likely required.

To use anion, read the "config options" section of anion.sh, produce a
configuration file with appropriate paths, and run ./multidriver.sh ./anion.sh
<configfile> <n> to run n instances of the fuzzer in parallel. Results will show
up in results-<configname>, organized by failure mode and signature hash.

Cation is a little more involved. Add "CATION:<TAG>\n" printfs to the code
wherever you encounter something you wish to count (e.g. when a move instruction
is emitted). Configuration works the same way as anion, except there are two
sets of parameters to the JS engine and you need to identify <TAG>.

The test generator API is shared between anion and cation and is as simple as it
gets. Just produce valid JavaScript on standard out (the fuzz driver will choke
if it gets invalid testcases). There's a simple but surprisingly effective
general purpose generator included, and writing special case generators is both
productive and easy.
