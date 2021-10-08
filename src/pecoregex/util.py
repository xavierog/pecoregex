"""
Provide various functions that aim to process and dump a "document" describing multiple regex patterns to compile and
execute over given subject strings.
"""

import sys
import json
import yaml
from . import document as doc_key
from . import pcre

INDENT = '  '

def normalise_constant(name):
	"""
	Assume the given name is a PCRE_* constant and normalise it.
	"""
	name = name.upper()
	if not name.startswith('PCRE_'):
		name = 'PCRE_' + name
	return name

def constant(name):
	"""
	getattr()-based helper to fetch the value of a PCRE_* constant.
	Return None if the constant does not exist.
	"""
	return getattr(pcre, normalise_constant(name), None)

def extract_options(arg_values):
	"""
	Extract PCRE option names.
	arg_values can be either a string or a list of strings.
	Each string may contain multiple options separated with a pipe character '|'.
	"""
	if not isinstance(arg_values, list):
		arg_values = [arg_values]
	for value in arg_values:
		for option in value.split('|'):
			option = option.strip()
			if option:
				yield option

def normalise_options(options):
	"""
	Normalise a set of PCRE options.
	Return an array of PCRE_* constant. Unknown constants are dropped.
	"""
	normalised = []
	for name in extract_options(options):
		normalised_name = normalise_constant(name)
		if constant(normalised_name) is not None:
			normalised.append(normalised_name)
	return normalised

def extract_option_values(arg_values):
	"""
	Same as extract_options() but yield actual constant values, not names.
	Names that cannot be turned into a value generate a warning on stderr.
	"""
	for option in extract_options(arg_values):
		value = constant(option)
		if value is None:
			sys.stderr.write(f'Warning: ignoring unknown constant "{option}"\n')
		else:
			yield value

def or_options(values, initial_value=0):
	"""
	Combine all given values using binary OR.
	"""
	options = initial_value
	for value in values:
		options |= value
	return options

def normalise_doc_options(doc):
	"""
	Normalise all PCRE options found in the given pecoregeex document.
	"""
	def normalise(obj, key, check_key=True, ignore_int=True):
		if (check_key and key not in obj) or (ignore_int and isinstance(obj[key], int)):
			return
		obj[key] = normalise_options(obj[key])
	for key in (doc_key.REFERENCE_COMPILE_OPTIONS, doc_key.REFERENCE_EXECUTE_OPTIONS):
		if key in doc:
			for index in range(len(doc[key])):
				normalise(doc[key], index, check_key=False, ignore_int=False)
	for pattern in doc.get(doc_key.PATTERNS, []):
		normalise(pattern, doc_key.COMPILE_OPTIONS)
		for exe in pattern.get(doc_key.EXECUTE, []):
			normalise(exe, doc_key.EXECUTE_OPTIONS)

def get_value(obj, key, reference, default=None):
	"""
	Return the actual value described by obj[key].
	If obj[key] is not an integer, return it directly.
	Otherwise, consider obj[key] as an index within the reference list.
	If obj[key] is unreachable, return default.
	If default is None, raise the encoutered exception (either IndexError or KeyError).
	"""
	try:
		val = obj[key]
		return reference[val] if isinstance(val, int) else val
	except KeyError:
		if default is None:
			raise
		return default
	except IndexError:
		if default is None:
			raise
		return default

def add_compile_keys_to_pattern(pattern):
	"""
	Inject the "compile" and "error" keys so that they appear *before* the "execute" key.
	"""
	execute_in_pattern = doc_key.EXECUTE in pattern
	if execute_in_pattern:
		pattern_execute = pattern.pop(doc_key.EXECUTE)

	pattern[doc_key.COMPILE] = True
	if doc_key.ERROR not in pattern:
		pattern[doc_key.ERROR] = {}
	pattern[doc_key.ERROR][doc_key.ERROR_MESSAGE] = None
	pattern[doc_key.ERROR][doc_key.ERROR_OFFSET] = None

	if execute_in_pattern:
		pattern[doc_key.EXECUTE] = pattern_execute
	return pattern

