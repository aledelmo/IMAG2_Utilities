import os
import os.path
import random
import string
import unittest
from builtins import range
import glob
import ctk
import numpy as np
import pydicom
import qt
import slicer
import tempfile
import vtk
from joblib import Parallel, delayed, cpu_count
from nibabel.streamlines.tck import TckFile as tck
from nibabel.streamlines.tractogram import Tractogram
from nibabel.streamlines.trk import TrkFile as tv
from vtk.util import numpy_support as ns
from nibabel.affines import apply_affine
from dipy.tracking.streamline import values_from_volume
import nibabel as nib

try:
    from os import scandir, walk
except ImportError:
    from scandir import scandir, walk

__author__ = 'Alessandro Delmonte'
__email__ = 'delmonte.ale92@gmail.com'


class IMAG2Utilities:
    def __init__(self, parent):
        parent.title = 'IMAG2 Utilities'
        parent.categories = ['IMAG2']
        parent.dependencies = []
        parent.contributors = ['Alessandro Delmonte (IMAG2)']
        parent.helpText = '''INSERT HELP TEXT.'''
        parent.acknowledgementText = '''Module developed for 3DSlicer (<a>http://www.slicer.org</a>)'''

        self.parent = parent

        module_dir = os.path.dirname(self.parent.path)
        icon_path = os.path.join(module_dir, 'Resources', 'icon.png')
        if os.path.isfile(icon_path):
            parent.icon = qt.QIcon(icon_path)

        try:
            slicer.selfTests
        except AttributeError:
            slicer.selfTests = {}
        slicer.selfTests['IMAG2Utilities'] = self.run_test

    def __repr__(self):
        return 'IMAG2Utilities(parent={})'.format(self.parent)

    def __str__(self):
        return 'IMAG2Utilities module initialization class.'

    @staticmethod
    def run_test():
        tester = IMAG2UtilitiesTest()
        tester.run_test()


