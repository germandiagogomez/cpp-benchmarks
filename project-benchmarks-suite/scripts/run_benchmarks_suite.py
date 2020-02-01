#!/usr/bin/env python3
'''This script is assumed to run from the project root'''
import subprocess as sp
import itertools as it
import os.path as op
import os
import sys
import collections as col
import json
from deepmerge import always_merger
from pathlib import Path
from util import *

os.chdir(op.join(os.environ['MESON_SOURCE_ROOT'], '..'))
NATIVE_FILES = ('native-files/msvc2019.txt', 'native-files/msvc2019-2.txt')
build_dirs = [op.join(f'{BUILD_DIR_BASE}', op.splitext(op.basename(native_file_name))[0]) for native_file_name in NATIVE_FILES]
config_names = [op.splitext(op.basename(native_file_name))[0] for native_file_name in NATIVE_FILES]
OUTPUT_DATA_DIR= op.join(BUILD_DIR_BASE, 'bench-results')


def configure_meson(native_file_name, build_dir, verbose, **kwargs):
    print(f'meson --native-file {native_file_name} ' +
            kwargs.get('meson_setup_options', '') + ' '
            f'{build_dir}')
    return run_command(['meson --native-file', f'{native_file_name}'] +
            kwargs.get('meson_setup_options', '').split(' ') + [f'{build_dir}'],
            message=f'Configuring build dir for {native_file_name}')


def run_benchmarks_for(build_dir, **kwargs):
    return run_command(['ninja', '-C', f'{build_dir}', 'benchmark'], 
                        f'Running benchmarks for {build_dir}',
                        **kwargs)


def rec_defaultdict():
    return col.defaultdict(rec_defaultdict)


def gather_bench_results_per_benchmark(build_dir, config_name, **kwargs):
    benchmark_file = op.join(build_dir, 'meson-logs/benchmarklog.json')
    def sort_by_benchmark(bench):
        return bench['name'].split('!')[2]
    benchmarks_dict = rec_defaultdict()
    with open(benchmark_file) as f:
        all_benchmarks = sorted((json.loads(obj) for obj in f), key=sort_by_benchmark)
        for k, g in it.groupby(all_benchmarks, sort_by_benchmark):
            for group_elem in g:
                style, bench_name = group_elem['name'].split('!')[1:3]
                benchmarks_dict[bench_name][config_name][style] = int(group_elem['stdout'].strip())    
    return benchmarks_dict


def print_bench_results(bench_results):
    for benchmark, config in bench_results.items():
        print(f'Benchmark: {benchmark}')
        for config, results in config.items():
            print(f'\tConfig: {config}. Results: {results}')


def write_output_data_file_for_plotting(bench_name, all_benchmarks, config_names=config_names, outdir=OUTPUT_DATA_DIR):
    os.makedirs(outdir, exist_ok=True)
    separator = '|'
    benchmark_name_results = all_benchmarks[bench_name]
    with open(op.join(outdir, bench_name + '.txt'), 'w') as out:
        out.write(separator.join([bench_name, 'Old style', 'Modern style']) + '\n')
        for config_name in config_names:           
            out.write(separator.join([config_name, str(benchmark_name_results[config_name]['old_style']),
                    str(benchmark_name_results[config_name]['modern_style'])]) + '\n')

if __name__ == '__main__':
    if not checkpoint_exists('.configured_done'):
        for i, native_file in enumerate(NATIVE_FILES):
            configure_meson(native_file, build_dirs[i], verbose=True, raise_error=False)
        save_checkpoint('.configured_done')
        print("Configuration done. Checkpoint saved")

    start_at = len(NATIVE_FILES)
    for i in range(len(NATIVE_FILES)):
        if not checkpoint_exists(f'.benchmarks_run_done_{config_names[i]}'):
            start_at = i
            break
    
    for i, native_file in enumerate(NATIVE_FILES[start_at:], start_at):
        run_benchmarks_for(build_dirs[i], verbose=True)    
        save_checkpoint(f'.benchmarks_run_done_{config_names[i]}')
        print(f'Done running benchmark suite for {config_names[i]}')
    
    if not checkpoint_exists('.plot_data_generated_done'):
        bench_results = rec_defaultdict()
        for i, build_dir in enumerate(build_dirs):
            bench_results = always_merger.merge(bench_results, gather_bench_results_per_benchmark(build_dir, config_names[i]))
        
        for bench_target in get_benchmarks_names(op.join(BUILD_DIR_BASE, config_names[0])):
            print(bench_target)
            write_output_data_file_for_plotting(bench_target, bench_results)
        save_checkpoint('.plot_data_generated_done')
        print("Data for plotting done. Checkpoint saved.")
    print('Finished running the benchmarks suite')