"""
Test for pecoregex.factory.
"""
import pytest
from pecoregex import factory
from pecoregex import document as doc_key
from pecoregex import extproc

def test_document_factory_compile():
	pdf = factory.DocumentFactoryCompileOnly([r'^hello', r'goodbye$'], ['PCRE_CASELESS'], 42)
	doc = pdf.make_doc()
	assert doc[doc_key.PATTERNS][0][doc_key.PATTERN_VALUE] == r'^hello'
	assert doc[doc_key.PATTERNS][0][doc_key.COMPILE_OPTIONS] == ['PCRE_CASELESS']
	assert doc[doc_key.PATTERNS][1][doc_key.PATTERN_VALUE] == r'goodbye$'
	assert doc[doc_key.PATTERNS][1][doc_key.COMPILE_OPTIONS] == ['PCRE_CASELESS']
	assert doc['meta'] == 42

	pdf.add_pattern(r'^(cat|dog)$', meta='meta')
	doc = pdf.make_doc()
	assert doc[doc_key.PATTERNS][2][doc_key.PATTERN_VALUE] == r'^(cat|dog)$'
	assert doc_key.COMPILE_OPTIONS not in doc[doc_key.PATTERNS][2]
	assert doc[doc_key.PATTERNS][2]['meta'] == 'meta'

def test_document_factory_1n():
	pdf = factory.DocumentFactory1n('hello', meta={'mykey': 'myvar'})
	assert pdf.subject == 'hello'
	assert pdf.meta['mykey'] == 'myvar'
	assert not len(pdf.patterns)

	pdf.add_pattern(r'^hello')
	pdf.add_pattern(r'^hello', ['PCRE_CASELESS'])
	pdf.add_pattern(r'goodbye$', ['PCRE_CASELESS'], 42)
	assert len(pdf.patterns) == 3

	doc = pdf.make_doc()
	assert doc[doc_key.REFERENCE_SUBJECT_STRINGS][0] == 'hello'
	assert len(doc[doc_key.PATTERNS]) == 3
	assert doc[doc_key.PATTERNS][0][doc_key.PATTERN_VALUE] == r'^hello'
	assert doc[doc_key.PATTERNS][1][doc_key.COMPILE_OPTIONS][0] == 'PCRE_CASELESS'
	assert doc[doc_key.PATTERNS][2][doc_key.COMPILE_OPTIONS][0] == 'PCRE_CASELESS'
	assert doc[doc_key.PATTERNS][2]['meta'] == 42

def test_document_factory_n1():
	pdf = factory.DocumentFactoryn1(r'^hello', meta={'mykey': 'myvar'})
	assert pdf.pattern[doc_key.PATTERN_VALUE] == r'^hello'
	assert pdf.meta['mykey'] == 'myvar'
	assert not len(pdf.pattern[doc_key.EXECUTE])

	pdf.add_subject('hello')
	pdf.add_subject('Hello', [])
	pdf.add_subject('HELLO', ['PCRE_CASELESS'])
	pdf.add_subject('HeLlO', meta=42)
	pdf.add_subject('Goodbye', ['PCRE_CASELESS'], meta=42)
	assert len(pdf.pattern[doc_key.EXECUTE]) == 5

	doc = pdf.make_doc()
	assert len(doc[doc_key.PATTERNS]) == 1
	assert doc[doc_key.PATTERNS][0][doc_key.PATTERN_VALUE] == r'^hello'
	assert len(doc[doc_key.PATTERNS][0][doc_key.EXECUTE]) == 5
	assert doc[doc_key.PATTERNS][0][doc_key.EXECUTE][0][doc_key.SUBJECT] == 'hello'
	assert doc[doc_key.PATTERNS][0][doc_key.EXECUTE][1][doc_key.EXECUTE_OPTIONS] == []
	assert doc[doc_key.PATTERNS][0][doc_key.EXECUTE][2][doc_key.EXECUTE_OPTIONS][0] == 'PCRE_CASELESS'
	assert doc[doc_key.PATTERNS][0][doc_key.EXECUTE][3]['meta'] == 42
	assert doc[doc_key.PATTERNS][0][doc_key.EXECUTE][4][doc_key.SUBJECT] == 'Goodbye'
	assert doc[doc_key.PATTERNS][0][doc_key.EXECUTE][4][doc_key.EXECUTE_OPTIONS][0] == 'PCRE_CASELESS'
	assert doc[doc_key.PATTERNS][0][doc_key.EXECUTE][4]['meta'] == 42

def test_extproc_cli():
	doc = factory.DocumentFactoryCompileOnly([r'^hello', r'goodbye$', r'unclosed(group']).make_doc()
	doc = extproc.cli(doc)
	patterns = doc[doc_key.PATTERNS]
	assert patterns[0][doc_key.COMPILE] is True
	assert patterns[0][doc_key.ERROR][doc_key.ERROR_MESSAGE] is None
	assert patterns[0][doc_key.ERROR][doc_key.ERROR_OFFSET] is None
	assert patterns[1][doc_key.COMPILE] is True
	assert patterns[1][doc_key.ERROR][doc_key.ERROR_MESSAGE] is None
	assert patterns[1][doc_key.ERROR][doc_key.ERROR_OFFSET] is None
	assert patterns[2][doc_key.COMPILE] is False
	assert patterns[2][doc_key.ERROR][doc_key.ERROR_MESSAGE] == 'missing )'
	assert patterns[2][doc_key.ERROR][doc_key.ERROR_OFFSET] == len(patterns[2][doc_key.PATTERN_VALUE])
	execute = [
		{doc_key.SUBJECT: 'hello world'},
		{doc_key.SUBJECT: 'well, goodbye'},
	]
	patterns[0][doc_key.EXECUTE] = patterns[1][doc_key.EXECUTE] = execute

	doc = extproc.cli(doc)
	patterns = doc[doc_key.PATTERNS]
	assert patterns[0][doc_key.EXECUTE][0][doc_key.MATCH] is True
	assert patterns[0][doc_key.EXECUTE][1][doc_key.MATCH] is False
	assert patterns[1][doc_key.EXECUTE][0][doc_key.MATCH] is False
	assert patterns[1][doc_key.EXECUTE][1][doc_key.MATCH] is True
