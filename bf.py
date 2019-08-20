

from typing import *
from typing import IO
from io import IOBase, BytesIO, StringIO
from sys import stdin, stdout
from enum import IntEnum, unique
from types import SimpleNamespace
from collections import deque
from itertools import repeat



class BrainfuckParser:
	'''
	This class validates and parse brainfuck code (checking properly for syntax errors).

	e.g:
	parse = BrainfuckParser()
	parse(b'++[ >++.<- ] is a basic loop') # Returns b'++[>++.<-]'  (invalid chars are discarded)
	parse(b'++[+]]-') -> Raises SyntaxError


	It also allows interactive parsing (calling it multiple times)
	e.g:
	parse(b'+++++[.-') # Returns None because the sequence is incomplete
	parse(b'-]+.') # Returns all the parsed code (b'+++++[.--]+.') as the sequence is completed.
	'''
	def __init__(self):
		'''
		Initialize the parser.
		'''
		self.level = 0
		self.buffer = None


	def __call__(self, *args, **kwargs):
		# Its an alias of parse() method. It allows to use the parser as a callable object.
		return self.parse(*args, **kwargs)


	def parse(self, code: AnyStr) -> Union[bytes, None]:
		'''
		Parses the given brainfuck code:
		First, all invalid symbols (different than +-><.,[]) are discarded.
		Then:
			* If it contains syntax errors, raises SyntaxError.
			This happens if  ']' symbol appears before any '[' symbol.
			Also occurs when the number of occurrences of ']' is greater than for '[' symbol.

			* if the code is valid but incomplete (which happens when the number
			of '[' symbols is greater than the amount of ']'), then its stored in a internal
			buffer and the returned value is None.
			
			For any subsequent call to parse() method, the contents of the buffer will be appended
			at the beginning of the new code (this allows interactive parsing).

			* if the code is valid and complete, returns the code itself with all the invalid symbols
			removed as a bytes object.
		'''

		if not isinstance(code, (str, bytes)):
			raise TypeError('Code must be a string or bytes obect')

		if isinstance(code, str):
			code = code.encode()


		tokens = iter(code)
		c, self.level = self.level, 0
		buffer, self.buffer = self.buffer if self.buffer is not None else deque(), None

		try:
			while True:
				# Read each token
				token = next(tokens)

				# Ignore invalid tokens
				if token not in (43, 45, 62, 60, 91, 93, 44, 46):
					continue

				# Check syntax errors & update state
				if token == 93:
					if not buffer:
						raise SyntaxError
					prev = buffer[-1]
					if c == 0 or prev == 91:
						raise SyntaxError
					c -= 1
				else:
					if token == 91:
						c += 1

				# Add token
				buffer.append(token)

		except StopIteration:
			# Is the code valid but incomplete?
			if c > 0:
				self.level, self.buffer = c, buffer
				return None

		# Code valid & complete
		return bytes(buffer)




