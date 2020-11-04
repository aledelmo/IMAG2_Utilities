import os
import qt
import ctk
import slicer
import os.path
import unittest
import tempfile
import numpy as np
import nibabel as nib

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

        self.cut_to_bbox = qt.QCheckBox('Cut to BBox')
        self.cut_to_bbox.setChecked(False)
        dice_form_layout.addRow(self.cut_to_bbox)

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
                "DICE = {:.2f}".format(self.logic.dice(mask1, mask2, self.cut_to_bbox.isChecked())))

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
    @staticmethod
    def dice(m1, m2, cut=False):
        if cut:
            x, y, z = np.where(m1)
            x = sorted(x)
            y = sorted(y)
            z = sorted(z)
            bbox = (slice(x[0], x[-1]), slice(y[0], y[-1]), slice(z[0], z[-1]))
            mask = np.zeros(m1.shape)
            mask[bbox] = m2[bbox]
            m2 = mask
        return 100 * np.sum(m1[m1 == m2]) * 2.0 / (np.sum(m1) + np.sum(m2))


class IMAG2UtilitiesTest(unittest.TestCase):

    def __init__(self):
        super(IMAG2UtilitiesTest, self).__init__()

    def __repr__(self):
        return 'IMAG2Utilities(). Derived from {}'.format(unittest.TestCase)

    def __str__(self):
        return 'IMAG2Utilities test class'

    def run_test(self, scenario=None):
        pass


def load_nii(filename):
    img = nib.as_closest_canonical(nib.load(filename))
    return img.get_data(), img.affine
