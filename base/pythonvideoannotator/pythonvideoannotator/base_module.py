#! /usr/bin/python2
# -*- coding: utf-8 -*-
import pypi_xmlrpc
import pip, sys, subprocess

from .__init__ import __version__
from pyforms.basewidget import BaseWidget

from pyforms.controls import ControlPlayer
from pyforms.controls import ControlEventTimeline
from pyforms.controls import ControlDockWidget

from pythonvideoannotator_models_gui.models import Project
from pythonvideoannotator_models_gui.dialogs.dialog import Dialog
from pythonvideoannotator_models.models.video.objects.object2d.datasets.path import Path
from pythonvideoannotator_models.models.video import Video
from pythonvideoannotator_models.models.video.objects.object2d import  Object2D

from .userstats import track_user_stats

from confapp import conf
if conf.PYFORMS_MODE=='GUI':
    from AnyQt import QtCore
    from AnyQt.QtWidgets import QApplication, QFileDialog, QMessageBox
    


def Exit(): exit()

class BaseModule(BaseWidget):
    """Application form"""

    def __init__(self):
        global conf;
        conf += 'pythonvideoannotator.resources'  # Resources can only be loaded after pyqt is running

        super(BaseModule, self).__init__('Video annotation editor')

        self._project  = Project(parent=self)
        Dialog.project = self._project

        self._player    = ControlPlayer("Player")
        self._time      = ControlEventTimeline('Time')
        self._dock      = ControlDockWidget("Timeline", side='bottom', order=1, margin=5)

        self.formset    = ['_player']

        self._dock.value                    = self._time
        self._player.process_frame_event    = self.process_frame_event
        self._player.click_event            = self.on_player_click_event
        self._time.key_release_event        = self.__timeline_key_release_event

        self.load_order = []

        self.mainmenu.insert(0,
            {'File': [
                {'Open': self.__open_project_event, 'icon': conf.ANNOTATOR_ICON_OPEN},
                '-',
                {'Save': self.__save_project_event , 'icon': conf.ANNOTATOR_ICON_SAVE},
                {'Save as': self.__save_project_as_event, 'icon': conf.ANNOTATOR_ICON_SAVE},
                '-',
                {'Exit': QApplication.closeAllWindows, 'icon': conf.ANNOTATOR_ICON_EXIT}
            ] }
        )
        self.mainmenu.insert(1, {'Modules': []} )
        self.mainmenu.insert(2, {'Windows': []} )

        track_user_stats()

        ########################################################################
        ###### CHECK NEW VERSIONS RELEASES #####################################
        ########################################################################
        try:
            versions = pypi_xmlrpc.package_releases('Python-video-annotator')

            if versions is not None:
                new_version = versions[0]
                new_version_numbers = [int(x) for x in new_version.split('.')]
                version_numbers = [int(x) for x in __version__.split('.')]
                for new_n, n in zip(new_version_numbers, version_numbers):
                    if new_n > n:
                        response = self.question(
                            "<h2>New version <b>[{0}]</b> available</h2>"
                            "<p>Do you wish to update the software?</p>"
                            "<p>The software can be updated later by running the next command in the terminal:</p>"
                            "<i>pip install python-video-annotator --force-reinstall</i>".format(new_version),
                            'New version [{0}]'.format(new_version)
                        )

                        if response == 'yes':
                            subprocess.call([sys.executable, "-m", "pip", "install", 'python-video-annotator', '--force-reinstall'])

                            self.message('The software was updated and this session will be closed. Please execute the software again.', 'Restart required')
                            exit()
                        break
            else:
                print('Enabled to check new versions')

        except Exception as e:
            print('Enabled to check new versions:')



    ######################################################################################
    #### FUNCTIONS #######################################################################
    ######################################################################################
        
    def init_form(self):
        super(BaseModule, self).init_form()

        if conf.CHART_FILE_PATH: self._time.import_chart(*conf.CHART_FILE_PATH)
        if conf.PROJECT_PATH:    self.load_project(conf.PROJECT_PATH)


    ######################################################################################
    #### IO FUNCTIONS ####################################################################
    ######################################################################################

    def save(self, data, project_path=None):
        self._project.save(data, project_path)
        return data


    def load(self, data, project_path=None):
        try:
            self._project.load(data, project_path)
        except FileNotFoundError as e:
            QMessageBox.critical(self, "Error", str(e))

    def save_project(self, project_path=None):
        try:
            if project_path is None:
                project_path = QFileDialog.getExistingDirectory(self, "Select the project directory")

            if project_path is not None and str(project_path)!='':
                project_path = str(project_path)
                self.save({}, project_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def load_project(self, project_path=None):
        if project_path is None:
            project_path = QFileDialog.getExistingDirectory(self, "Select the project directory")
        if project_path is not None and str(project_path)!='':
            self.load({}, str(project_path) )



    ######################################################################################
    #### EVENTS ##########################################################################
    ######################################################################################

    def on_player_click_event(self, event, x, y):
        """
        Code to select a blob with the mouse
        """
        super(VideoAnnotationEditor, self).on_player_click_event(event, x, y)
        self._player.refresh()

    def process_frame_event(self, frame):
        """
        Function called before render each frame
        """
        return frame


    def add_dataset_event(self, dataset):
        pass

    def removed_dataset_event(self, dataset):
        pass

    def removed_object_event(self, obj):
        pass


    def __open_project_event(self): self.load_project()

    def __save_project_event(self):
        print('Project saved')
        self.save_project(self._project.directory)

    def __save_project_as_event(self): self.save_project()
    
    def __timeline_key_release_event(self, event):
        """
        Control video playback using the space bar to Play/Pause
        """
        if event.key() == QtCore.Qt.Key_Space:
            self._player.stop() if self._player.is_playing else _player._video.play()

    def keyReleaseEvent(self, event):

        #Select the path of the next object
        if event.key() == QtCore.Qt.Key_L:

            selected = self.project.tree.selected_item

            if selected is not None:

                #If it's a video, try to select the its first object and the object's first child 
                if isinstance(selected.win, Video):

                    if selected.childCount() > 0:
                        child_object = selected.child(0)

                        if child_object.childCount() > 0:
                            self.project.tree.selected_item = child_object.child(0)

                #If it's an object, try to select it's first child
                elif isinstance(selected.win, Object2D):
                    if selected.childCount() > 0:
                        self.project.tree.selected_item = selected.child(0)

                #If it's a path try to select the first child of the next object of their parent video
                elif isinstance(selected.win, Path):

                    parent_object = selected.parent()
                    parent_video = parent_object.parent()

                    parent_object_index = parent_video.indexOfChild(parent_object)

                    if parent_object_index < parent_video.childCount() -1 :
                        next_object = parent_video.child(parent_video.indexOfChild(parent_object)+1)

                        if next_object.childCount() > 0:
                            self.project.tree.selected_item = next_object.child(0)

                    #If it's the last object of the video, go back to the path of the first one
                    else:
                        next_object = parent_video.child(0)

                        if next_object.childCount() > 0:
                            self.project.tree.selected_item = next_object.child(0)

        #"Click" the Mark Point button in the current Path
        elif event.key() == QtCore.Qt.Key_K:

            selected = self.project.tree.selected_item

            if selected is not None and isinstance(selected.win, Path):
                path = selected.win

                path.mark_point_button.click()




    ######################################################################################
    #### PROPERTIES ######################################################################
    ######################################################################################

    @property
    def timeline(self): return self._time

    @property
    def player(self): return self._player
    
    @property
    def video(self): return self._player.value
    @video.setter
    def video(self, value): 
        self._player.value      = value
        self._player.enabled    = value is not None
        if value:
            self._time.max = self._player.max

    @property
    def project(self): return self._project
