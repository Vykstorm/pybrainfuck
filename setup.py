
'''
Installation script for this library
'''

from setuptools import setup


if __name__ == '__main__':
    setup(
        name='pybrainfuck',
        version='1.0.0',
        description='Brainfuck code interpreter implemented in python',
        author='Vykstorm',
        author_email='victorruizgomezdev@gmail.com',
        keywords=['brainfuck', 'brainfuck-interpreter', 'esoteric', 'esoteric-language'],
        url='https://github.com/Vykstorm/pybrainfuck',

        python_requires='>=3.5',
        install_requires=[],
        dependency_links=[],

        package_dir={'bf': 'src'},
        packages=['bf']
    )