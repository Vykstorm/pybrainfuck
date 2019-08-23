
import unittest
from unittest import TestCase
from src import *
from re import match
from os import listdir
from os.path import join
from io import BytesIO, StringIO
from collections import deque


samples = {}
for filename in listdir('examples'):
	name = match(r'(.+)\..+$', filename).group(1)
	with open(join('examples', filename), 'r') as file:
		samples[name] = file.read()



class TestExamples(TestCase):
	'''
	This provides a set of tests which executes brainfuck code examples and verifies
	that the result written on the output stream is the expected.
	The examples are stored in the "examples/" directory

	They are extracted from:
	https://github.com/kavehmz/brainfuck_examples
	http://www.hevanet.com/cristofd/brainfuck/
	'''
	def test_numbers100(self):
		buf = StringIO()
		bf_exec(samples['numbers100'], output=buf, mem_size=100, max_ops=10000)
		nums = list(map(int, buf.getvalue().split('\n')[:-1]))
		self.assertEqual(nums, list(range(0, 100)))


	def test_fib(self):
		buf = StringIO()
		try:
			bf_exec(samples['fib'], output=buf, mem_size=100, max_ops=10000)
		except RuntimeError:
			pass
		nums = deque(map(int, buf.getvalue().split('\n')[:-1]))
		self.assertEqual(nums.popleft(), 0)
		a, b = 0, 1
		while len(nums) > 0:
			self.assertEqual(nums.popleft(), b)
			a, b = b, a+b


	def test_squares(self):
		buf = StringIO()
		try:
			bf_exec(samples['squares'], output=buf, mem_size=20, max_ops=100000)
		except RuntimeError:
			pass
		nums = list(map(int, buf.getvalue().split('\n')[:-1]))
		self.assertEqual([x ** 2 for x in range(26)], nums)


	def test_factorial(self):
		buf = StringIO()
		try:
			bf_exec(samples['factorial'], output=buf, mem_size=1000, max_ops=100000)
		except RuntimeError:
			pass
		nums = deque(map(int, buf.getvalue().split('\n')[:-1]))
		nums.popleft()
		a, b = 1, 1
		while len(nums) > 0:
			self.assertEqual(nums.popleft(), b)
			a += 1
			b *= a


if __name__ == '__main__':
	unittest.main()