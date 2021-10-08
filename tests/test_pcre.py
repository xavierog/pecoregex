"""
Tests for pecoregex.pcre.
"""
import re
from ctypes import CDLL
import pytest
from pecoregex import pcre

# pylint: disable=C0111

def test_nametable_entry():
	entry = bytes((1, 0)) + b'hello' + bytes(28)
	index, name = pcre.nametable_entry(entry)
	assert index == 256
	assert name == 'hello'

def test_pcre_lib_constructor():
	lib = pcre.PCRELibrary(ovector_size=40, soname='libpcre.so.1', encode='ascii')
	assert lib.ovector_size == 40
	assert lib.encode == 'ascii'
	assert lib.decode == 'utf-8'
	assert lib.shared_object_name == 'libpcre.so.1'

def test_pcre_lib_get_lib():
	lib = pcre.PCRELibrary().get_lib()
	assert isinstance(lib, CDLL)

def test_pcre_lib_version():
	version = pcre.PCRELibrary().version()
	print(version)
	assert isinstance(version, str)
	assert re.match(r'''
^
\d+\.\d+        # version itself
\s+             # whitespace
\d{4}-\d\d-\d\d # date
$
''', version, re.VERBOSE)

def test_pcre_lib_config():
	lib = pcre.PCRELibrary()
	exceptions = (pcre.PCRE_CONFIG_UTF16, pcre.PCRE_CONFIG_UTF32)
	for i in exceptions:
		with pytest.raises(pcre.PCREErrorBadOption):
			lib.config(i)
	for i in range(13):
		if i in exceptions:
			continue
		value = lib.config(i)
		assert isinstance(value, pcre.CONFIG_OUTPUT_TYPE[i])
	# Not testing pcre.PCRE_CONFIG_PARENS_LIMIT (13) as it may not be present everywhere

def test_pcre_lib_caseless():
	lib = pcre.PCRELibrary()
	assert isinstance(lib.supports_caseless_utf8(), bool)

def test_pcre_lib_compile():
	lib = pcre.PCRELibrary()
	# Simple pattern:
	assert lib.compile('^hello') is not None
	# Simple pattern with legal options:
	assert lib.compile('hello', pcre.PCRE_ANCHORED|pcre.PCRE_CASELESS) is not None

	# Incorrect patterns:
	for pattern in ('^hello(', '^(?<namé>hello)'):
		with pytest.raises(pcre.PCRECompileException):
			lib.compile(pattern)

	# Correct pattern with conflicting options:
	with pytest.raises(pcre.PCRECompileException):
		lib.compile('hello', pcre.PCRE_UTF8|pcre.PCRE_NEVER_UTF)

def test_pcre_lib_exec():
	lib = pcre.PCRELibrary()
	# Simple pattern:
	pcre_code = lib.compile(r'^(?i)hello')
	assert lib.exec(pcre_code, 'Hello!')
	assert lib.exec(pcre_code, 'Oh, hello!') is False

	# Simple pattern with options:
	pcre_code = lib.compile(r'hello', pcre.PCRE_CASELESS|pcre.PCRE_ANCHORED)
	assert lib.exec(pcre_code, 'Hello!')
	assert lib.exec(pcre_code, 'Oh, hello!') is False

	# Captures:
	pcre_code = lib.compile(r'It is raining (?<rain1>\S+) and (?<rain2>\S+)')
	captures = lib.exec(pcre_code, 'It is raining cats and dogs')
	assert captures
	assert captures['by_index'][0] == 'It is raining cats and dogs'
	assert captures['by_index'][1] == 'cats'
	assert captures['by_index'][2] == 'dogs'
	assert captures['by_name']['rain1'] == 'cats'
	assert captures['by_name']['rain2'] == 'dogs'

	# UTF-8 matching:
	if lib.supports_caseless_utf8():
		pcre_code = lib.compile(r'éléphant', pcre.PCRE_UTF8|pcre.PCRE_CASELESS|pcre.PCRE_ANCHORED)
		assert lib.exec(pcre_code, 'Éléphant!')
		assert lib.exec(pcre_code, 'Oh, éléphant!') is False

def test_pcre_lib_exec_data_unit():
	lib = pcre.PCRELibrary(encode='utf-8', decode='iso-8859-15')
	pcre_code = lib.compile(r'\C(\Cl\C)\Cphant', pcre.PCRE_UTF8|pcre.PCRE_CASELESS)
	captures = lib.exec(pcre_code, 'éléphant')
	assert captures
	assert captures['by_index'][1] == '©lÃ'
	captures = lib.exec(pcre_code, 'ÉLÉPHANT')
	assert captures
	assert captures['by_index'][1] == '\x89LÃ'
	lib.free(pcre_code)
	assert True # still alive / no segfault

def test_pcre_lib_info_nametable():
	lib = pcre.PCRELibrary()
	pcre_code = lib.compile(r'''(?x)
^
(?<all>
	(?<dotdotdot>
		\.\.\.
	)
	(?<dashdashdash>
		---
	)
	(?<dotdotdotagain>
		\.\.\.
	)
)
$
''')
	expected_entries = 4
	expected_entry_size = 2 + len('dotdotdotagain\x00')
	expected_table_size = expected_entries * expected_entry_size
	assert lib.info_namecount(pcre_code) == expected_entries
	assert lib.info_nameentrysize(pcre_code) == expected_entry_size
	nametable = lib.info_nametable_data(pcre_code)
	nametable_bytes = nametable[0:expected_table_size]
	assert len(nametable_bytes) == expected_table_size # still alive

	nametable = lib.nametable(pcre_code)
	assert nametable
	assert len(nametable) == expected_entries

	ordered_nametable = lib.ordered_nametable(pcre_code)
	assert ordered_nametable == [None, 'all', 'dotdotdot', 'dashdashdash', 'dotdotdotagain']

def test_pcre_lib_match():
	res = pcre.PCRELibrary().match(r'''
/(?<prefix>[^/]+)
/(?<action>[^/]+)
/(?<value>.+)
''', '/just/do/it', pcre.PCRE_EXTENDED, pcre.PCRE_ANCHORED)
	assert res
	assert res['by_index'] == ['/just/do/it', 'just', 'do', 'it']
	assert res['by_name'] == {'action': 'do', 'prefix': 'just', 'value': 'it'}

def test_alternative_match():
	lib = pcre.PCRELibrary()
	alt_match_re = r'''
^(?:
	(?<name1>abc)
	(?<name2>def)
|
	(?<name3>ghi)
	(?<name4>jkl)
)$
'''
	pcre_code = lib.compile(alt_match_re, pcre.PCRE_EXTENDED)
	res = lib.exec(pcre_code, 'abcdef')
	assert res
	assert res['by_index'] == ['abcdef', 'abc', 'def']
	assert res['by_name'] == {'name1': 'abc', 'name2': 'def', 'name3': None, 'name4': None}
	res = lib.exec(pcre_code, 'ghijkl')
	assert res
	assert res['by_index'] == ['ghijkl', '', '', 'ghi', 'jkl']
	assert res['by_name'] == {'name1': '', 'name2': '', 'name3': 'ghi', 'name4': 'jkl'}
