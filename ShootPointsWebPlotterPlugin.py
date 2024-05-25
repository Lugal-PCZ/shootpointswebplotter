import os
import json
from PyQt5.QtWidgets import QAction, QFileDialog
from PyQt5.QtGui import QIcon
from qgis.core import *

from .resources import *


class ShootPointsWebPlotterPlugin:
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        self.action = QAction(
            QIcon(":/plugins/shootpointswebplotter/prism.png"),
            "Add ShootPoints-Web Session Layers…",
            self.iface.mainWindow(),
        )
        self.action.triggered.connect(self.run)
        self.iface.addLayerMenu().addAction(self.action)

    def unload(self):
        self.iface.addLayerMenu().removeAction(self.action)
        del self.action

    def run(self):
        datadirpath = self.get_data_directory_path()
        if datadirpath:
            shootpointsdatagroup = self.find_or_create_shootpoints_data_group()
            sessiongroup = self.create_session_group(datadirpath, shootpointsdatagroup)
            self.plot_data(datadirpath, self.get_styles_path(), sessiongroup)
            self.iface.messageBar().pushMessage(
                "Success",
                f"Shapefiles have been added to the <i>{sessiongroup.name()}</i> group.",
                level=Qgis.Success,
            )

    def get_data_directory_path(self) -> str:
        thepath = QFileDialog.getExistingDirectory()
        if thepath:
            if not os.path.isfile(f"{thepath}/session_info.json"):
                self.iface.messageBar().pushMessage(
                    "Error",
                    f"The <i>{os.path.basename(thepath)}</i> directory is not a valid ShootPoints-Web export.",
                    level=Qgis.Critical,
                )
                thepath = None
            elif not os.path.isdir(f"{thepath}/gis_shapefiles"):
                self.iface.messageBar().pushMessage(
                    "Notice",
                    f"There are no shapefiles in the <i>{os.path.basename(thepath)}</i> export.",
                    level=Qgis.Warning,
                )
                thepath = None
        return thepath

    def find_or_create_shootpoints_data_group(self) -> QgsLayerTreeNode:
        rootgroup = "ShootPoints Data"
        if not (
            shootpointsdatagroup := QgsProject.instance()
            .layerTreeRoot()
            .findGroup(rootgroup)
        ):
            shootpointsdatagroup = (
                QgsProject.instance().layerTreeRoot().insertGroup(0, rootgroup)
            )
        return shootpointsdatagroup

    def create_session_group(
        self, datadirpath, shootpointsdatagroup
    ) -> QgsLayerTreeNode:
        with open(f"{datadirpath}/session_info.json", "r") as f:
            sessioninfo = json.load(f)
            sessionlabel = sessioninfo["session"]["label"]
            sessiongroup = shootpointsdatagroup.addGroup(sessionlabel)
        return sessiongroup

    def get_styles_path(self) -> str:
        stylespath = f"{os.path.dirname(__file__)}/styles/"
        return stylespath

    def plot_data(self, datadirpath, stylespath, sessiongroup) -> None:
        datafiles = [
            "pointclouds.shp",
            "allshots.shp",
            "openpolygons.shp",
            "closedpolygons.shp",
            "spatialcontrol.shp",
        ]
        crssetting = QgsSettings().value("app/projections/unknownCrsBehavior")
        QgsSettings().setValue("app/projections/unknownCrsBehavior", "UseProjectCrs")
        for eachfile in datafiles:
            if os.path.isfile(f"{datadirpath}/gis_shapefiles/{eachfile}"):
                layername = eachfile[:-4]
                newlayer = QgsVectorLayer(
                    f"{datadirpath}/gis_shapefiles/{eachfile}",
                    layername,
                    "ogr",
                )
                QgsProject.instance().addMapLayer(newlayer, False)
                newlayer.loadNamedStyle(f"{stylespath}{layername}.qml")
                sessiongroup.addLayer(newlayer)
        QgsSettings().setValue("app/projections/unknownCrsBehavior", crssetting)