class IMAG2UtilitiesWidget:
    def __init__(self, parent=None):
        self.module_name = self.__class__.__name__
        if self.module_name.endswith('Widget'):
            self.module_name = self.module_name[:-6]
        settings = qt.QSettings()
        try:
            self.developerMode = settings.value('Developer/DeveloperMode').lower() == 'true'
        except AttributeError:
            self.developerMode = settings.value('Developer/DeveloperMode') is True

        self.logic = IMAG2UtilitiesLogic()
        self.tmp = tempfile.mkdtemp()

        if not parent:
            self.parent = slicer.qMRMLWidget()
            self.parent.setLayout(qt.QVBoxLayout())
            self.parent.setMRMLScene(slicer.mrmlScene)
        else:
            self.parent = parent
        self.layout = self.parent.layout()

        if not parent:
            self.setup()
            self.parent.show()

    def __repr__(self):
        return 'IMAG2UtilitiesWidget(parent={})'.format(self.parent)

    def __str__(self):
        return 'IMAG2Utilities GUI class'

    def setup(self):

        converter_collapsible_button = ctk.ctkCollapsibleButton()
        converter_collapsible_button.text = 'Tractogram format converter'

        self.layout.addWidget(converter_collapsible_button)

        converter_form_layout = qt.QFormLayout(converter_collapsible_button)

        label_converter = qt.QLabel()
        label_converter.setText(
            "Convert an existing tractogram file between the three most used format (.tck, .trk, .vtk).<br>The conversion"
            " can be performed, for every possible combination, in both directions.<br>")
        converter_form_layout.addRow(label_converter)

        self.input_file_selector = ctk.ctkPathLineEdit()
        self.input_file_selector.filters = ctk.ctkPathLineEdit.Files | ctk.ctkPathLineEdit.Writable | \
                                           ctk.ctkPathLineEdit.Hidden
        self.input_file_selector.addCurrentPathToHistory()
        converter_form_layout.addRow("Input File: ", self.input_file_selector)

        self.output_file_selector = ctk.ctkPathLineEdit()
        self.output_file_selector.filters = ctk.ctkPathLineEdit.Files | ctk.ctkPathLineEdit.Writable | \
                                            ctk.ctkPathLineEdit.Hidden
        self.output_file_selector.addCurrentPathToHistory()
        converter_form_layout.addRow("Output File: ", self.output_file_selector)

        self.convert_button = qt.QPushButton('Convert')
        self.convert_button.enabled = True
        self.convert_button.connect('clicked(bool)', self.on_convert_button)
        converter_form_layout.addRow(self.convert_button)

        anonim_collapsible_button = ctk.ctkCollapsibleButton()
        anonim_collapsible_button.text = 'DICOM Anonymization'

        self.layout.addWidget(anonim_collapsible_button)

        anonim_form_layout = qt.QFormLayout(anonim_collapsible_button)

        label_anonim = qt.QLabel()
        label_anonim.setText(
            "Completely anonymize a directory containing DICOM images.<br>The processing is propagated to all "
            "the sub-directories.<br>")
        anonim_form_layout.addRow(label_anonim)

        self.dialogfolderbutton = ctk.ctkDirectoryButton()
        self.dir = None
        self.dialogfolderbutton.connect('directoryChanged(const QString&)', self.onApplydialogfolderbutton)
        anonim_form_layout.addRow('DICOM Folder:', self.dialogfolderbutton)

        self.anonim_button = qt.QPushButton('Anonymize')
        self.anonim_button.enabled = True
        self.anonim_button.connect('clicked(bool)', self.on_anonim_button)
        anonim_form_layout.addRow(self.anonim_button)

        split_collapsible_button = ctk.ctkCollapsibleButton()
        split_collapsible_button.text = 'Split Tractograms'

        self.layout.addWidget(split_collapsible_button)

        split_form_layout = qt.QFormLayout(split_collapsible_button)

        label_split = qt.QLabel()
        label_split.setText(
            "Split tractograms in left/right components using sacral holes segmentation.<br>")
        split_form_layout.addRow(label_split)

        self.dialogfolderbutton_split = ctk.ctkDirectoryButton()
        self.dir_split = None
        self.dialogfolderbutton_split.connect('directoryChanged(const QString&)', self.onApplydialogfolderbuttonsplit)
        split_form_layout.addRow('DICOM Folder:', self.dialogfolderbutton_split)

        self.split_button = qt.QPushButton('Split')
        self.split_button.enabled = True
        self.split_button.connect('clicked(bool)', self.on_split_button)
        split_form_layout.addRow(self.split_button)

        dice_collapsible_button = ctk.ctkCollapsibleButton()
        dice_collapsible_button.text = 'Dice Score'

        self.layout.addWidget(dice_collapsible_button)

        dice_form_layout = qt.QFormLayout(dice_collapsible_button)

        label_dice = qt.QLabel()
        label_dice.setText(
            "Compute DICE score between two binary masks.")
        dice_form_layout.addRow(label_dice)

        self.mask1Selector = slicer.qMRMLNodeComboBox()
        self.mask1Selector.nodeTypes = ['vtkMRMLLabelMapVolumeNode']
        self.mask1Selector.selectNodeUponCreation = True
        self.mask1Selector.addEnabled = False
        self.mask1Selector.removeEnabled = False
        self.mask1Selector.noneEnabled = False
        self.mask1Selector.showHidden = False
        self.mask1Selector.renameEnabled = False
        self.mask1Selector.showChildNodeTypes = False
        self.mask1Selector.setMRMLScene(slicer.mrmlScene)

        self.mask1Node = self.mask1Selector.currentNode()

        self.mask1Selector.connect('nodeActivated(vtkMRMLNode*)', self.onmask1Select)

        dice_form_layout.addRow("Mask 1", self.mask1Selector)

        self.mask2Selector = slicer.qMRMLNodeComboBox()
        self.mask2Selector.nodeTypes = ['vtkMRMLLabelMapVolumeNode']
        self.mask2Selector.selectNodeUponCreation = True
        self.mask2Selector.addEnabled = False
        self.mask2Selector.removeEnabled = False
        self.mask2Selector.noneEnabled = False
        self.mask2Selector.showHidden = False
        self.mask2Selector.renameEnabled = False
        self.mask2Selector.showChildNodeTypes = False
        self.mask2Selector.setMRMLScene(slicer.mrmlScene)

        self.mask2Node = self.mask2Selector.currentNode()

        self.mask2Selector.connect('nodeActivated(vtkMRMLNode*)', self.onmask2Select)

        dice_form_layout.addRow("Mask 2", self.mask2Selector)

        self.dice_button = qt.QPushButton('Compute DICE')
        self.dice_button.enabled = True
        self.dice_button.connect('clicked(bool)', self.on_dice_button)
        dice_form_layout.addRow(self.dice_button)

        self.dice_result = qt.QLabel()
        self.dice_result.setText(
            "DICE = ...")
        dice_form_layout.addRow(self.dice_result)

        self.layout.addStretch(1)

        if self.developerMode:
            def create_hor_layout(elements):
                widget = qt.QWidget()
                row_layout = qt.QHBoxLayout()
                widget.setLayout(row_layout)
                for element in elements:
                    row_layout.addWidget(element)
                return widget

            """Developer interface"""
            self.reload_collapsible_button = ctk.ctkCollapsibleButton()
            self.reload_collapsible_button.text = "Reload && Test"
            self.layout.addWidget(self.reload_collapsible_button)
            reload_form_layout = qt.QFormLayout(self.reload_collapsible_button)

            self.reload_button = qt.QPushButton("Reload")
            self.reload_button.toolTip = "Reload this module."
            self.reload_button.name = "ScriptedLoadableModuleTemplate Reload"
            self.reload_button.connect('clicked()', self.on_reload)

            self.reload_and_test_button = qt.QPushButton("Reload and Test")
            self.reload_and_test_button.toolTip = "Reload this module and then run the self tests."
            self.reload_and_test_button.connect('clicked()', self.on_reload_and_test)

            self.edit_source_button = qt.QPushButton("Edit")
            self.edit_source_button.toolTip = "Edit the module's source code."
            self.edit_source_button.connect('clicked()', self.on_edit_source)

            self.restart_button = qt.QPushButton("Restart Slicer")
            self.restart_button.toolTip = "Restart Slicer"
            self.restart_button.name = "ScriptedLoadableModuleTemplate Restart"
            self.restart_button.connect('clicked()', slicer.app.restart)

            reload_form_layout.addWidget(
                create_hor_layout(
                    [self.reload_button, self.reload_and_test_button, self.edit_source_button, self.restart_button]))

    def onApplydialogfolderbutton(self):
        self.dir = self.dialogfolderbutton.directory

    def onApplydialogfolderbuttonsplit(self):
        self.dir_split = self.dialogfolderbutton_split.directory

    def on_convert_button(self):
        input = self.input_file_selector.currentPath
        output = self.output_file_selector.currentPath
        _, input_ext = os.path.splitext(input)
        _, output_ext = os.path.splitext(output)
        supported_formats = ('.tck', '.trk', '.vtk', '.xml', '.vtp')

        if (input_ext in supported_formats) and (output_ext in supported_formats):
            self.input_file_selector.addCurrentPathToHistory()
            self.output_file_selector.addCurrentPathToHistory()
            if input_ext == '.vtk':
                streamlines = read_vtk(input)[0]
            elif input_ext == '.trk':
                streamlines, _ = read_trk(input)
            else:
                streamlines, _ = read_tck(input)

            if output_ext == 'vtk':
                save_vtk(output, streamlines)
            elif output_ext == 'trk':
                header = None
                save_trk(output, streamlines, header)
            else:
                header = None
                save_tck(output, streamlines, header)

    def on_anonim_button(self):
        if self.dir:
            with Parallel(n_jobs=cpu_count(), backend='threading') as parallel:
                parallel(delayed(anonymize)(root, files) for root, _, files in walk(self.dir))

    def on_split_button(self):
        if self.dir_split:
            for dir in os.listdir(self.dir_split):
                dir = os.path.abspath(os.path.join(self.dir_split, dir))
                if os.path.isdir(dir):
                    seg_path = glob.glob(os.path.join(dir, "*.nii*"))
                    if len(seg_path) > 0:
                        seg, affine = load_nii(seg_path[0])
                        tracts = glob.glob(os.path.join(dir, "*.vtk"))
                        right_side = np.zeros(seg.shape)
                        right_side[(seg == 7) | (seg == 16) | (seg == 19) | (seg == 22) | (seg == 25)] = 1
                        left_side = np.zeros(seg.shape)
                        left_side[(seg == 8) | (seg == 17) | (seg == 20) | (seg == 23) | (seg == 26)] = 1
                        for tract in tracts:
                            lines = read_vtk(tract)[0]
                            right_tracts = []
                            left_tracts = []
                            for i, s in enumerate(streamlines_mapvolume(lines, right_side, affine)):
                                if np.count_nonzero(s) > 0:
                                    right_tracts.append(lines[i])
                            for i, s in enumerate(streamlines_mapvolume(lines, left_side, affine)):
                                if np.count_nonzero(s) > 0:
                                    left_tracts.append(lines[i])

                            if len(right_tracts) > 0:
                                save_vtk(os.path.abspath(os.path.join(dir, os.path.basename(tract) + '_Right.vtk')),
                                         right_tracts)
                            if len(left_tracts) > 0:
                                save_vtk(os.path.abspath(os.path.join(dir, os.path.basename(tract) + '_Left.vtk')),
                                         left_tracts)
                else:
                    print('Skipped {}'.format(dir))

    def onmask1Select(self):
        self.mask1Node = self.mask1Selector.currentNode()

    def onmask2Select(self):
        self.mask2Node = self.mask2Selector.currentNode()

    def on_dice_button(self):
        if self.mask1Node and self.mask2Node:
            mask1_path = os.path.join(self.tmp, 'mask1.nii')
            properties = {'useCompression': 0}
            slicer.util.saveNode(self.mask1Node, mask1_path, properties)

            mask2_path = os.path.join(self.tmp, 'mask2.nii')
            properties = {'useCompression': 0}
            slicer.util.saveNode(self.mask2Node, mask2_path, properties)

            mask1, _ = load_nii(mask1_path)
            mask2, _ = load_nii(mask2_path)

            mask1 = mask1.astype(np.uint8)
            mask2 = mask2.astype(np.uint8)

            self.dice_result.setText(
                "DICE = {}".format(np.sum(mask1[mask1 == mask2]) * 2.0 / (np.sum(mask1) + np.sum(mask2))))

    def on_reload(self):
        print('\n' * 2)
        print('-' * 30)
        print('Reloading module: ' + self.module_name)
        print('-' * 30)
        print('\n' * 2)

        slicer.util.reloadScriptedModule(self.module_name)

    def on_reload_and_test(self):
        try:
            self.on_reload()
            test = slicer.selfTests[self.module_name]
            test()
        except Exception:
            import traceback
            traceback.print_exc()
            error_message = "Reload and Test: Exception!\n\n" + "See Python Console for Stack Trace"
            slicer.util.errorDisplay(error_message)

    def on_edit_source(self):
        file_path = slicer.util.modulePath(self.module_name)
        qt.QDesktopServices.openUrl(qt.QUrl("file:///" + file_path, qt.QUrl.TolerantMode))

    def cleanup(self):
        pass


