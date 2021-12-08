"""
This modules provides:
- various PCRE_* constants from <pcre.h>
- access to the most popular libpcre functions: pcre_compile, pcre_exec, pcre_free
- wrappers around pcre_fullinfo, but only to access information about named captures
- a few other functions gravitating around everything above

This module leverages ctypes to dynamically load the pcre library (which must be present on the system) and call its
functions. Therefore, it does not require any kind of compilation when running "pip install pecoregex".
"""

import ctypes
from ctypes.util import find_library
from struct import unpack

# (almost) straight from pcre.h:
PCRE_CASELESS           = 0x00000001 # (?i)
PCRE_MULTILINE          = 0x00000002 # (?m)
PCRE_DOTALL             = 0x00000004 # (?s)
PCRE_EXTENDED           = 0x00000008 # (?x)
PCRE_ANCHORED           = 0x00000010 # \A
PCRE_DOLLAR_ENDONLY     = 0x00000020
PCRE_EXTRA              = 0x00000040 # (?X)
PCRE_NOTBOL             = 0x00000080
PCRE_NOTEOL             = 0x00000100
PCRE_UNGREEDY           = 0x00000200 # (?U)
PCRE_NOTEMPTY           = 0x00000400
PCRE_UTF8               = 0x00000800 # (*UTF8)
PCRE_UTF16              = 0x00000800 # (*UTF16)
PCRE_UTF32              = 0x00000800 # (*UTF32)
PCRE_NO_AUTO_CAPTURE    = 0x00001000
PCRE_NO_UTF8_CHECK      = 0x00002000
PCRE_NO_UTF16_CHECK     = 0x00002000
PCRE_NO_UTF32_CHECK     = 0x00002000
PCRE_AUTO_CALLOUT       = 0x00004000
PCRE_PARTIAL_SOFT       = 0x00008000
PCRE_PARTIAL            = 0x00008000
PCRE_NEVER_UTF          = 0x00010000
PCRE_DFA_SHORTEST       = 0x00010000
PCRE_NO_AUTO_POSSESS    = 0x00020000 # (*NO_AUTO_POSSESS)
PCRE_DFA_RESTART        = 0x00020000
PCRE_FIRSTLINE          = 0x00040000
PCRE_DUPNAMES           = 0x00080000 # (?J)
PCRE_NEWLINE_CR         = 0x00100000 # (*CR)
PCRE_NEWLINE_LF         = 0x00200000 # (*LF)
PCRE_NEWLINE_CRLF       = 0x00300000 # (*CRLF)
PCRE_NEWLINE_ANY        = 0x00400000 # (*ANY)
PCRE_NEWLINE_ANYCRLF    = 0x00500000 # (*ANYCRLF)
PCRE_BSR_ANYCRLF        = 0x00800000 # (*BSR_ANYCRLF)
PCRE_BSR_UNICODE        = 0x01000000 # (*BSR_UNICODE)
PCRE_JAVASCRIPT_COMPAT  = 0x02000000
PCRE_NO_START_OPTIMIZE  = 0x04000000 # (*NO_START_OPT)
PCRE_NO_START_OPTIMISE  = 0x04000000 # (*NO_START_OPT)
PCRE_PARTIAL_HARD       = 0x08000000
PCRE_NOTEMPTY_ATSTART   = 0x10000000
PCRE_UCP                = 0x20000000 # (*UCP)

PCRE_INFO_OPTIONS             = 0
PCRE_INFO_SIZE                = 1
PCRE_INFO_CAPTURECOUNT        = 2
PCRE_INFO_BACKREFMAX          = 3
PCRE_INFO_FIRSTBYTE           = 4
PCRE_INFO_FIRSTCHAR           = 4
PCRE_INFO_FIRSTTABLE          = 5
PCRE_INFO_LASTLITERAL         = 6
PCRE_INFO_NAMEENTRYSIZE       = 7
PCRE_INFO_NAMECOUNT           = 8
PCRE_INFO_NAMETABLE           = 9
PCRE_INFO_STUDYSIZE           = 10
PCRE_INFO_DEFAULT_TABLES      = 11
PCRE_INFO_OKPARTIAL           = 12
PCRE_INFO_JCHANGED            = 13
PCRE_INFO_HASCRORLF           = 14
PCRE_INFO_MINLENGTH           = 15
PCRE_INFO_JIT                 = 16
PCRE_INFO_JITSIZE             = 17
PCRE_INFO_MAXLOOKBEHIND       = 18
PCRE_INFO_FIRSTCHARACTER      = 19
PCRE_INFO_FIRSTCHARACTERFLAGS = 20
PCRE_INFO_REQUIREDCHAR        = 21
PCRE_INFO_REQUIREDCHARFLAGS   = 22

