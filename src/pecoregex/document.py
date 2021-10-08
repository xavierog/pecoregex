"""
Define the various keys expected in a pecoregex document.
"""
# pecoregex documents provide the ability to declare reusable strings and sets of PCRE options in "reference"
# structures:
REFERENCE_COMPILE_OPTIONS = 'compile_options'
REFERENCE_EXECUTE_OPTIONS = 'execute_options'
REFERENCE_PATTERN_STRINGS = 'pattern_strings'
REFERENCE_SUBJECT_STRINGS = 'subject_strings'

# pecoregex documents are all about compiling patterns:
PATTERNS = 'patterns'
PATTERN_VALUE = 'value'
COMPILE_OPTIONS = 'options'

# ... and match subject strings against them:
EXECUTE = 'execute'
SUBJECT = 'subject'
EXECUTE_OPTIONS = 'options'

# This produces compilation-related attributes:
COMPILE = 'compile'
ERROR = 'error'
ERROR_MESSAGE = 'message'
ERROR_OFFSET = 'offset'

# ... and execution-related attributes:
MATCH = 'match'
CAPTURES = 'captures'