def process(doc, **pcre_library_args):
	"""
	Process a pecoregex "document". Patterns are compiled and the success of each compilation is reflected through the
	"compile" attribute (either true of false). If the compilation failed, error.message and error.offset provide more
	details; otherwise, they are null.
	For each pattern, its 0 to n associated subjects are matched against it, thus filling the "match" attribute (either
	true or false). Captures are made available through captures.by_index (array/list) and captures.by_name
	(object/dict).
	"""
	if doc_key.PATTERNS not in doc: # nothing to do
		return doc

	# The doc may provide various references:
	pattern_strings = doc.get(doc_key.REFERENCE_PATTERN_STRINGS, [])
	subject_strings = doc.get(doc_key.REFERENCE_SUBJECT_STRINGS, [])
	compile_options = doc.get(doc_key.REFERENCE_COMPILE_OPTIONS, [])
	execute_options = doc.get(doc_key.REFERENCE_EXECUTE_OPTIONS, [])

	lib = pcre.PCRELibrary(**pcre_library_args)

	for pattern in doc[doc_key.PATTERNS]:
		# Compilation phase:
		add_compile_keys_to_pattern(pattern)
		value = get_value(pattern, doc_key.PATTERN_VALUE, pattern_strings)
		options = get_value(pattern, doc_key.COMPILE_OPTIONS, compile_options, [])
		try:
			code = lib.compile(value, or_options(extract_option_values(options)))
		except pcre.PCRECompileException as exc:
			pattern[doc_key.COMPILE] = False
			pattern[doc_key.ERROR][doc_key.ERROR_MESSAGE] = exc.error
			pattern[doc_key.ERROR][doc_key.ERROR_OFFSET] = exc.offset
		if not pattern[doc_key.COMPILE]:
			continue
		# Execution phase:
		for exe in pattern.get(doc_key.EXECUTE, []):
			value = get_value(exe, doc_key.SUBJECT, subject_strings)
			options = get_value(exe, doc_key.EXECUTE_OPTIONS, execute_options, [])
			exe_result = lib.exec(code, value, or_options(extract_option_values(options)))
			exe[doc_key.MATCH] = bool(exe_result)
			exe[doc_key.CAPTURES] = exe_result if exe_result else {}
		lib.free(code)
	return doc

def dump_doc_json(doc, filedesc=sys.stdout, indent=2):
	"""
	Dump a pecoregex document as JSON.
	"""
	json.dump(doc, filedesc, indent=indent)
	sys.stdout.write('\n')

def dump_doc_yaml(doc):
	"""
	Dump a pecoregex document as YAML.
	"""
	yaml.dump(doc, sys.stdout)

def dump_doc_console(doc, *args, **kwargs):
	"""
	Dump a pecoregex document as plain text.
	"""
	if doc_key.PATTERNS not in doc: # nothing to do
		return

	def say(*objects):
		print(*args, *objects, **kwargs)

	def dump_captures(captures):
		for capt_key, capt_value in captures:
			say(INDENT*3 + f'[{capt_key}] {capt_value}')

	# The doc may provide various references:
	pattern_strings = doc.get(doc_key.REFERENCE_PATTERN_STRINGS, [])
	subject_strings = doc.get(doc_key.REFERENCE_SUBJECT_STRINGS, [])
	compile_options = doc.get(doc_key.REFERENCE_COMPILE_OPTIONS, [])
	execute_options = doc.get(doc_key.REFERENCE_EXECUTE_OPTIONS, [])

	for pattern_index, pattern in enumerate(doc[doc_key.PATTERNS], 1):
		value = get_value(pattern, doc_key.PATTERN_VALUE, pattern_strings)
		options = get_value(pattern, doc_key.COMPILE_OPTIONS, compile_options, [])
		say('Pattern #' + str(pattern_index) + ':', value)
		say(INDENT + 'Options:', options)
		say(INDENT + 'Compilation:', pattern[doc_key.COMPILE])
		if not pattern[doc_key.COMPILE]:
			say(INDENT + 'Error message:', pattern[doc_key.ERROR][doc_key.ERROR_MESSAGE])
			say(INDENT + 'Error offset:', pattern[doc_key.ERROR][doc_key.ERROR_OFFSET])
			continue
		if doc_key.EXECUTE not in pattern:
			continue
		for index, exe in enumerate(pattern[doc_key.EXECUTE], 1):
			value = get_value(exe, doc_key.SUBJECT, subject_strings)
			options = get_value(exe, doc_key.EXECUTE_OPTIONS, execute_options, [])
			say(INDENT + 'Subject #' + str(index) + ':', value)
			say(INDENT + 'Options:', options)
			say(INDENT*2 + 'Match:', exe[doc_key.MATCH])
			if doc_key.CAPTURES in exe and exe[doc_key.CAPTURES]:
				if 'by_index' in exe[doc_key.CAPTURES]:
					say(INDENT*2 + 'Captures by index:')
					dump_captures(enumerate(exe[doc_key.CAPTURES]['by_index']))
				if 'by_name' in exe[doc_key.CAPTURES]:
					say(INDENT*2 + 'Captures by name:')
					dump_captures(exe[doc_key.CAPTURES]['by_name'].items())