PCRE_CONFIG_UTF8                    = 0
PCRE_CONFIG_NEWLINE                 = 1
PCRE_CONFIG_LINK_SIZE               = 2
PCRE_CONFIG_POSIX_MALLOC_THRESHOLD  = 3
PCRE_CONFIG_MATCH_LIMIT             = 4
PCRE_CONFIG_STACKRECURSE            = 5
PCRE_CONFIG_UNICODE_PROPERTIES      = 6
PCRE_CONFIG_MATCH_LIMIT_RECURSION   = 7
PCRE_CONFIG_BSR                     = 8
PCRE_CONFIG_JIT                     = 9
PCRE_CONFIG_UTF16                   = 10
PCRE_CONFIG_JITTARGET               = 11
PCRE_CONFIG_UTF32                   = 12
PCRE_CONFIG_PARENS_LIMIT            = 13

CONFIG_OUTPUT_TYPE = {
	PCRE_CONFIG_UTF8: bool,
	PCRE_CONFIG_NEWLINE: int,
	PCRE_CONFIG_LINK_SIZE: int,
	PCRE_CONFIG_POSIX_MALLOC_THRESHOLD: int,
	PCRE_CONFIG_MATCH_LIMIT: int,
	PCRE_CONFIG_STACKRECURSE: bool,
	PCRE_CONFIG_UNICODE_PROPERTIES: bool,
	PCRE_CONFIG_MATCH_LIMIT_RECURSION: int,
	PCRE_CONFIG_BSR: int,
	PCRE_CONFIG_JIT: bool,
	PCRE_CONFIG_UTF16: bool,
	PCRE_CONFIG_JITTARGET: str,
	PCRE_CONFIG_UTF32: bool,
	PCRE_CONFIG_PARENS_LIMIT: int,
}

# pylint: disable=R0903
class VoidPointer(ctypes.c_void_p):
	"""
	Dummy subclass of ctypes.c_void_p used to ensure ctypes returns pointers intact and untouched.
	"""

class PCREErrorBadOption(Exception):
	"""
	Represent a "bad option" error (PCRE_ERROR_BADOPTION)
	"""
	def __init__(self, what):
		super().__init__(f'pcre_config(): bad option {what}')

class PCRECompileException(Exception):
	"""
	Represent a compile error.
	Useful attributes:
	- pattern: pattern the compilation of which failed
	- error: error message returned by libpcre
	- offset: offset at which the error was supposedly detected
	All three attributes are reflected by this exception's main message.
	"""
	def __init__(self, pattern, error, offset):
		self.pattern = pattern
		self.error = error
		self.offset = offset
		message = 'Error when compiling pattern %s: %s at offset %d'
		message = message % (pattern, error, offset)
		super().__init__(message)

def nametable_entry(entry):
	"""
	Unpack a name table entry into an index+name tuple.
	"""
	index = unpack('>H', entry[0:2])[0]
	name_bytes = bytes(ctypes.c_char_p(entry[2:]).value)
	# "Names consist of up to 32 alphanumeric characters and underscores." -- pcrepattern(3)
	# Anything else yields "syntax error in subpattern name (missing terminator)".
	name = name_bytes.decode('ascii')
	return (index, name)

