
import unittest
from unittest import TestCase
from bf import *
from re import match
from os import listdir
from io import BytesIO, StringIO


samples = {}
for filename in listdir('examples'):
	name = match(r'(.+)\..+$', filename).group(1)
	with open(f'examples/{filename}', 'r') as file:
		samples[name] = file.read()



class TestExamples(TestCase):
	'''
	This provides a set of tests that executes brainfuck code examples and verifies
	that the result written on the output stream is the expected.
	The examples are stored in the "examples/" directory

	They are extracted from:
	https://github.com/kavehmz/brainfuck_examples
	
	'''
	def test_print0to99(self):
		buf = StringIO()
		bf_exec(samples['print0to99'], output=buf, mem_size=2**10, max_ops=2**13)
		nums = list(map(int, buf.getvalue().split('\n')[:-1]))
		self.assertEqual(nums, list(range(0, 100)))




if __name__ == '__main__':
	unittest.main()