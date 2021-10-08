# PECOREGEX

Pecoregex stands for Perl-Compatible Regular Expression, better known as PCRE.
Pecoregex is [python-pcre](https://github.com/awahlig/python-pcre)'s weird little cousin: like python-pcre, pecoregex
acts as a bridge between Python and libpcre.

The key differences are:

- pecoregex relies on ctypes to load and leverage libpcre.so; consequently, it can be installed without compiling
  anything;

- pecoregex only provides access to the most essential features of libpcre: compiling and executing regexes (including
  retrieving captures); other features such as study(), JIT or sub() were not considered (yet?).

## Modules

The pecoregex package provides multiple modules:

- pecoregex.pcre provides PCRE\_\* constants and the PCRELibrary class; this is the part that actually interacts with
  libpcre.so; it can be used directly or through the other modules that build upon it;

- pecoregex.document defines key names for the Pecoregex document format; Pecoregex documents are a way to bundle 1 to n
  PCRE patterns along with 0 to n subjects each.

- pecoregex.factory provides helpers to build common Pecoregex documents (e.g. "1 subject, n patterns" documents);

- pecoregex.util provides functions to process Pecoregex documents, i.e. compile the PCRE patterns they contain and
  match their associated subject strings against them;

- pecoregex.cli is typically invoked through the `pecoregex` CLI tool; it provides a mean to compile and execute PCRE
  patterns: patterns and subjects are provided either as command-line arguments or by passing a Pecoregex document on
  the standard input (as JSON or YAML); supported output formats include text, JSON and YAML; therefore, it is perfectly
  possible to compile and execute multiple PCRE patterns and subjects before picking up their captures using `jq`.

- pecoregex.extproc provides simple subprocess-based wrappers that leverage pecoregex.cli to compile and execute PCRE
  patterns in a separate process; this is meant for all those who consider calling C functions from Python as a threat
  to the reliability of their program.

## License
This Python package and its modules are released under the 3-clause BSD license.
