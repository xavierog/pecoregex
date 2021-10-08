"""
Test for pecoregex.util.
"""
import pytest
from pecoregex import util
from pecoregex import document as doc_key

a = ' |||  |  caseless |dupnames|PCRE_UTF8'
b = [a, 'never_utf', 'PCRE_NO_START_OPTIMISE']
a_norm = ['PCRE_CASELESS', 'PCRE_DUPNAMES', 'PCRE_UTF8']
b_norm = ['PCRE_CASELESS', 'PCRE_DUPNAMES', 'PCRE_UTF8', 'PCRE_NEVER_UTF', 'PCRE_NO_START_OPTIMISE']

def test_normalise_constant():
	assert util.normalise_constant('foo') == 'PCRE_FOO'
	assert util.normalise_constant('2') == 'PCRE_2'
	assert util.normalise_constant('DUPNAMES') == 'PCRE_DUPNAMES'
	assert util.normalise_constant('dupnames') == 'PCRE_DUPNAMES'
	assert util.normalise_constant('pcre_dupnames') == 'PCRE_DUPNAMES'
	assert util.normalise_constant('PCRE_DUPNAMES') == 'PCRE_DUPNAMES'

def test_constant():
	assert util.constant('foo') is None
	assert util.constant('PCRE_FOO') is None
	assert util.constant('DUPNAMES') == 0x00080000
	assert util.constant('dupnames') == 0x00080000
	assert util.constant('pcre_dupnames') == 0x00080000
	assert util.constant('PCRE_DUPNAMES') == 0x00080000

def test_extract_options():
	assert list(util.extract_options(a)) == ['caseless', 'dupnames', 'PCRE_UTF8']
	assert list(util.extract_options(b)) == ['caseless', 'dupnames', 'PCRE_UTF8', 'never_utf', 'PCRE_NO_START_OPTIMISE']

def test_normalise_options():
	assert list(util.normalise_options(a)) == a_norm
	assert list(util.normalise_options(b)) == b_norm

def test_extract_option_values():
	assert list(util.extract_option_values(a)) == [0x00000001, 0x00080000, 0x00000800]
	assert list(util.extract_option_values(b)) == [0x00000001, 0x00080000, 0x00000800, 0x00010000, 0x04000000]

def test_or_options():
	assert util.or_options((1, 2, 4, 8, 16, 32, 64), 128) == 255
	assert util.or_options((0x20000000, 0x02000000)) == 0x22000000

def test_normalise_doc_options():
	doc = {
		doc_key.REFERENCE_COMPILE_OPTIONS: [a, list(b)],
		doc_key.REFERENCE_EXECUTE_OPTIONS: [a, list(b)],
		doc_key.PATTERNS: [
			{
				doc_key.PATTERN_VALUE: '^foo',
				doc_key.COMPILE_OPTIONS: a,
				doc_key.EXECUTE: [
					{
						doc_key.SUBJECT: 'foo',
						doc_key.EXECUTE_OPTIONS: list(b),
					},
				],
			},
		],
	}
	util.normalise_doc_options(doc)
	assert doc[doc_key.REFERENCE_COMPILE_OPTIONS] == [a_norm, b_norm]
	assert doc[doc_key.REFERENCE_EXECUTE_OPTIONS] == [a_norm, b_norm]
	assert doc[doc_key.PATTERNS][0][doc_key.COMPILE_OPTIONS] == a_norm
	assert doc[doc_key.PATTERNS][0][doc_key.EXECUTE][0][doc_key.EXECUTE_OPTIONS] == b_norm

def test_get_value():
	reference = ['foo', 'bar', 'baz']
	obj = {'value1': 'real_value!', 'value2': 2, 'value3': 3}
	assert util.get_value(obj, 'value1', reference, 'default!') == 'real_value!'
	assert util.get_value(obj, 'value2', reference, 'default!') == 'baz'
	assert util.get_value(obj, 'value3', reference, 'default!') == 'default!'
	assert util.get_value(obj, 'value4', reference, 'default!') == 'default!'
	with pytest.raises(IndexError):
		util.get_value(obj, 'value3', reference)
	with pytest.raises(KeyError):
		util.get_value(obj, 'value4', reference)

