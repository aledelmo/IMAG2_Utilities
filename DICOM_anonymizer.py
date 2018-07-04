#!/usr/bin/env python

import argparse
import os.path
import sys

import pydicom

try:
    from os import scandir, walk
except ImportError:
    from scandir import scandir, walk
try:
    from joblib import Parallel, delayed, cpu_count
    from psutil import virtual_memory

    parallel = True
except:
    parallel = False

__author__ = 'Alessandro Delmonte'
__email__ = 'delmonte.ale92@gmail.com'


def main():
    dir_path, q, e = setup()

    if q:
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    for root, _, files in walk(dir_path):
        if not e:
            if 'DICOM' in root:
                if files:
                    if parallel:
                        num_cores = cpu_count()
                        Parallel(n_jobs=num_cores)(delayed(anonymize_par)(root, img) for img in files)
                    else:
                        anonymize(root, files)
        else:
            if parallel:
                num_cores = cpu_count()
                Parallel(n_jobs=num_cores)(delayed(anonymize_par)(root, img) for img in files if img.endswith('.dcm'))
            else:
                anonymize(root, files, e)


def anonymize_par(directory, img):
    try:
        ds = pydicom.dcmread(os.path.join(directory, img))
        ds.remove_private_tags()
        ds.walk(type1_callback)
        ds.walk(type2_callback)
        ds.walk(type3_callback)

        type4_tags = ['OtherPatientIDsSequence']
        for tag in type4_tags:
            if tag in ds:
                delattr(ds, tag)

        os.remove(os.path.join(directory, img))
        ds.save_as(os.path.join(directory, img))
    except:
        print 'Non DICOM file found in {}'.format(os.path.normpath(directory))


def anonymize(directory, files, e=False):
    for img in files:
        if e and img.endswith('.dcm'):
            try:
                ds = pydicom.dcmread(os.path.join(directory, img))
                ds.remove_private_tags()
                ds.walk(type1_callback)
                ds.walk(type2_callback)
                ds.walk(type3_callback)

                type4_tags = ['OtherPatientIDsSequence']
                for tag in type4_tags:
                    if tag in ds:
                        delattr(ds, tag)

                os.remove(os.path.join(directory, img))
                ds.save_as(os.path.join(directory, img))
            except:
                print 'Non DICOM file found in {}'.format(os.path.normpath(directory))


def type1_callback(ds, data_element):
    type1_tags = ['PN']
    for tag in type1_tags:
        if data_element.VR == tag:
            data_element.value = "Anonymous"


def type2_callback(ds, data_element):
    if data_element.VR == 'DA':
        data_element.value = "20000101"
    if data_element.VR == 'TM':
        data_element.value = "000000"


def type3_callback(ds, data_element):
    if data_element.VR == 'LO':
        data_element.value = "(??)"
    if data_element.VR == 'SH':
        data_element.value = "(??)"


def setup():
    parser = argparse.ArgumentParser()
    parser.add_argument('DICOM_Folder', help='Database to anonimyze', type=check_folder)
    parser.add_argument('-e', '--ext', help='Anonymize by file extension (.dcm, default: by folder name)',
                        action='store_true')
    parser.add_argument('-q', '--quiet', help='Suppress output', action='store_true')

    args = parser.parse_args()

    return args.DICOM_Folder, args.quiet, args.ext


def check_folder(value):
    if not os.path.isdir(value):
        raise argparse.ArgumentTypeError('Path is not a directory: %s' % value)
    else:
        return value


if __name__ == '__main__':
    main()
    sys.exit()
