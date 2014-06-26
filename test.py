#!/bin/env python

import os
import argparse
import sys
import subprocess as sp
import shutil

import numpy as np

# Below: switch between Mahotas and scikit-image for IO.
# from skimage import io
import mahotas as io

from verify import open_write

# Some constants
test_data_dir = 'test-data'
test_output_dir = 'test-data-out'
test_results_dir = 'test-data-results'
test_output_mask_dir = 'test-data-out-m'
test_results_mask_dir = 'test-data-results-m'


def find_errors(out_dir, res_dir, ignore_masks=False):
    """Check that each output .tif file matches its reference output.

    Parameters
    ----------
    out_dir, res_dir : string
        The name of the root directories containing input, output,
        and expected results.
    ignore_masks : bool, optional
        Ignore files ending in "o1.C01".

    Returns
    -------
    missed : list of string
        A list of filenames that have no equivalent in the output being
        tested.
    not_equal : list of string
        A list of filenames in which the output image and the reference
        image don't match.
    """
    out_paths = os.walk(out_dir)
    res_paths = os.walk(res_dir)
    missed = []
    not_equal = []
    files_counted = 0
    for ((res_path, _, res_files), (out_path, _, out_files)) in \
                                        zip(res_paths, out_paths):
        res_files = filter(lambda fn: fn.endswith('.tif'), res_files)
        res_files = sorted(res_files)
        out_files = set(out_files)
        for resfn in res_files:
            files_counted += 1
            reference_file = os.path.join(res_path, resfn)
            if resfn not in out_files:
                missed.append(reference_file)
            else:
                out_im = io.imread(os.path.join(out_path, resfn))
                res_im = io.imread(reference_file)
                percent_off = (out_im - res_im).astype(np.float) / res_im.max()
                if np.any(np.abs(percent_off) > 0.01):
                    not_equal.append(reference_file)
    print("%i files counted" % files_counted)
    return missed, not_equal


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Test the cellom2tif converter.')
    parser.add_argument('-m', '--ignore-masks', action='store_true',
                        help='Ignore files ending in "o1.C01".')
    parser.add_argument('-o', '--output-file', dest='fout', action=open_write,
                        default=sys.stdout,
                        help='Write output to this file, or stdout if not ' +
                        'provided. Caution: will overwrite existing files.')

    args = parser.parse_args()
    shutil.rmtree(test_output_dir, ignore_errors=True)
    shutil.rmtree(test_output_mask_dir, ignore_errors=True)

    call = ['python', 'cellom2tif.py']
    if not args.ignore_masks:
        flags = []
        indirs = [test_data_dir, test_output_dir]
        resdir = test_results_dir
    else:
        flags = ['-m']
        indirs = [test_data_dir, test_output_mask_dir]
        resdir = test_results_mask_dir
    cmd_line = call + flags + indirs
    print(' '.join(cmd_line))
    sp.call(call + flags + indirs, shell=False)
    missing, not_equal = find_errors(indirs[1], resdir, args.ignore_masks)

    if len(missing) > 0 or len(not_equal) > 0:
        args.fout.write('# Missed files:')
        for fn in missing:
            args.fout.write('  ' + fn + '\n')
        args.fout.write('# Images do not match:')
        for fn in not_equal:
            args.fout.write('  ' + fn + '\n')
    else:
        shutil.rmtree(test_output_dir, ignore_errors=True)
        shutil.rmtree(test_output_mask_dir, ignore_errors=True)
        if args.fout.name != '<stdout>':
            args.fout.close()
            os.remove(args.fout.name)