def test_add_compile_keys_to_pattern():
	pattern = {
		doc_key.EXECUTE: 'something',
	}
	util.add_compile_keys_to_pattern(pattern)
	assert doc_key.COMPILE in pattern
	assert doc_key.ERROR in pattern
	assert doc_key.ERROR_MESSAGE in pattern[doc_key.ERROR]
	assert doc_key.ERROR_OFFSET in pattern[doc_key.ERROR]
	assert doc_key.EXECUTE in pattern
	assert list(pattern.keys()) == ['compile', 'error', 'execute']

def test_process():
	# Helpers:
	def compilation_succeeded(pattern_id):
		pattern = doc[doc_key.PATTERNS][pattern_id]
		assert pattern[doc_key.COMPILE] is True
		assert pattern[doc_key.ERROR][doc_key.ERROR_MESSAGE] is None
		assert pattern[doc_key.ERROR][doc_key.ERROR_OFFSET] is None

	def regex_matched(pattern_id, exec_id, result=True):
		pattern = doc[doc_key.PATTERNS][pattern_id]
		exe = pattern[doc_key.EXECUTE][exec_id]
		assert exe[doc_key.MATCH] is result
		captures = exe[doc_key.CAPTURES]
		if result:
			assert list(captures.keys()) == ['by_index', 'by_name']
		else:
			assert captures == {}
	# Test document:
	doc = {
		doc_key.REFERENCE_COMPILE_OPTIONS: [
			'PCRE_CASELESS',
			'PCRE_ANCHORED',
			['PCRE_CASELESS', 'PCRE_ANCHORED'],
		],
		doc_key.REFERENCE_EXECUTE_OPTIONS: [
			'no_utf8_check|no_start_optimise',
		],
		doc_key.REFERENCE_PATTERN_STRINGS: [
			r'^',
			r'^/(?<prefix>[^/]+)/(?<animal>cat|dog|cow)(?<tail>.*)',
			r'''(?x) # PCRE extended mode
			^
			/(?<prefix>[^/]+)
			/(?<animal>cat|dog|cow)
			(?<tail>.*)
			'''
		],
		doc_key.REFERENCE_SUBJECT_STRINGS: [
			'hello',
			'/foo/cat/tail',
			'/bar/dog/tail',
			'moo',
		],
		doc_key.PATTERNS: [
			{ # this first pattern is described using exclusively references:
				doc_key.PATTERN_VALUE: 0,
				doc_key.COMPILE_OPTIONS: 0,
				doc_key.EXECUTE: [{
					doc_key.SUBJECT: 0,
					doc_key.EXECUTE_OPTIONS: 0,
				}],
			},
			{ # this second pattern is described using exclusively direct values:
				doc_key.PATTERN_VALUE: r'^(?:quack)+$',
				doc_key.COMPILE_OPTIONS: 'caseless',
				doc_key.EXECUTE: [
					{
						doc_key.SUBJECT: 'quack',
						doc_key.EXECUTE_OPTIONS: 'no_start_optimise',
					},
					{ doc_key.SUBJECT: 'QUACK' },
					{ doc_key.SUBJECT: 'quackquack' },
					{ doc_key.SUBJECT: 'QUACKQUACK' },
					{ doc_key.SUBJECT: 'QuAcKqUaCk' },
				],
			},
		]
	}
	util.process(doc)
	compilation_succeeded(0)
	compilation_succeeded(1)
	regex_matched(0, 0)
	for i in range(5):
		regex_matched(1, i)

	# Also test dump functions:
	util.dump_doc_json(doc)
	util.dump_doc_yaml(doc)
	util.dump_doc_console(doc)
	assert True