class BrainfuckInterpreter:
	'''
	Brainfuck code interpreter.
	e.g:
	bf = BrainfuckInterpreter()
	bf.exec('++[.-]') # 210
	
	The memory state and the cursor position is saved accross different executions
	using the same interpreter:

	bf.exec('+++')       # Memory: 3 0 0 ... Cursor: 0
	bf.exec('[>.++<-]>') # Memory: 0 6 0 ... Cursor: 1 
	bf.exec('.<')		 # Memory: 0 6 0 ... Cursor: 0

	The constructor parameters allows to specify alternative input/output streams rather than
	stdin/stdout, set the memory size among other things:

	buf = StringIO('123')
	bf = BrainfuckInterpreter(input=buf, mem_size=2)
	bf.exec('+++[>,++.<-]') # 345
	
	
	Finally, exec() method returns execution metrics:
	metrics = bf.exec('++[>+<-]')
	print(metrics.value_ops_count)   # 6
	print(metrics.pointer_ops_count) # 4
	'''
	def __init__(self,
		input: Optional[Union[IO, AnyStr]]=None, output: Optional[IO]=None,
		mem_size: Optional[int]=None, wrap_values: Optional[bool]=None, max_ops: Optional[int]=None):

		if input is not None:
			if not isinstance(input, (IOBase, str, bytes)):
				raise TypeError('Input stream must be an IO, string or bytes object')
			if isinstance(input, IOBase):
				if not input.readable():
					raise TypeError('Input stream must be a readable IO object')
			elif isinstance(input, str):
				input = StringIO(input)
			else:
				input = BytesIO(input)
		else:
			input = stdin

		if output is not None:
			if not isinstance(output, IOBase) or not output.writable():
				raise TypeError('Output stream must be a writable IO object')
		else:
			output = stdout

		if mem_size is not None:
			if not isinstance(mem_size, int):
				raise TypeError('Memory size must be a number')
			if mem_size < 1:
				raise ValueError('Memory size must be a number greater than zero')
		else:
			mem_size = 30000

		if wrap_values is not None:
			if not isinstance(wrap_values, bool):
				raise TypeError('Wrap value argument must be boolean')
		else:
			wrap_values = False

		if max_ops is not None:
			if not isinstance(max_ops, int):
				raise TypeError('Max instruction must be a number')
			if max_ops < 1:
				raise ValueError('Max instructions must be a number greater than zero')
		else:
			max_ops = 1000000


		self.input, self.output = input, output
		self.wrap_values, self.max_ops = wrap_values, max_ops
		self.mem, self.pointer = bytearray(mem_size), 0



	def __call__(self, *args, **kwargs):
		# Alias of method exec(). This allows the interpreter to be used as a callable object.
		return self.exec(*args, **kwargs)


	def exec(self, code: AnyStr) -> SimpleNamespace:
		'''
		Executes the given brainfuck code with this interpreter.
		The code must be valid and complete (otherwise it raises SyntaxError or EOFError)
		
		While the code is running:
		- Trying to move the pointer with > and < instructions outside the bounds of the memory tape,
		causes an IndexError

		- If wrap_values parameter  is set to False, attempting to decrement a byte with the value 0x00 or
		increment 0xFF, causes an OverflowError.

		- If the number of instructions executed reaches the limit allowed (max_ops parameter), raises
		RuntimeError
		
		Any exception raised while executing the code will halt the interpreter and save the current
		memory and pointer state (for future calls to exec)

		The returned value will be an object (SimpleNamespace) with execution metrics (number of
		io instructions, number of value change operations, ...)
		'''

		# Parse code and check for syntax errors
		code = BrainfuckParser().parse(code)
		if code is None:
			# Code is not complete
			raise EOFError

		input, output = self.input, self.output
		wrap_values, max_ops = self.wrap_values, self.max_ops
		mem, pointer = self.mem, self.pointer


		try:
			# Initialize metrics
			value_ops_count, pointer_ops_count, io_ops_count, jump_ops_count, ops_count = repeat(0, times=5)

			# Execute the code
			k, goto, n = 0, deque(), len(code)
			while k < n:
				instr = code[k]

				# Update metrics
				if instr in (43, 45):
					value_ops_count += 1
				elif instr in (60, 62):
					pointer_ops_count += 1
				elif instr in (44, 46):
					io_ops_count += 1
				elif instr in (91, 93):
					jump_ops_count += 1
				ops_count += 1

				# Reached max instructions limit?
				if ops_count > max_ops:
					raise RuntimeError


				if instr == 43: # increment value
					if mem[pointer] == 0xFF and not wrap_values:
						raise OverflowError
					mem[pointer] = (mem[pointer]+1)%256

				elif instr == 45: # decrement value
					if mem[pointer] == 0x00 and not wrap_values:
						raise OverflowError
					mem[pointer] = (mem[pointer]+255)%256


				elif instr == 62: # increment pointer
					if pointer == len(mem)-1:
						raise IndexError
					pointer += 1

				elif instr == 60: # decrement pointer
					if pointer == 0:
						raise IndexError
					pointer -= 1

				elif instr == 46: # write to stdout
					output.write(chr(mem[pointer]))
					output.flush()

				elif instr == 44: # read to stdout
					mem[pointer] = ord(input.read(1))%256

				elif instr == 91: # begin while
					if mem[pointer]:
						goto.append(k)
					else:
						c = 0
						k += 2
						instr = code[k]
						while instr != 93 or c > 0:
							if instr == 91:
								c += 1
							elif instr == 93:
								c -= 1
							k += 1
							instr = code[k]


				elif instr == 93: # end while
					if mem[pointer]:
						k = goto[-1]
					else:
						goto.pop()

				# Go to the next instruction
				k += 1


			# Return execution metrics
			metrics = SimpleNamespace(
				value_ops_count=value_ops_count,
				pointer_ops_count=pointer_ops_count,
				io_ops_count=io_ops_count,
				jump_ops_count=jump_ops_count,
				ops_count=ops_count
			)
			return metrics

		finally:
			self.pointer = pointer





def bf_parse(code: AnyStr) -> Union[bytes, None]:
	'''
	First, all invalid symbols (different than +-><.,[]) are discarded.
	Then:
		* If it contains syntax errors, raises SyntaxError.
		This happens if  ']' symbol appears before any '[' symbol.
		Also occurs when the number of occurrences of ']' is greater than for '[' symbol.

		* if the code is valid but incomplete (which happens when the number
		of '[' symbols is greater than the amount of ']'), returns None.
		
		* if the code is valid and complete, returns the code itself with all the invalid symbols
		removed as a bytes object.

	Its a shorthand for BrainfuckParser().parse(code)

	Note: For interactive parsing, you should use BrainfuckParser class directly (read its docs)
	'''
	return BrainfuckParser().parse(code)



def bf_exec(
	code: AnyStr,
	input: Optional[IO]=None, output: Optional[IO]=None,
	mem_size: Optional[int]=None, wrap_values: Optional[bool]=None,
	max_ops: Optional[int]=None) -> SimpleNamespace:
	'''
	Executes the given brainfuck code.
	The code must be valid and complete (otherwise it raises SyntaxError or EOFError)
	
	While the code is running:
	- Trying to move the pointer with > and < instructions outside the bounds of the memory tape,
	causes an IndexError

	- If wrap_values parameter  is set to False, attempting to decrement a byte with the value 0x00 or
	increment 0xFF, causes an OverflowError.

	- If the number of instructions executed reaches the limit allowed (max_ops parameter), raises
	RuntimeError
	
	Its a shorthand for BrainfuckInterpreter(input, output, mem_size, wrap_values, max_ops).exec(code).
	'''
	return BrainfuckInterpreter(input, output, mem_size, wrap_values, max_ops).exec(code)





