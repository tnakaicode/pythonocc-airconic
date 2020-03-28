# -*- coding: utf-8 -*-
# MainWindow class and most of this file are edited from OCC.Display.SimpleGui
# @Author: p-chambers
# @Date:   2016-08-23 14:43:28
# @Last Modified by:   p-chambers
# @Last Modified time: 2016-10-07 15:05:47
import logging
import os
import sys

from OCC import VERSION
from OCC.Display.backend import load_backend, get_qt_modules
from . import Topology
import matplotlib.pyplot as plt
import numpy as np
import itertools

log = logging.getLogger(__name__)


def check_callable(_callable):
    if not callable(_callable):
        raise AssertionError("The function supplied is not callable")


# Currently only trying qt
used_backend = load_backend()
log.info("GUI backend set to: {0}".format(used_backend))


from OCC.Display.qtDisplay import qtViewer3d
QtCore, QtGui, QtWidgets, QtOpenGL = get_qt_modules()

from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas)

from .matplotlib_radar import radar_factory, example_data


class Airconics_Viewgrid(QtWidgets.QWidget):
    """A simple grid containing both a 3d viewer and a range of performance
    metrics for the geometry contained in the widget

    Inputs
    ------
    Topology - airconics.Toplogy (default None)
        The Topology to display in this widget: see attributes. If no Topology
        is specified. An empty Topology will be created

    Attributes
    ----------
    Topology - airconics.Topology object
        The aircraft topology object which is mapped to this viewer. This is
        intended to not be deleted.

    Notes
    -----
    """
    select_clicked = QtCore.pyqtSignal()

    # Note: Some of these have a min target, some have max... misleading
    data_labels = ['Static Margin', 'Fuel Burn',
                   'Cost', 'Weight', 'Range', 'Payload']

    colors = itertools.cycle(['b', 'r', 'g', 'm', 'y'])

    def __init__(self, Topology=None, *args):
        super(Airconics_Viewgrid, self).__init__()

        # Create a blank topology object if one has not been provided
        if Topology:
            self._Topology = Topology
        else:
            self._Topology = Topology()

        # Matplotlib colour character (different for each instance)
        self.color = next(self.colors)

        grid = QtGui.QGridLayout(self)
        self.setLayout(grid)
        viewer = qtViewer3d(*args)

        viewer.setMinimumSize(200, 200)

        self.viewer = viewer

        grid.setSpacing(10)
        grid.setMargin(10)

        # Add the viewer spanning 3/4 of the width of the widget
        grid.addWidget(viewer, 0, 0, 1, 1)

        self.InitDataCanvas()

        # Add the canvas to a new VBox layout with a title
        data_group = QtGui.QGroupBox("Estimated Performance Metrics")
        data_box = QtGui.QVBoxLayout(data_group)

        data_box.addWidget(self._data_canvas)

        data_group.setLayout(data_box)

        grid.addWidget(data_group, 0, 1)

        self.select_button = QtGui.QPushButton('Select', self)

        grid.addWidget(self.select_button, 1, 0, 1, 2)

        self.select_clicked.connect(self.Evolve)

        self._Topology.Display(self.viewer._display)

    @property
    def Topology(self):
        return self._Topology

    @Topology.setter
    def Topology(self, newTopology):
        self._Topology = newTopology
        self._Topology.Display(self.viewer._display)
        self.viewer._display.FitAll()

    # @QtCore.pyqtSlot()
    # def onSelectButtonClick(self):
    #     Airconics_Viewgrid.select_clicked.emit()

    @QtCore.pyqtSlot()
    def Evolve(self):
        self.viewer._display.EraseAll()
        self.Topology.Display(self.viewer._display)

        Nvars = len(self.data_labels)

        # This initialises some data in the radar plot: remove this later!
        data = np.random.random(Nvars)

        self._ax.plot(self.radar_factory, data, color=self.color)
        self._ax.fill(self.radar_factory, data, facecolor=self.color,
                      alpha=0.25)

        self._data_canvas.repaint()
        self._ax.redraw_in_frame()

    def InitDataCanvas(self):
        """Initialises a radar chart in self._data_canvas to be embedded in
        the parent viewer widget

        The radar chart contains the labels defined at the class level via
        self.data_labels.
        """
        # Labels
        # labels = []
        # outputs = []

        # data_group = QtGui.QGroupBox("Estimated Performance Metrics")
        # data_gridlayout = QtGui.QVBoxLayout(data_group)

        # for i, lbl_string in enumerate(self.data_box_labels):
        #     label = QtGui.QLabel(lbl_string)
        #     labels.append(label)

        #     # output = QtGui.QLineEdit("Nil")
        #     # output.setReadOnly(True)
        #     # outputs.append(output)

        #     data_gridlayout.addWidget(label)
        #     # data_gridlayout.addWidget(output, i, 1)

        # data_group.setLayout(data_gridlayout)
        Nvars = len(self.data_labels)
        # Nvars = len(self.data_labels)
        self.radar_factory = radar_factory(Nvars, frame='polygon')

        # This initialises some data in the radar plot: remove this later!
        data = np.random.random(Nvars)

        self._fig = plt.figure(facecolor="white")
        self._ax = self._fig.add_subplot(111, projection='radar')

        self._ax.set_rgrids([0.2, 0.4, 0.6, 0.8])
        self._ax.set_rmin(0.)
        self._ax.set_rmax(1.)

        self._ax.plot(self.radar_factory, data, color=self.color)
        self._ax.fill(self.radar_factory, data, facecolor=self.color,
                      alpha=0.25)
        self._ax.set_varlabels(self.data_labels)

        # plt.tight_layout()

        self._data_canvas = FigureCanvas(self._fig)
        self._data_canvas.setParent(self)
        self._data_canvas.setFocusPolicy(QtCore.Qt.StrongFocus)

        # self._data_canvas.setMinimumSize(200, 200)
        self._data_canvas.setMaximumSize(200, 200)