class IMAG2UtilitiesLogic:
    def __init__(self):
        pass


class IMAG2UtilitiesTest(unittest.TestCase):

    def __init__(self):
        super(IMAG2UtilitiesTest, self).__init__()

    def __repr__(self):
        return 'IMAG2Utilities(). Derived from {}'.format(unittest.TestCase)

    def __str__(self):
        return 'IMAG2Utilities test class'

    def run_test(self, scenario=None):
        pass


def load_nii(fname):
    img = nib.as_closest_canonical(nib.load(fname))
    return img.get_data(), img.affine


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
    result = {'lines': ns.vtk_to_numpy(polydata.GetLines().GetData()),
              'points': ns.vtk_to_numpy(polydata.GetPoints().GetData()), 'numberOfLines': polydata.GetNumberOfLines()}

    data = {}
    if polydata.GetPointData().GetScalars():
        data['ActiveScalars'] = polydata.GetPointData().GetScalars().GetName()
    if polydata.GetPointData().GetVectors():
        data['ActiveVectors'] = polydata.GetPointData().GetVectors().GetName()
    if polydata.GetPointData().GetTensors():
        data['ActiveTensors'] = polydata.GetPointData().GetTensors().GetName()

    for i in range(polydata.GetPointData().GetNumberOfArrays()):
        array = polydata.GetPointData().GetArray(i)
        np_array = ns.vtk_to_numpy(array)
        if np_array.ndim == 1:
            np_array = np_array.reshape(len(np_array), 1)
        data[polydata.GetPointData().GetArrayName(i)] = np_array

    result['pointData'] = data

    tracts, data = vtkPolyData_dictionary_to_tracts_and_data(result)
    return tracts, data


