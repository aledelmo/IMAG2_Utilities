#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os.path
import sys
import random
import string
import pydicom
from builtins import range

try:
    from os import scandir, walk
except ImportError:
    from scandir import scandir, walk
try:
    from joblib import Parallel, delayed, cpu_count

    par = True
except:
    par = False

__author__ = 'Alessandro Delmonte'
__email__ = 'delmonte.ale92@gmail.com'


def main():
    dir_path, q = setup()

    if q:
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    if par:
        print('Parallel computing enabled')
        with Parallel(n_jobs=cpu_count(), backend='threading') as parallel:
            parallel(delayed(anonymize)(root, files) for root, _, files in walk(dir_path))
    else:
        print('Parallel computing not available (install joblib)')
        for root, _, files in walk(dir_path):
            anonymize(root, files)


def anonymize(root, files):
    files = [os.path.join(root, file) for file in files]
    random_string = ''.join(random.choice(string.ascii_uppercase) for _ in range(8))
    for file in files:
        try:
            ds = pydicom.dcmread(file)

            ds.walk(del_callback)

            ds.data_element('PatientName').value = random_string
            ds.data_element('PatientID').value = "(??)"
            ds.data_element('InstitutionName').value = "(??)"
            ds.data_element('SeriesDescription').value = "(??)"
            ds.data_element('ProtocolName').value = "(??)"

            for tag in ['PatientWeight', 'AdditionalPatientHistory']:
                if tag in ds:
                    delattr(ds, tag)

            os.remove(file)
            ds.save_as(file)
        except:
            pass


def del_callback(ds, data_element):
    if data_element.VR == 'PN':
        data_element.value = 'ANONYMOUS'
    if data_element.VR == 'DA':
        data_element.value = "20000101"
    if data_element.VR == 'TM':
        data_element.value = "000000"
    if data_element.VR == 'SH':
        data_element.value = "(??)"


def setup():
    parser = argparse.ArgumentParser()
    parser.add_argument('DICOM_Folder', help='Database to anonimyze', type=check_folder)
    parser.add_argument('-q', '--quiet', help='Suppress output', action='store_true')

    args = parser.parse_args()

    return args.DICOM_Folder, args.quiet


def check_folder(value):
    if not os.path.isdir(value):
        raise argparse.ArgumentTypeError('Path is not a directory: %s' % value)
    else:
        return value


if __name__ == '__main__':
    main()
    sys.exit()
