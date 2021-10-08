#!/usr/bin/env python3
"""
Provide a Command-Line Interface (CLI) able to compile and execute multiple patterns.
These patterns and their associated subjects can be read from either a YAML/JSON document passed on stdin or from
command-line arguments.
"""
import argparse
import sys
import yaml
from . import util
from . import document as doc_key

def init_arg_parser(input_mode=False):
	"""
	Initialise the argparse object used to parse command-line arguments.
	"""
	desc = 'Evaluate Perl-Compatible Regular Expressions (PCRE)'
	if input_mode:
		desc += '\nThis message describes input mode. Remove -in to read about default mode.'
	else:
		desc += '\nThis message describes default mode. Use -h -in to read about input mode.'

	if input_mode:
		epilog = None
	else:
		epilog = '''
COMPILE_OPTIONS and EXECUTE_OPTIONS format:
- PCRE_* options from pcre.h, e.g. PCRE_NO_AUTO_CAPTURE
- "PCRE_" prefix optional, e.g. NO_AUTO_CAPTURE
- case does not matter, e.g. no_auto_capture
- support for multiple options per argument, separated with '|'
  spaces are stripped, leading/trailing pipes do not matter
Examples:
  --compile-options='PCRE_ANCHORED|PCRE_NO_AUTO_CAPTURE'
  --execute-options '| PCRE_NO_UTF8_CHECK | NO_START_OPTIMIZE'
  -co caseless anchored no_auto_capture
By default, options are normalised and unknown ones are silently discarded.
However, when option normalisation is disabled, unknown options trigger a warning on stderr.
'''
	formatter = argparse.RawDescriptionHelpFormatter
	parser = argparse.ArgumentParser(prog='pecoregex', description=desc, epilog=epilog, formatter_class=formatter)
	return parser

def add_common_args(parser):
	"""
	Add arguments common to both default and input modes to the given argparse object.
	"""
	out_choices = ['json', 'yaml', 'console']
	parser.add_argument('--output', '-out', choices=out_choices, default='console', help='output format')
	parser.add_argument('--no-norm', action='store_false', dest='normalise_options', help='do not normalise options')

def parse_input_args():
	"""
	Parse command-line arguments in "input mode".
	"""
	parser = init_arg_parser(True)
	parser.add_argument('--input', '-in', default=sys.stdin, type=argparse.FileType('r'), metavar='DOCUMENT')
	add_common_args(parser)
	return parser.parse_args()

def parse_args():
	"""
	Parse command-line arguments in "default mode".
	"""
	parser = init_arg_parser()
	# Main arguments: patterns and subjects:
	parser.add_argument('pattern', nargs='+', help='PCRE patterns (at least one)')
	parser.add_argument('--subject', '-S', nargs='*', help='subjects to match against all patterns')

	# PCRE popular options:
	parser.add_argument('--caseless', '--ignore-case', '--case-insensitive', '-i',
	                    dest='compile_caseless', action='store_true',
	                    help='ignore case; same as (?i) or -co caseless')
	parser.add_argument('--duplicate-names', '-J',
	                    dest='compile_dupnames', action='store_true',
	                    help='allow duplicate names; same as (?J) or -ci dupnames')
	parser.add_argument('--multiline', '-m',
	                    dest='compile_multiline', action='store_true',
	                    help='multiline; same as (?m) or -co multiline')
	parser.add_argument('--dot-all', '--single-line', '-s',
	                    dest='compile_dotall', action='store_true',
	                    help='single line / dotall; same as (?s) or -co dotall')
	parser.add_argument('--ungreedy', '--lazy', '-u', '-U',
	                    dest='compile_ungreedy', action='store_true',
	                    help='ungreedy / lazy; same as (?U) or -co ungreedy')
	parser.add_argument('--extended', '--free-spacing', '-x', # --verbose? Here? Really? Nah, sounds like a bad idea.
	                    dest='compile_extended', action='store_true',
	                    help='extended / free-spacing mode; same as (?x) or -co extended')

	# Arbitrary options:
	parser.add_argument('--compile-options', '-co', nargs='*', help='Arbitrary compile options')
	parser.add_argument('--execute-options', '-eo', nargs='*', help='Arbitrary execute options')

	add_common_args(parser)
	return parser.parse_args()

def args_options(args, prefix, arbitrary=None):
	"""
	Extract PCRE options from command-line arguments.
	This function assumes the relevant arguments follow this pattern: <prefix>_<value>, e.g. "compile_dupnames".
	arbitrary is the name of an argument that allows arbitrary PCRE options.
	"""
	options = []
	for arg, value in args.__dict__.items():
		if arg == arbitrary and value:
			options.extend(util.extract_options(value))
		elif arg.startswith(prefix) and value:
			options.append(arg.replace(prefix, '', 1))
	return options

def _exit(doc, args):
	"""
	Output the given pecoregex document in the adequate format (text, JSON, YAML) based on command-line arguments.
	"""
	if args.output == 'json':
		util.dump_doc_json(doc)
	elif args.output == 'yaml':
		util.dump_doc_yaml(doc)
	else:
		util.dump_doc_console(doc)
	sys.exit(0)

def doc_from_args(args):
	"""
	Return a brand new pecoregex document based on command-line arguments.
	"""
	compile_options = args_options(args, 'compile_', 'compile_options')
	execute_options = args_options(args, 'execute_', 'execute_options')
	patterns = []
	for pattern in args.pattern:
		patterns.append({doc_key.PATTERN_VALUE: pattern, doc_key.COMPILE_OPTIONS: 0})
		if args.subject:
			execute = []
			for subject in args.subject:
				execute.append({doc_key.SUBJECT: subject, doc_key.EXECUTE_OPTIONS: 0})
			patterns[-1][doc_key.EXECUTE] = execute
	return {
		doc_key.REFERENCE_COMPILE_OPTIONS: [compile_options],
		doc_key.REFERENCE_EXECUTE_OPTIONS: [execute_options],
		doc_key.PATTERNS: patterns,
	}

def run_cli():
	"""
	Read a pecoregex document from stdin ("input mode") or create one based on command-line arguments ("default mode"),
	process it and output it.
	"""
	if '-in' in sys.argv or '--input' in sys.argv:
		args = parse_input_args()
		doc = yaml.safe_load(args.input)
	else:
		args = parse_args()
		doc = doc_from_args(args)
	if args.normalise_options:
		util.normalise_doc_options(doc)
	doc = util.process(doc)
	_exit(doc, args)

if __name__ == '__main__':
	run_cli()