def vtkPolyData_dictionary_to_tracts_and_data(dictionary):
    dictionary_keys = {'lines', 'points', 'numberOfLines'}
    if not dictionary_keys.issubset(dictionary.keys()):
        raise ValueError("Dictionary must have the keys lines and points" + repr(dictionary.keys()))

    tract_data = {}
    tracts = []

    lines = np.asarray(dictionary['lines']).squeeze()
    points = dictionary['points']

    actual_line_index = 0
    number_of_tracts = dictionary['numberOfLines']
    original_lines = []
    for l in range(number_of_tracts):
        tracts.append(points[lines[actual_line_index + 1:actual_line_index + lines[actual_line_index] + 1]])
        original_lines.append(
            np.array(lines[actual_line_index + 1:actual_line_index + lines[actual_line_index] + 1], copy=True))
        actual_line_index += lines[actual_line_index] + 1

    if 'pointData' in dictionary:
        point_data_keys = [it[0] for it in dictionary['pointData'].items() if isinstance(it[1], np.ndarray)]

        for k in point_data_keys:
            array_data = dictionary['pointData'][k]
            if k not in tract_data:
                tract_data[k] = [array_data[f] for f in original_lines]
            else:
                np.vstack(tract_data[k])
                tract_data[k].extend([array_data[f] for f in original_lines[-number_of_tracts:]])

    return tracts, tract_data


def save_vtk(filename, tracts, lines_indices=None):
    lengths = [len(p) for p in tracts]
    line_starts = ns.numpy.r_[0, ns.numpy.cumsum(lengths)]
    if lines_indices is None:
        lines_indices = [ns.numpy.arange(length) + line_start for length, line_start in zip(lengths, line_starts)]

    ids = ns.numpy.hstack([ns.numpy.r_[c[0], c[1]] for c in zip(lengths, lines_indices)])
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


def streamlines_mapvolume(streamlines, volume, affine):
    inverse = np.linalg.inv(affine)
    streamlines = [apply_affine(inverse, np.array(s)) for s in streamlines]
    mapping = values_from_volume(volume, streamlines)

    return mapping


def del_callback(ds, data_element):
    if data_element.VR == 'PN':
        data_element.value = 'ANONYMOUS'
    if data_element.VR == 'DA':
        data_element.value = "20000101"
    if data_element.VR == 'TM':
        data_element.value = "000000"
    if data_element.VR == 'SH':
        data_element.value = "(??)"
