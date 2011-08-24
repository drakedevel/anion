To run Anion/Cation:

./{anion,cation}.py <config>

Or, to take advantage of multiple cores:

./multidriver.sh ./{anion,cation}.py <config> <ncores>

The configuration files are Python ConfigParser files, which look like INI
files. Documentation on all available configuration options is available in
examples/config-{anion,cation}.

Once configured, Anion is pretty hands-off. Run it on as many cores as you
like and as many times as you like and it will dump crashes/segfaults/etc
into results-<configname> organized by crash type and backtrace/signature.

Cation is a little more involved. Add "CATION:<TAG>\n" printfs to the code
wherever you encounter something you wish to count (e.g. when a move instruction
is emitted), and identify the value of <TAG> in the configuration file (see the
example file). Cation will run tests and save test cases organized by win/loss,
as well as keeping track of how bad good/bad each win/loss was in the scorecard
file. `sort -n loss/scorecard | tail` is probably the most effective way to
view these files.

Anion and Cation share the generator API, which is about as simple as it gets.
Simply produce a valid, standalone JavaScript blob on standard out, and ensure
that it does not print any lines beginning with "DRIVER:" or "CATION:".
Producing invalid JavaScript will produce bogus failures, and producing lines
beginning with those prefixes will screw up the driver and/or Cation. There's
a simple but surprisingly effective general purpose generator included, and
writing special case generators tends to be both productive and easy.
