import os
import unittest

import ctk
import qt
import slicer

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

        def create_hor_layout(elements):
            widget = qt.QWidget()
            row_layout = qt.QHBoxLayout()
            widget.setLayout(row_layout)
            for element in elements:
                row_layout.addWidget(element)
            return widget

        self.layout.addStretch(1)

        if self.developerMode:
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
