

from typing import *
from typing import IO
from io import IOBase
from sys import stdin, stdout
from enum import IntEnum, unique
from types import SimpleNamespace
from collections import deque
from itertools import repeat




def bf_parse(code: AnyStr) -> bytes:
	'''
	Validate and parse the given brainfuck code.
	:param code: Must be brainfuck code to parse; A string or bytes object.
	
	
	Returns a byte array object where each byte is a valid brainfuck instruction. Will be one of this:
	b',', b'.', b'<', '>', b'+', b'-', b'[', b']'
	Raises SyntaxError if the code is not valid.
	Returns None if the code is valid but its incomplete.
	'''
	if not isinstance(code, (str, bytes)):
		raise TypeError('Code must be a string or bytes obect')

	if isinstance(code, str):
		code = code.encode()

	instrs, c, tokens = deque(), 0, iter(code)
	

	try:
		while True:
			# Read each token
			token = next(tokens)

			# Ignore invalid tokens
			if token not in (43, 45, 62, 60, 91, 93, 44, 46):
				continue

			# Check syntax errors & update state
			if token == 93:
				if not instrs:
					raise SyntaxError
				prev = instrs[-1]
				if c == 0 or prev == 91:
					raise SyntaxError
				c -= 1
			else:
				if token == 91:
					c += 1

			# Add token
			instrs.append(token)


	except StopIteration:
		# Is code incomplete?
		if c > 0:
			return None

	# Code valid & complete
	return bytes(instrs)





def bf_exec(
	code: AnyStr, input: Optional[IO]=None,
	output: Optional[IO]=None,
	mem: Optional[Union[int, bytearray]]=None,
	pointer: Optional[int]=None,
	wrap_values: Optional[bool]=None, max_instructions: Optional[int]=None) -> Tuple[bytearray, int, SimpleNamespace]:
	'''
	Execute the given brainfuck code.
	:param code: Code to be executed; A string or bytes object.
	Must be a valid and complete brainfuck code. If the code is not valid, raises SyntaxError.
	If the code is valid but not complete, raises EOFError

	:param input: Input stream for the brainfuck interpreter that must be a readable IO object. By default is sys.stdin
	:param output: Output stream, a writable IO object. By default is sys.stdout

	:param mem: Must be either a bytearray object to be used as memory for the interpreter or a positive number indicating
	the memory size you want to use (in that case, a new bytearray with that length initialized with zeros is created and used)
	By default, its 30000
	If the pointer is moved during the execution outside of the memory limits, IndexError exception is raised.
	
	:param pointer: Is the position where the pointer should be located at the beginning of the execution in memory.
	It must be an integer between 0 and len(mem)-1 (By default 0)

	:param wrap_values: If True, the byte 0XFF is converted to 0x00 when its incremented and viceversa when its decremented.
	By default is False. If 0x00 is decremented or 0xFF incremented when this is set to False, raises OverflowError exception.

	:param max_instructions: Maximum amount of instructions allowed for the interpreter. Reaching this limit will raise
	RuntimeError exception. By default is 1000000 (1m).


	If code was run succesfully, the returned value is a tuple with three items.
	The first & second items will be the state of the memory and the pointer position after the code execution (bytearray and int objects).
	The last will be a simple namespace with metrics:
		* value_ops_count:   Number of byte increments/decrements operations
		* pointer_ops_count: Number of pointer increments/decrements operations
		* io_ops_count:		 Number of input/output operations
		* jump_ops_count:    Number of "jump" operations (using [ and ] instructions)
		* ops_count:		 Total operations performed

	'''

	if input is not None:
		if not isinstance(input, IOBase) or not input.readable():
			raise TypeError('Input stream must be a readable IO object')
	else:
		input = stdin

	if output is not None:
		if not isinstance(output, IOBase) or not output.writable():
			raise TypeError('Output stream must be a writable IO object')
	else:
		output = stdout


	if mem is not None:
		if not isinstance(mem, (int, bytearray)):
			raise TypeError('Memory must be a number or a bytearray object')
		if isinstance(mem, int):
			if mem < 1:
				raise ValueError('Memory size must be a number greater than zero')
		elif not mem:
			raise ValueError('Memory must be a non empty bytearray object')
	else:
		mem = 30000

	if pointer is not None:
		if not isinstance(pointer, int):
			raise TypeError('Pointer position must be a number')
		if pointer not in range(0, mem if isinstance(mem, int) else len(mem)):
			raise ValueError('Pointer position out of bounds')
	else:
		pointer = 0

	if wrap_values is not None:
		if not isinstance(wrap_values, bool):
			raise TypeError('Wrap value argument must be boolean')
	else:
		wrap_values = False

	if max_instructions is not None:
		if not isinstance(max_instructions, int):
			raise TypeError('Max instruction must be a number')
		if max_instructions < 1:
			raise ValueError('Max instructions must be a number greater than zero')
	else:
		max_instructions = 1000000


	# Parse code and check for syntax errors
	code = bf_parse(code)
	if code is None:
		# Code is not complete
		raise EOFError

	# Initialize memory tape with zeros
	if isinstance(mem, int):
		mem = bytearray(mem)

	# Initialize metrics
	value_ops_count, pointer_ops_count, io_ops_count, jump_ops_count, ops_count = repeat(0, times=5)


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
		if ops_count > max_instructions:
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




	metrics = SimpleNamespace(
		value_ops_count=value_ops_count,
		pointer_ops_count=pointer_ops_count,
		io_ops_count=io_ops_count,
		jump_ops_count=jump_ops_count,
		ops_count=ops_count
	)
	return mem, pointer, metrics

