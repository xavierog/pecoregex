"""
Provide a Command-Line Interface (CLI) able to compile and execute multiple patterns.
These patterns and their associated subjects can be read from either a YAML/JSON document passed on stdin or from
command-line arguments.
"""
from .cli import run_cli
if __name__ == '__main__':
	run_cli()