class MainWindow(QtWidgets.QMainWindow):
    """The main Aircraft Topology (configuration) App.

    A number of 3D AirconicsViewgrids (equal to NX * NY) will be created in
    this mainwindow widget. Select buttons of each widget are connected to
    a single slot, such that all topologies rebuild (i.e., are 'evolved') from
    the selected parent.

    Selection of visibly 'fit' aircraft models should be based on both the
    information displayed in the radar chart in the widget, and the users
    sensible judgement based on manufacturability and feasibility.

    Parameters
    ----------
    size : tuple of scalar, length 2 (default 1024 768)
        The (x, y) size of the main window widget, in pixels

    NX, NY : int
        The number of widgets (geometry viewers) in the horizontal/vertical
        direction

    Topologies : list of airconics.Topology
        The topologies to be used in each of the viewers (default empty list)

    Notes
    -----
    This is currently in development, and currently no topology evolution is
    performed.
    """
    global_select_clicked = QtCore.pyqtSignal()

    def __init__(self, size=(1024, 768),
                 NX=2,
                 NY=2,
                 Topologies=[],
                 *args):
        QtWidgets.QMainWindow.__init__(self, *args)
        self.setWindowTitle(
            "occ-airconics aircraft topology app ('%s' backend)" %
            (used_backend))

        # Set up the main widget (this will have several widgets nested within)
        self.main_widget = QtGui.QWidget(self)
        self.setCentralWidget(self.main_widget)

        grid = QtGui.QGridLayout(self.main_widget)
        self.setLayout(grid)

        # Set up the grid (i, j) widget layout
        positions = [(i, j) for i in range(NX) for j in range(NY)]

        # Add the sub widgets for evolved topology options (9 for now?)
        self.viewer_grids = []

        for position in positions:
            viewer_grid = Airconics_Viewgrid()
            grid.addWidget(viewer_grid, *position)

            # connect the select button from the viewer grid to the signal
            viewer_grid.select_button.clicked.connect(
                self.global_select_clicked)

            self.viewer_grids.append(viewer_grid)

        # Connect the main signal to the rebuild function
        self.global_select_clicked.connect(self.onAnySelectClicked)

        if not sys.platform == 'darwin':
            self.menu_bar = self.menuBar()
        else:
            # create a parentless menubar
            # see: http://stackoverflow.com/questions/11375176/qmenubar-and-qmenu-doesnt-show-in-mac-os-x?lq=1
            # noticeable is that the menu ( alas ) is created in the
            # topleft of the screen, just
            # next to the apple icon
            # still does ugly things like showing the "Python" menu in
            # bold
            self.menu_bar = QtWidgets.QMenuBar()
        self._menus = {}
        self._menu_methods = {}

        # place the window in the center of the screen, at half the
        # screen size
        self.centerOnScreen()

        self.resize(size[0], size[1])

    def centerOnScreen(self):
        '''Centers the window on the screen.'''
        resolution = QtWidgets.QDesktopWidget().screenGeometry()
        self.move((resolution.width() / 2) - (self.frameSize().width() / 2),
                  (resolution.height() / 2) - (self.frameSize().height() / 2))

    def add_menu(self, menu_name):
        _menu = self.menu_bar.addMenu("&" + menu_name)
        self._menus[menu_name] = _menu

    def add_function_to_menu(self, menu_name, _callable):
        check_callable(_callable)
        try:
            _action = QtWidgets.QAction(
                _callable.__name__.replace('_', ' ').lower(), self)
            # if not, the "exit" action is now shown...
            _action.setMenuRole(QtWidgets.QAction.NoRole)
            _action.triggered.connect(_callable)

            self._menus[menu_name].addAction(_action)
        except KeyError:
            raise ValueError('the menu item %s does not exist' % menu_name)

    @QtCore.pyqtSlot()
    def onAnySelectClicked(self):
        for viewer in self.viewer_grids:
            viewer.select_clicked.emit()


