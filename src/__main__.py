
'''
This script runs an interactive console to execute brainfuck code.
'''

from src import BrainfuckParser, BrainfuckInterpreter, bf_parse, bf_exec
from argparse import ArgumentParser, FileType
from sys import stdin, stdout


DESCRIPTION=\
'''
Brainfuck language interpreter.
'''


if __name__ == '__main__':
	# Parser CLI args
	parser = ArgumentParser(description=DESCRIPTION)
	parser.add_argument('source', type=open, help='File containing the brainfuck code to execute')
	parser.add_argument('--input', '-i', type=open, help='Input file where read operations should be performed. By default is the standard input.')
	parser.add_argument('--output', '-o', type=FileType('w'), default=stdout, help='Output file to store the results. By default is the standard output.')
	parser.add_argument('--memsize', '-m', type=int, default=30000, help='Size of the memory tape of the interpreter in bytes. By default is 30000')
	parser.add_argument('--maxops', type=int, default=100000, help='Maximum number of operations allowed. This is used to prevent infinite loops. By default is 1000000')
	parser.add_argument('--wrap', '-w', action='store_true', help='If enabled, decrementing the byte 0x00 will turn it into 0xFF, and 0xFF into 0x00 if incremented')
	parser.add_argument('--debug', '-d', action='store_true', help='Print execution metrics and debug information')
	args = parser.parse_args()
	
	# Get source code
	code = args.source
	input, output = args.input, args.output
	mem_size, max_ops, wrap_values = args.memsize, args.maxops, args.wrap
	debug = args.debug
	
	try:
		try:
			# Execute the code
			interpreter = BrainfuckInterpreter(input, output, mem_size, wrap_values, max_ops)
			metrics = interpreter.exec(code)

			# Print execution metrics
			if debug:
				print()
				print(">" * 40)
				print("Number of instructions executed: {:8d}".format(metrics.ops_count))
				print("- i/o (, and .):{:25d}".format(metrics.io_ops_count))
				print("- byte modifications (+ and -):{:10d}".format(metrics.value_ops_count))
				print("- pointer moves (< and >):{:15d}".format(metrics.pointer_ops_count))
				print("- jumps ([ and ]):{:23d}".format(metrics.jump_ops_count))
				print("<" * 40)
				print()

		except (RuntimeError, OverflowError, IndexError) as e:
			# Interpreter failed
			print()
			print(f"Interpreter halted ({e})")
			print()

		# Print memory & pointer state at the end of the execution (even if it fails)
		if debug:
			nz_bytes_count = sum(map(bool, interpreter.mem))
			print()
			print(">" * 40)
			print("Memory & pointer state (at the end):")
			print("- Non-zero bytes: {} {}".format(
				f"{nz_bytes_count}/{mem_size}".rjust(23),
				f"(~{round(nz_bytes_count*100/mem_size, 2)}%)"
				))

			if nz_bytes_count > 0:
				last_nz_byte_index = next(filter(None, reversed(interpreter.mem)))
				print("- Last non-zero byte:{:20d}".format(last_nz_byte_index))
			print("- Pointer position:{:22d}".format(interpreter.pointer))
			print("<" * 40)
			print()


	except (TypeError, ValueError) as e:
		parser.error(e)

