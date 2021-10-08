"""
This module provides a few factory classes as convenient ways to build common Pecoregex documents.
"""
from . import document as doc_key

class DocumentFactoryCompileOnly:
	"""
	Factory to make a pecoregex document that compiles n patterns.
	"""
	def __init__(self, initial_patterns=None, compile_options=None, meta=None):
		self.meta = meta
		self.patterns = []
		if initial_patterns is not None:
			for pattern in initial_patterns:
				self.add_pattern(pattern, compile_options)

	def add_pattern(self, pattern, compile_options=None, meta=None):
		"""
		Add the provided PCRE pattern to the Pecoregex document.
		"""
		pattern = {doc_key.PATTERN_VALUE: pattern}
		if compile_options:
			pattern[doc_key.COMPILE_OPTIONS] = compile_options
		if meta:
			pattern['meta'] = meta
		self.patterns.append(pattern)

	def make_doc(self):
		"""
		Return the desired Pecoregex document.
		"""
		return {
			'meta': self.meta,
			doc_key.PATTERNS: self.patterns,
		}

class DocumentFactory1n:
	"""
	Factory to make a pecoregex document that matches one subject against n patterns.
	"""
	def __init__(self, subject, meta=None):
		self.subject = subject
		self.execute = [{doc_key.SUBJECT: 0}]
		self.patterns = []
		self.meta = meta

	def add_pattern(self, pattern, options=None, meta=None):
		"""
		Add the provided PCRE pattern to the Pecoregex document.
		"""
		pattern = {doc_key.PATTERN_VALUE: pattern, doc_key.EXECUTE: self.execute}
		if options is not None:
			pattern[doc_key.COMPILE_OPTIONS] = options
		if meta:
			pattern['meta'] = meta
		self.patterns.append(pattern)

	def make_doc(self):
		"""
		Return the desired Pecoregex document.
		"""
		return {
			'meta': self.meta,
			doc_key.REFERENCE_SUBJECT_STRINGS: [self.subject],
			doc_key.PATTERNS: self.patterns,
		}

class DocumentFactoryn1:
	"""
	Factory to make a pecoregex document that matches n subjects against a single pattern.
	"""
	def __init__(self, pattern, compile_options=None, meta=None):
		self.pattern = {
			doc_key.PATTERN_VALUE: pattern,
			doc_key.EXECUTE: []
		}
		if compile_options is not None:
			self.pattern[doc_key.COMPILE_OPTIONS] = compile_options
		self.meta = meta

	def add_subject(self, subject_string, options=None, meta=None):
		"""
		Add the provided subject to the Pecoregex document.
		"""
		subject = {doc_key.SUBJECT: subject_string}
		if options is not None:
			subject[doc_key.EXECUTE_OPTIONS] = options
		if meta is not None:
			subject['meta'] = meta
		self.pattern[doc_key.EXECUTE].append(subject)

	def make_doc(self):
		"""
		Return the desired Pecoregex document.
		"""
		return {
			'meta': self.meta,
			doc_key.PATTERNS: [self.pattern],
		}
