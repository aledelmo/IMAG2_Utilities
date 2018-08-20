#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import shlex
import shutil
import sys
import tempfile
from subprocess import (Popen, PIPE, call)
from time import time

import pydicom
from joblib import cpu_count

__author__ = 'Alessandro Delmonte'
__email__ = 'delmonte.ale92@gmail.com'


def main():
    in_folder, mask, basename, quiet = setup()
    tmp = tempfile.mkdtemp()

    if quiet:
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    start = time()

    dicom_list = []
    for dirName, subdirList, fileList in os.walk(in_folder):
        for filename in fileList:
            dicom_list.append(os.path.join(dirName, filename))
    reference = pydicom.dcmread(dicom_list[0])
    try:
        if reference.InPlanePhaseEncodingDirection == 'COL':
            phase_encoding_direction = 'AP '
        elif reference.InPlanePhaseEncodingDirection == 'ROW':
            phase_encoding_direction = 'LR '
    except:
        raise AttributeError('No Phase Encoding Direction Information.')

    try:
        diff_dir = reference[0x0019, 0x10e0].value
        diff_dir = int(diff_dir)
    except:
        raise AttributeError('Wrong number of diffusion direction.')

    win_size = 2
    while win_size ** 3 < diff_dir:
        win_size += 1
    win_size = str(win_size)

    # DENOISING
    if mask:
        pipe('dwidenoise ' + in_folder + ' ' + os.path.join(tmp, basename + '_denoise.mif') + ' -extent ' +
             win_size + ' -mask ' + mask, True)
    else:
        pipe('dwidenoise ' + in_folder + ' ' + os.path.join(tmp, basename + '_denoise.mif') + ' -extent ' + win_size,
             True)
    # GIBBS RINGING ARTIFACT REMOVAL
    pipe('mrdegibbs ' + os.path.join(tmp, basename + '_denoise.mif') + ' ' +
         os.path.join(tmp, basename + '_de_n_g.mif'), True)
    # MOTION AND EDDY CURRENTS CORRECTION
    num_cores = str(cpu_count())
    pipe('dwipreproc -nthreads ' + num_cores + ' -tempdir ' + tmp + ' -rpe_none -pe_dir ' + phase_encoding_direction +
         os.path.join(tmp, basename + '_de_n_g.mif') + ' ' + os.path.join(tmp, basename + '_denoise_preproc.mif'),
         True)
    # BIAS CORRECTION (N4 ANTs)
    pipe('dwibiascorrect -ants ' + os.path.join(tmp, basename + '_denoise_preproc.mif') + ' ' +
         os.path.join(tmp, basename + '_ready.mif'))
    pipe('mrconvert ' + os.path.join(tmp, basename + '_ready.mif') + ' ' +
         os.path.join(os.getcwd(), basename + '_preprocessed.nii.gz') + ' -export_grad_fsl ' +
         os.path.join(os.getcwd(), basename + '.bvec') + ' ' + os.path.join(os.getcwd(), basename + '.bval'), True)

    print('Total runtime: %.2f m.' % ((time() - start) / 60.))

    shutil.rmtree(tmp)


def pipe(cmd, verbose=False, topipe=False):
    if verbose:
        print('Executing command: ' + str(cmd) + '\n')
    if topipe:
        p = Popen(cmd, shell=True, stdin=None, stdout=PIPE, stderr=PIPE)
        [stdout, stderr] = p.communicate()
        return stdout, stderr
    else:
        cmd = shlex.split(cmd)
        call(cmd, shell=False, stdin=None, stdout=None, stderr=None)


def check_folder(value):
    if not os.path.isdir(value):
        raise argparse.ArgumentTypeError('Path is not a directory: %s' % value)
    else:
        return os.path.normpath(value)


def check_nii(value):
    if value.split('.')[1] in ('nii', 'nii.gz'):
        return os.path.normpath(value)
    else:
        raise argparse.ArgumentTypeError('Invalid file extension: %s' % value)


def setup():
    parser = argparse.ArgumentParser()
    parser.add_argument('DICOM_Folder', help='Data folder containing DICOM files', type=check_folder)
    parser.add_argument('-m', '--mask', help='Whole-pelvis mask', type=check_nii)
    parser.add_argument('-n', '--basename', help='Output filename', type=str, default='noname')
    parser.add_argument('-q', '--quiet', help='No ', action='store_true')

    args = parser.parse_args()

    return args.DICOM_Folder, args.mask, args.basename, args.quiet


if __name__ == '__main__':
    main()
    sys.exit(0)
