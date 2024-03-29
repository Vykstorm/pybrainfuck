
import unittest
from unittest import TestCase
from src import *




class TestParser(TestCase):
	# Test case for function for brainfuck parser

	def test_parse_operations(self):
		# Symbols ',.+-><' are left as-is.
		self.assertEqual(bf_parse(b',.+-><'), b',.+-><')

		# Parsing an empty sequence of symbols returns a an empty byte sequence
		self.assertEqual(len(bf_parse(b'')), 0)

		# Any symbol different than ,.+-><[] is discarded
		for i in range(0, 256):
			if i not in b',.+-><[]':
				expr = bytes([i])
				self.assertEqual(len(bf_parse(expr)), 0)



	
	def test_parse_while(self):
		# Symbol ']' must appear after '[', otherwise it raises SyntaxError
		for expr in (b']', b'++>--.]', b'],--++'):
			self.assertRaises(SyntaxError, bf_parse, expr)

		# Symbol right before '[' cannot be '[' (raises SyntaxError)
		for expr in (b'[]', b'+-+-[]', b'[]+>-<+.', b'+-[]+-'):
			self.assertRaises(SyntaxError, bf_parse, expr)

		# If multiple occurrences of ']' happens such that no '[' appears between them,
		# there must be at least the same number of '[' before the first occurrence of ']'
		for expr in (b'[+]]', b'[-]]+-', b'><[-]]+-', b'>+[+-+]-]<'):
			self.assertRaises(SyntaxError, bf_parse, expr)

		# If there is no ']' after '[', bf_parse returns None (sequence is incomplete)
		for expr in (b'[', b'+-><[', b'+-[><'):
			self.assertEqual(bf_parse(expr), None)

		# If there are few '[', there must be also the same amount of ']' after them.
		# Otherwise, the sequence is also incomplete.
		for expr in (b'[[+]', b'+-[[-]', b',-[>+[<-]+-'):
			self.assertEqual(bf_parse(expr), None)



	def test_interactive_parsing(self):
		# BrainfuckParser class can be used to emulate interactive parsing
		parser = BrainfuckParser()
		self.assertEqual(parser.parse(b'++++['), None)
		self.assertEqual(parser.parse(b'.-]'), b'++++[.-]')

		self.assertEqual(parser.parse(b'++++['), None)
		self.assertEqual(parser.parse(b'.-'), None)
		self.assertEqual(parser.parse(b']'), b'++++[.-]')


		self.assertEqual(parser.parse(b'++[>+++[>++++<-]<'), None)
		self.assertEqual(parser.parse(b'-]'), b'++[>+++[>++++<-]<-]')


	def test_parse_str(self):
		# strings can be also parsed (they are encoded to bytes)
		for expr in ('++--', '++[-].', ',[.-]', '++[>++<-]'):
			self.assertEqual(bf_parse(expr), bf_parse(expr.encode()))


if __name__ == '__main__':
	unittest.main()