if __name__ == '__main__':
    from pkg_resources import resource_filename
    app = QtWidgets.QApplication.instance()
    # checks if QApplication already exists
    if not app:  # create QApplication if it doesnt exist
        app = QtWidgets.QApplication(sys.argv)

    # Set up the splash loading screen
    res_pkg = 'airconics.resources.images'
    cover_name = 'cover.png'

    splash_png = resource_filename(res_pkg, cover_name)
    splash_pix = QtGui.QPixmap(splash_png)

    splash = QtGui.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())

    progressBar = QtGui.QProgressBar(splash)

    splash.show()

    app.processEvents()

    win = MainWindow()

    splash.finish(win)

    win.raise_()  # make the application float to the top

    # Add some stuff to test the app
    from . import LiftingSurface, Topology, Airfoil
    from . import AirCONICStools as act
    from .liftingsurface import airfoilfunct
    import copy

    def blended_winglet():
        # Position of the apex of the wing
        P = (0, 0, 0)

        # Class definition
        NSeg = 1

        # Instantiate the class
        ChordFactor = 0.3
        ScaleFactor = 7.951

        def myDihedralFunction(Epsilon):
            return 7

        def myTwistFunction(Epsilon):
            return Epsilon * -2

        myChordFunction = act.Generate_InterpFunction([1, 0.33], [0, 1])

        @airfoilfunct
        def myAirfoilFunction(eps):
            af_root = Airfoil(SeligProfile='naca63a418')
            af_tip = Airfoil(SeligProfile='naca63a412')

            profile_dict = {'InterpProfile': True, 'Epsilon': eps,
                            'Af1': af_root, 'Af2': af_tip, 'Eps1': 0,
                            'Eps2': 1}
            return profile_dict

        def mySweepAngleFunction(Epsilon):
            return 3

        Wing = LiftingSurface(P, mySweepAngleFunction,
                              myDihedralFunction,
                              myTwistFunction,
                              myChordFunction,
                              myAirfoilFunction,
                              SegmentNo=NSeg,
                              ScaleFactor=ScaleFactor,
                              ChordFactor=ChordFactor)

        Winglet = Wing.Fit_BlendedTipDevice(
            0.8,
            cant=15)

        topo = Topology()
        topo.AddPart(Wing, 'Wing', 1)
        topo.AddPart(Winglet, 'Winglet', 0)
        return topo

    # For now I'll just make one fully constructed version and copy it
    main_topo = blended_winglet()

    win.show()

    for viewer_grid in win.viewer_grids:
        viewer_grid.viewer.InitDriver()
        topo = copy.copy(main_topo)
        print(type(viewer_grid))
        # topo.Display(viewer_grid.viewer._display)
        viewer_grid.Topology = main_topo

    # add_menu('primitives')
    # add_function_to_menu('primitives', sphere)
    # add_function_to_menu('primitives', cube)
    # add_function_to_menu('primitives', exit)

    sys.exit(app.exec_())
