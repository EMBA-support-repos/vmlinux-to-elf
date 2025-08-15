#!/usr/bin/env python3
#-*- encoding: Utf-8 -*-
from os.path import dirname, realpath
from argparse import ArgumentParser
from sys import stdout
import logging
import sys

SCRIPT_DIR = dirname(realpath(__file__))
PACKAGE_DIR = dirname(SCRIPT_DIR)
PARENT_DIR = dirname(PACKAGE_DIR)
sys.path.insert(0, PARENT_DIR)

from vmlinux_to_elf.core.vmlinuz_decompressor import obtain_raw_kernel_from_file
from vmlinux_to_elf.core.architecture_detecter import ArchitectureGuessError
from vmlinux_to_elf.core.kallsyms import KallsymsFinder

if __name__ == '__main__':

    logging.basicConfig(stream=stdout, level=logging.INFO, format='%(message)s')

    args = ArgumentParser(description = "Find the kernel's embedded symbol table from a raw " +
        "or stripped ELF kernel file, and print these to the standard output with their " +
        "addresses or optionally save them to a file")
    
    args.add_argument('input_file', help = "Path to the kernel file to extract symbols from")
    args.add_argument('--output', help= "Path to the analyzable .kallsyms output")
    args.add_argument('--use-absolute', help = 'Assume kallsyms offsets are absolute addresses' , action="store_true")
    args.add_argument('--bit-size', help = 'Force overriding the input kernel ' +
        'bit size, providing 32 or 64 bit (rather than auto-detect)', type = int)
    args.add_argument('--base-address', help = 'Force overriding the base address used for converting ' +
        'relocations to relative relocations with this integer value (rather than auto-detect)',
        type = lambda string: int(string.replace('0x', ''), 16), metavar = 'HEX_NUMBER')
    
    args = args.parse_args()


    with open(args.input_file, 'rb') as kernel_bin:
        
        try:
            kallsyms = KallsymsFinder(obtain_raw_kernel_from_file(kernel_bin.read()), args.bit_size, args.use_absolute, args.base_address)
        
        except ArchitectureGuessError:
           exit('[!] The architecture of your kernel could not be guessed ' +
                'successfully. Please specify the --bit-size argument manually ' +
                '(use --help for its precise specification).')
        
        kallsyms.print_symbols_debug()
        
        if args.output:
            output_file = args.output if args.output.endswith(".kallsyms") else args.output + ".kallsyms"
            with open(output_file, 'w') as f:
                for symbol_address, symbol_name in zip(kallsyms.kernel_addresses, kallsyms.symbol_names):
                    address_str = (
                        f"{symbol_address:016x}" if kallsyms.is_64_bits else f"{symbol_address:08x}")
                    line = f"{address_str} {symbol_name[0]} {symbol_name[1:]}\n"
                    f.write(line)
        
