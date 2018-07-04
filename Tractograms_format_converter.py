#!/usr/bin/env python

import os
import sys
import vtk
import argparse
import numpy as np
from itertools import izip
from vtk.util import numpy_support as ns
from nibabel.streamlines.trk import TrkFile as tv
from nibabel.streamlines.tck import TckFile as tck
from nibabel.streamlines.tractogram import Tractogram

def main():
    in_file, out_format = setup()
    filename, file_extension = os.path.splitext(in_file)
    if file_extension == '.vtk':
        streamlines = read_vtk(in_file)[0]
    elif file_extension == '.trk':
        streamlines, _ = read_trk(in_file)
    else:
        streamlines, _ = read_tck(in_file)
	
    file_name, _ = os.path.splitext(in_file)
    if out_format == 'vtk':
        save_vtk(file_name + '.vtk', streamlines)
    elif out_format == 'trk':
        header = None
        save_trk(file_name + '.trk', streamlines, header)
    else:
        header = None
        save_tck(file_name + '.tck', streamlines, header)


def read_tck(filename):
    tck_object = tck.load(filename)
    streamlines = tck_object.streamlines
    header = tck_object.header

    return streamlines, header


def read_trk(filename):
    trk_object = tv.load(filename)
    streamlines = trk_object.streamlines
    header = trk_object.header

    return streamlines, header


def save_tck(filename, tracts, header):
    tractogram = Tractogram(tracts, affine_to_rasmm=np.eye(4))
    tck_obj = tck(tractogram, header)
    tck_obj.save(filename)


def save_trk(filename, tracts, header):
    tractogram = Tractogram(tracts, affine_to_rasmm=np.eye(4))
    trk_obj = tv(tractogram, header)
    trk_obj.save(filename)


def read_vtk(filename):
    if filename.endswith('xml') or filename.endswith('vtp'):
        polydata_reader = vtk.vtkXMLPolyDataReader()
    else:
        polydata_reader = vtk.vtkPolyDataReader()

    polydata_reader.SetFileName(filename)
    polydata_reader.Update()

    polydata = polydata_reader.GetOutput()

    return vtkPolyData_to_tracts(polydata)


def vtkPolyData_to_tracts(polydata):
    result = {}
    result['lines'] = ns.vtk_to_numpy(polydata.GetLines().GetData())
    result['points'] = ns.vtk_to_numpy(polydata.GetPoints().GetData())
    result['numberOfLines'] = polydata.GetNumberOfLines()

    data = {}
    if polydata.GetPointData().GetScalars():
        data['ActiveScalars'] = polydata.GetPointData().GetScalars().GetName()
    if polydata.GetPointData().GetVectors():
        data['ActiveVectors'] = polydata.GetPointData().GetVectors().GetName()
    if polydata.GetPointData().GetTensors():
        data['ActiveTensors'] = polydata.GetPointData().GetTensors().GetName()

    for i in xrange(polydata.GetPointData().GetNumberOfArrays()):
        array = polydata.GetPointData().GetArray(i)
        np_array = ns.vtk_to_numpy(array)
        if np_array.ndim == 1:
            np_array = np_array.reshape(len(np_array), 1)
        data[polydata.GetPointData().GetArrayName(i)] = np_array

    result['pointData'] = data

    tracts, data = vtkPolyData_dictionary_to_tracts_and_data(result)
    return tracts, data


def vtkPolyData_dictionary_to_tracts_and_data(dictionary):
    dictionary_keys = set(('lines', 'points', 'numberOfLines'))
    if not dictionary_keys.issubset(dictionary.keys()):
        raise ValueError("Dictionary must have the keys lines and points" + repr(dictionary.keys()))

    tract_data = {}
    tracts = []

    lines = np.asarray(dictionary['lines']).squeeze()
    points = dictionary['points']

    actual_line_index = 0
    number_of_tracts = dictionary['numberOfLines']
    original_lines = []
    for l in xrange(number_of_tracts):
        tracts.append(points[lines[actual_line_index + 1:actual_line_index + lines[actual_line_index] + 1]])
        original_lines.append(
            np.array(lines[actual_line_index + 1:actual_line_index + lines[actual_line_index] + 1], copy=True))
        actual_line_index += lines[actual_line_index] + 1

    if 'pointData' in dictionary:
        point_data_keys = [it[0] for it in dictionary['pointData'].items() if isinstance(it[1], np.ndarray)]

        for k in point_data_keys:
            array_data = dictionary['pointData'][k]
            if not k in tract_data:
                tract_data[k] = [array_data[f] for f in original_lines]
            else:
                np.vstack(tract_data[k])
                tract_data[k].extend([array_data[f] for f in original_lines[-number_of_tracts:]])

    return tracts, tract_data


def save_vtk(filename, tracts, lines_indices=None):
    lengths = [len(p) for p in tracts]
    line_starts = ns.numpy.r_[0, ns.numpy.cumsum(lengths)]
    if lines_indices is None:
        lines_indices = [ns.numpy.arange(length) + line_start for length, line_start in izip(lengths, line_starts)]
	
    ids = ns.numpy.hstack([ns.numpy.r_[c[0], c[1]] for c in izip(lengths, lines_indices)])
    vtk_ids = ns.numpy_to_vtkIdTypeArray(ids.astype('int64'), deep=True)

    cell_array = vtk.vtkCellArray()
    cell_array.SetCells(len(tracts), vtk_ids)
    points = ns.numpy.vstack(tracts).astype(ns.get_vtk_to_numpy_typemap()[vtk.VTK_DOUBLE])
    points_array = ns.numpy_to_vtk(points, deep=True)

    poly_data = vtk.vtkPolyData()
    vtk_points = vtk.vtkPoints()
    vtk_points.SetData(points_array)
    poly_data.SetPoints(vtk_points)
    poly_data.SetLines(cell_array)

    poly_data.BuildCells()

    if filename.endswith('.xml') or filename.endswith('.vtp'):
        writer = vtk.vtkXMLPolyDataWriter()
        writer.SetDataModeToBinary()
    else:
        writer = vtk.vtkPolyDataWriter()
        writer.SetFileTypeToBinary()

    writer.SetFileName(filename)
    if hasattr(vtk, 'VTK_MAJOR_VERSION') and vtk.VTK_MAJOR_VERSION > 5:
        writer.SetInputData(poly_data)
    else:
        writer.SetInput(poly_data)
    writer.Write()


def check_ext(value):
    filename, file_extension = os.path.splitext(value)
    if file_extension in ('.tck', '.trk', '.vtk', '.xml', '.vtp'):
        return value
    else:
        raise argparse.ArgumentTypeError(
            "Invalid file extension (file format supported: tck,trk,vtk,xml,vtp): %r" % value)


def check_format(value):
    if value.lower() in ('tck', 'trk', 'vtk', 'xml', 'vtp'):
        return value
    else:
        raise argparse.ArgumentTypeError(
            "Invalid file extension (file format supported: tck,trk,vtk,xml,vtp): %r" % value)


def setup():
    parser = argparse.ArgumentParser()
    parser.add_argument('Input_Tractogram', help='Name of the input file', type=check_ext)
    parser.add_argument('Output_Format', help='File format of the output file', type=check_format)
    args = parser.parse_args()

    return args.Input_Tractogram, args.Output_Format


if __name__ == "__main__":
    main()
    sys.exit()
