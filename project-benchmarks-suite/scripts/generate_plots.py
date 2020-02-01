#!/usr/bin/env python3
'''This script is assumed to run from the project root'''
import subprocess as sp
import os.path as op
import os
import sys
import json
from pathlib import Path
from util import *

os.chdir(op.join(os.environ['MESON_SOURCE_ROOT'], '..'))

GNUPLOT = sys.argv[1]
PLOTS_DIR = op.join(BUILD_DIR_BASE, 'plots')
NATIVE_FILES = ('native-files/msvc2019.txt', 'native-files/msvc2019-2.txt')
config_names = [op.splitext(op.basename(native_file_name))[0] for native_file_name in NATIVE_FILES]


def generate_plot(benchmark_name, **kwargs):
    os.makedirs(PLOTS_DIR, exist_ok=True)
    benchmark_title = benchmark_name.replace('-', ' ').replace('_', ' ').capitalize()
    filename = op.join(BUILD_DIR_BASE, 'bench-results', benchmark_name) + '.txt'
    png_file = op.join(PLOTS_DIR, benchmark_name) + '.png'
    bench_plotter = op.join(MESON_SOURCE_ROOT, 'scripts', 'bench_plotter.plt')
    command = [f'{GNUPLOT}', '-e', f"filename='{filename}';output_plot='{png_file}';benchmark_title='{benchmark_title}'", bench_plotter]
    result = run_command(command, **kwargs)
    

if not checkpoint_exists('.plots_generated'):
    for benchmark_name in get_benchmarks_names(op.join(BUILD_DIR_BASE, config_names[0])):
        generate_plot(benchmark_name) 
    save_checkpoint('.plots_generated')
print('Done generating plots for benchmark suite')