class PCRELibrary:
	"""
	Offer a thin abstraction layer on top of the most popular libpcre functions.
	"""
	def __init__(self, soname=None, encode='utf-8', decode='utf-8', ovector_size=60):
		"""
		soname: filename of the libpcre shared object, or None for autodetection.
		encode: encoding used to turn patterns and subjects into bytes before passing them to libpcre functions.
		decode: encoding used to turn capture values into regular Python strings.
		ovector_size: refer to libpcre documentation
		lazy: False to load the pcre library in this constructor, False to wait until it is actually required.
		"""
		self.shared_object_name = soname
		self.encode = encode
		self.decode = decode
		self.ovector_size = ovector_size
		self.libpcre = None

	def get_lib(self):
		"""
		Simple wrapper around ctypes.CDLL to load libpcre.so (specifically shared_object_name).
		"""
		if self.libpcre is None:
			if self.shared_object_name is None:
				self.shared_object_name = find_library('pcre')
				if self.shared_object_name is None:
					self.shared_object_name = 'libpcre.so.1'
			self.libpcre = ctypes.CDLL(self.shared_object_name)
		return self.libpcre

	def version(self):
		"""
		Wrapper around pcre_version().
		"""
		lib = self.get_lib()
		lib.pcre_version.restype = ctypes.c_char_p
		return lib.pcre_version().decode('ascii')

	def config_generic(self, what, where_type):
		"""
		Direct wrapper around pcre_config().
		what should be an integer, typically a PCRE_CONFIG_* value.
		where_type should be a ctypes type, typically c_int or c_char_p.
		"""
		lib = self.get_lib()
		where = where_type()
		result = lib.pcre_config(ctypes.c_int(what), ctypes.byref(where))
		if result < 0:
			raise PCREErrorBadOption(what)
		return where.value

	def config_string(self, what):
		"""
		Helper to use config_generic assuming the output type is an ASCII zero-terminated string.
		"""
		c_string = self.config_generic(what, ctypes.c_char_p)
		return bytes(c_string).decode('ascii')

	def config_int(self, what):
		"""
		Helper to use config_generic assuming the output type is an integer.
		"""
		return self.config_generic(what, ctypes.c_int)

	def config_bool(self, what):
		"""
		Helper to use config_generic assuming the output type is a boolean.
		"""
		return bool(self.config_int(what))

	def config(self, what):
		"""
		Human-friendly interface to pcre_config(): just pass a PCRE_CONFIG_* constant.
		If an unknown value is passed, its output type is assumed to be an integer.
		Like config_generic, this function may raise a PCREErrorBadOption exception.
		"""
		output_type = CONFIG_OUTPUT_TYPE.get(what, int)
		if output_type is bool:
			method = self.config_bool
		elif output_type is str:
			method = self.config_string
		else:
			method = self.config_int
		return method(what)

	def supports_caseless_utf8(self):
		"""
		Return whether the loaded PCRE library "is compiled with Unicode property support as well as with UTF-8
		support", thus enabling "caseless matching for characters 128 and above" (quotes from the pcreapi documention).
		"""
		return self.config(PCRE_CONFIG_UTF8) and self.config(PCRE_CONFIG_UNICODE_PROPERTIES)

	def compile(self, pattern, options=0):
		"""
		Wrapper around the pcre_compile() function.
		pattern should be a regular Python string.
		options should be a regular Python integer.

		Examples:
		this.compile('^(?i)hello')
		this.compile('hello', pcre.PCRE_ANCHORED|pcre.PCRE_CASELESS)

		Return a pointer to the successfully compiled regex or raise a PCRECompileException.
		"""
		lib = self.get_lib()
		err = ctypes.c_char_p()
		erroffset = ctypes.c_int()
		lib.pcre_compile.restype = VoidPointer
		pcre_code = lib.pcre_compile(
			ctypes.c_char_p(pattern.encode(self.encode)),
			options,
			ctypes.byref(err),
			ctypes.byref(erroffset),
			None
		)
		if not pcre_code:
			error = bytes(err.value).decode('ascii')
			raise PCRECompileException(pattern, error, erroffset.value)
		return pcre_code

	def free(self, pcre_code):
		"""
		Free memory allocated by libpcre.
		"""
		lib = self.get_lib()
		# Cannot use pcre_free since the ELF shared object declares pcre_free as a global varible (st_type: STT_OBJECT)
		# as opposed to a function (st_type: STT_FUNC); fortunately, pcre_free_substring exists exactly for this
		# purpose:
		lib.pcre_free_substring(pcre_code)

	def exec(self, pcre_code, subject, exec_options=0):
		"""
		Matches subject against the given pcre code.
		pcre_code should be a pointer returned by pcre_compile(). Passing a pattern string directly is not supported.
		subject should be a regular Python string.
		options should be a regular Python integer.

		Examples:
		pcre_exec(my_compiled_pattern, 'Hello World!', pcre.PCRE_NO_START_OPTIMIZE)
		"""
		lib = self.get_lib()
		subject_bytes = subject.encode(self.encode)
		ovector = (ctypes.c_int * self.ovector_size)()
		match_count = lib.pcre_exec(
			pcre_code,                      # code
			None,                           # extra
			ctypes.c_char_p(subject_bytes), # subject
			len(subject_bytes),             # length
			0,                              # startoffset
			ctypes.c_uint32(exec_options),  # options
			ovector,                        # ovector
			self.ovector_size               # ovecsize
		)
		if match_count < 1:
			return False
		return self.get_captures(pcre_code, subject_bytes, ovector, match_count)

	def info_namecount(self, pcre_code):
		"""
		Wrapper around pcre_fullinfo() to get PCRE_INFO_NAMECOUNT, i.e. the number of named subpatterns, which is also the
		number of entries in the name table.
		"""
		lib = self.get_lib()
		res_int = ctypes.c_int()
		lib.pcre_fullinfo(pcre_code, None, PCRE_INFO_NAMECOUNT, ctypes.byref(res_int))
		return res_int.value

	def info_nameentrysize(self, pcre_code):
		"""
		Wrapper around pcre_fullinfo() to get PCRE_INFO_NAMEENTRYSIZE, i.e. the size of name table entries.
		"""
		lib = self.get_lib()
		res_int = ctypes.c_int()
		lib.pcre_fullinfo(pcre_code, None, PCRE_INFO_NAMEENTRYSIZE, ctypes.byref(res_int))
		return res_int.value

	def info_nametable(self, pcre_code):
		"""
		Wrapper around pcre_fullinfo() to get PCRE_INFO_NAMETABLE, i.e. name table itself.
		Like pcre_fullinfo(), this function returns a "void *" pointer.
		See info_nametable_data().
		"""
		lib = self.get_lib()
		where = ctypes.c_void_p()
		lib.pcre_fullinfo(pcre_code, None, PCRE_INFO_NAMETABLE, ctypes.byref(where))
		return where

	def info_nametable_data(self, pcre_code):
		"""
		Wrapper around info_nametable() that casts the pointer into usable data.
		"""
		nametable_ptr = self.info_nametable(pcre_code)
		nametable_data = ctypes.cast(nametable_ptr, ctypes.POINTER(ctypes.c_char))
		return nametable_data

	def nametable(self, pcre_code):
		"""
		Return the name table as a list of index+name tuples.
		"""
		named_captures_count = self.info_namecount(pcre_code)
		entrysize = self.info_nameentrysize(pcre_code)
		data = self.info_nametable_data(pcre_code)
		names = []
		for i in range(0, named_captures_count):
			entry = data[entrysize * i:entrysize * i + entrysize]
			names.append(nametable_entry(entry))
		return names

	def ordered_nametable(self, pcre_code):
		"""
		Return the name table as a list of names.
		Note: index 0 is always None.
		"""
		nametable = self.nametable(pcre_code)
		ordered_nametable = [None for i in range(len(nametable)+1)]
		for index, name in nametable:
			ordered_nametable[index] = name
		return ordered_nametable

	def get_capture(self, ovector, subject_bytes, index):
		"""
		Extract a numbered capture from the subject string.
		"""
		start = ovector[index*2]
		end   = ovector[index*2+1]
		capture = subject_bytes[start:end].decode(self.decode)
		return capture

	def get_captures(self, pcre_code, subject_bytes, ovector, match_count):
		"""
		Extract both numbered and named captures and return them through a dict with keys 'by_index' and 'by_name'.
		'by_index' points to an array of strings wheread 'by_name' points to a dict keyed by capture names.
		"""
		# Numbered captures:
		matches = [self.get_capture(ovector, subject_bytes, i) for i in range(0, match_count)]
		# Named captures:
		name_matches = {}
		for index, name in self.nametable(pcre_code):
			try:
				name_matches[name] = matches[index]
			except IndexError:
				# Depending on which alternative matched, names may point to non-existent indices.
				# In this case, keep the name and set its value to None/null:
				name_matches[name] = None
		return { 'by_index': matches, 'by_name': name_matches }

	def match(self, pattern, subject, compile_options=0, exec_options=0):
		"""
		Compile pattern using compile_options, then match subject against it using exec_options.
		May raise a PCREException as described in compile().
		Return the same thing as exec().
		"""
		code = self.compile(pattern, compile_options)
		res = self.exec(code, subject, exec_options)
		self.free(code)
		return res
