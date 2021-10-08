"""
As pecoregex ultimately delegates the real work to the PCRE C library, it remains liable to crash your precious Python
program. This module provides helpers that delegate the processing of a pecoregex document to an external process.
"""
import json
import subprocess

def cli(doc, cmdline=None, **subprocess_args):
	"""
	Given a pecoregex document, pipe it to "pecoregex -in - --no-norm -out json" and return the resulting document.
	The command line can be entirely changed and extra arguments (e.g. timeout) are passed to subprocess.run().
	This function may raise the following exceptions:
	- subprocess.CalledProcessError (if pecoregex yields a non-zero exit code)
	- subprocess.TimeoutExpired (if timeout was set and pecoregex spent too much time processing the document)
	"""
	if cmdline is None:
		cmdline = ['pecoregex', '-in', '-', '--no-norm', '-out', 'json']
	pecoregex_process = subprocess.run(
		cmdline,
		input=json.dumps(doc),
		encoding='utf-8',
		stdout=subprocess.PIPE,
		shell=False,
		check=True,
		**subprocess_args
	)
	return json.loads(pecoregex_process.stdout)

def simplecli(doc, cmdline=None, **subprocess_args):
	"""
	Same as cli but return False (failure) or None (timeout) instead of raising exceptions.
	"""
	try:
		return cli(doc, cmdline, **subprocess_args)
	except subprocess.CalledProcessError:
		return False
	except subprocess.TimeoutExpired:
		return None
