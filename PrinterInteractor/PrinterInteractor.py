import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import time
import functools
import argparse
import math
import numpy as np


#
# PrinterInteractor
#

class PrinterInteractor(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "PrinterInteractor"  # TODO make this more human readable by adding spaces
        self.parent.categories = ["SlicerSpectroscopy"]
        self.parent.dependencies = []
        self.parent.contributors = [
            "Laura Connolly PerkLab (Queen's University), Mark Asselin PerkLab (Queen's University)"]  # replace with "Firstname Lastname (Organization)"
        self.parent.helpText = """
This is an module developed to interface Slicer Software with the Monoprice Mini V2 3D Printer for spectroscopy 
"""
        self.parent.helpText += self.getDefaultModuleDocumentationLink()
        self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
"""  # replace with organization, grant and thanks.


#
# PrinterInteractorWidget
#

class PrinterInteractorWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """


    def setup(self):

        #self.installShortcutKeys()

        ScriptedLoadableModuleWidget.setup(self)

        # Instantiate and connect widgets ...
        self.logic = PrinterInteractorLogic()
        #
        # Parameters Area
        #
        PrinterControlCollapsibleButton= ctk.ctkCollapsibleButton()
        PrinterControlCollapsibleButton.text = "Printer Control "
        self.layout.addWidget(PrinterControlCollapsibleButton)
        # Layout within the Printer Control collapsible button
        PrinterControlFormLayout = qt.QFormLayout(PrinterControlCollapsibleButton)

        # Contour Tracing tools

        ContourTracingCollapsibleButton = ctk.ctkCollapsibleButton()
        ContourTracingCollapsibleButton.text = " Contour Tracing Tools"
        self.layout.addWidget(ContourTracingCollapsibleButton)
        #
        ContourTracingFormLayout = qt.QFormLayout(ContourTracingCollapsibleButton)

        #
        # Image Registration tools
        #

        ImageRegistrationCollapsibleButton = ctk.ctkCollapsibleButton()
        ImageRegistrationCollapsibleButton.text = " Image Registration Tools"
        self.layout.addWidget(ImageRegistrationCollapsibleButton)
        #
        ImageRegistrationFormLayout = qt.QFormLayout(ImageRegistrationCollapsibleButton)

        #
        # Home Button
        #
        self.homeButton = qt.QPushButton("Home")
        self.homeButton.toolTip = "Return to reference axis"
        self.homeButton.enabled = True
        PrinterControlFormLayout.addRow(self.homeButton)
        self.homeButton.connect('clicked(bool)', self.onHomeButton)
        #
        # Keyboard ShortCut Button
        #
        self.shortcutButton = qt.QPushButton("Activate Keyboard Shortcuts")
        self.shortcutButton.toolTip = "Activate arrow key movement shortcuts."
        self.shortcutButton.enabled = True
        PrinterControlFormLayout.addRow(self.shortcutButton)
        self.shortcutButton.connect('clicked(bool)', self.onActivateKeyboardShortcuts)
        #
        # IGT Link Connector
        #
        self.inputSelector = slicer.qMRMLNodeComboBox()
        self.inputSelector.nodeTypes = ["vtkMRMLIGTLConnectorNode"]
        self.inputSelector.selectNodeUponCreation = False
        self.inputSelector.addEnabled = False
        self.inputSelector.removeEnabled = False
        self.inputSelector.noneEnabled = False
        self.inputSelector.showHidden = False
        self.inputSelector.showChildNodeTypes = False
        self.inputSelector.setMRMLScene(slicer.mrmlScene)
        self.inputSelector.setToolTip("Connect to OpenIGTLink to control printer from module.")
        PrinterControlFormLayout.addRow("Connect to: ", self.inputSelector)
        #
        # Wavelength Selector
        #
        self.laserSelector = qt.QComboBox()
        self.laserSelector.insertItem(1, "UV: 395 nm ")
        self.laserSelector.insertItem(2, "RED: 660 nm")
        PrinterControlFormLayout.addRow("Laser Wavelength :", self.laserSelector)
        #
        # Output Array Selector
        #
        self.outputArraySelector = slicer.qMRMLNodeComboBox()
        self.outputArraySelector.nodeTypes = (("vtkMRMLDoubleArrayNode"), "")
        self.outputArraySelector.addEnabled = True
        self.outputArraySelector.removeEnabled = True
        self.outputArraySelector.noneEnabled = False
        self.outputArraySelector.showHidden = False
        self.outputArraySelector.showChildNodeTypes = False
        self.outputArraySelector.setMRMLScene(slicer.mrmlScene)
        self.outputArraySelector.setToolTip("Pick the output array for spectrum analysis.")
        PrinterControlFormLayout.addRow("Output spectrum array: ", self.outputArraySelector)
        #
        # X Resolution
        #
        self.xResolution_spinbox = qt.QSpinBox()
        self.xResolution_spinbox.setMinimum(2)
        self.xResolution_spinbox.setMaximum(120)
        self.xResolution_spinbox.setValue(10)
        PrinterControlFormLayout.addRow("X resolution (mm / step) :", self.xResolution_spinbox)
        #
        # Y Resolution
        #
        self.yResolution_spinbox = qt.QSpinBox()
        self.yResolution_spinbox.setMinimum(2)
        self.yResolution_spinbox.setMaximum(120)
        self.yResolution_spinbox.setValue(10)
        PrinterControlFormLayout.addRow("Y resolution (mm/ step):", self.yResolution_spinbox)
        #
        # Time per Reading
        #
        self.timeDelay_spinbox = qt.QSpinBox()
        self.timeDelay_spinbox.setMinimum(0)
        self.timeDelay_spinbox.setMaximum(5000)
        self.timeDelay_spinbox.setValue(1000)
        # self.timeDelay_spinbox.setSingleStep(1000)
        PrinterControlFormLayout.addRow("Time for data delay (ms) :", self.timeDelay_spinbox)
        #
        # Fiducial Placement on/ off
        #
        self.fiducialMarkerCheckBox = qt.QCheckBox()
        self.fiducialMarkerCheckBox.checked = 0
        PrinterControlFormLayout.addRow("Fiducial Marking Off:" ,self.fiducialMarkerCheckBox)
        self.fiducialMarkerCheckBox.connect('stateChanged(int)', self.onFiducialMarkerChecked)
        #
        # UV Threshold Bar
        #
        self.UVthresholdBar = ctk.ctkSliderWidget()
        self.UVthresholdBar.singleStep = 0.1
        self.UVthresholdBar.minimum = 0
        self.UVthresholdBar.maximum = 1
        self.UVthresholdBar.value = 0.5
        PrinterControlFormLayout.addRow(" UV Intensity at 530 nm wavelength: ", self.UVthresholdBar)
        #
        # Learn Spectra Button
        #
        self.learnSpectraButton = qt.QPushButton("Learn Spectra (necessary for 660 nm wavelength)")
        self.learnSpectraButton.toolTip = "Move over spectra of interest to collect reference."
        self.learnSpectraButton.enabled = True
        PrinterControlFormLayout.addRow(self.learnSpectraButton)
        self.learnSpectraButton.connect('clicked(bool)', self.onLearnSpectraButton)
        #
        # Surface Scan Button
        #
        self.scanButton = qt.QPushButton("GO")
        self.scanButton.toolTip = "Begin systematic surface scan"
        self.scanButton.enabled = True
        PrinterControlFormLayout.addRow(self.scanButton)
        self.scanButton.connect('clicked(bool)', self.onScanButton)
        self.scanButton.setStyleSheet("background-color: green; font: bold")
        #
        # Stop Button
        #
        self.stopButton = qt.QPushButton("STOP")
        self.stopButton.toolTip = "Requires restart (slicer and printer)."
        self.stopButton.enabled = True
        PrinterControlFormLayout.addRow(self.stopButton)
        self.stopButton.connect('clicked(bool)', self.onStopButton)
        self.stopButton.setStyleSheet("background-color: red; font: bold")
        #
        # Edge Tracing Button
        #
        self.createModelButton = qt.QPushButton("Trace Contour (after systematic scan)")
        self.createModelButton.toolTip = "Outline the image."
        self.createModelButton.enabled = True
        ContourTracingFormLayout.addRow(self.createModelButton)
        self.createModelButton.connect('clicked(bool)', self.onFindConvexHull)
        #
        # Testing Button
        #
        self.testButton = qt.QPushButton("Find Edge")
        self.testButton.toolTip = "Move to the edge of the area of interest."
        self.testButton.enabled = True
        ContourTracingFormLayout.addRow(self.testButton)
        self.testButton.connect('clicked(bool)', self.onFindEdge)
        #
        # Independent Contour Trace Button
        #
        self.independentEdgeTraceButton = qt.QPushButton("Trace Contour (after edge found, without systematic scan)")
        self.independentEdgeTraceButton.toolTip = "Independent contour tracing using a root finding algorithm."
        self.independentEdgeTraceButton.enabled = True
        ContourTracingFormLayout.addRow(self.independentEdgeTraceButton)
        self.independentEdgeTraceButton.connect('clicked(bool)', self.onIndependentContourTrace)
        #
        # Place Fiducials
        #
        self.placeFiducialsButton = qt.QPushButton("Place Fiducial")
        self.placeFiducialsButton.toolTip = "Place fiducials around ROI"
        self.placeFiducialsButton.enabled = True
        ImageRegistrationFormLayout.addRow(self.placeFiducialsButton)
        self.placeFiducialsButton.connect('clicked(bool)', self.onPlaceFiducials)
        #
        #Follow Fiducials Button
        #
        #self.followFiducialButton = qt.QPushButton("Follow Fiducial")
        #self.followFiducialButton.toolTip = " Oscillate about selected fiducials for 10 rotations."
        #self.followFiducialButton.enabled = True
        #ImageRegistrationFormLayout.addRow(self.followFiducialButton)
        #self.followFiducialButton.connect('clicked(bool)', self.followFiducials)
        #
        # ICP registration stuff
        #
        self.ICPregirstrationButton = qt.QPushButton("ICP Registration")
        self.ICPregirstrationButton.enabled = True
        ImageRegistrationFormLayout.addRow(self.ICPregirstrationButton)
        self.ICPregirstrationButton.connect('clicked(bool)', self.onICPregistration)
        # Center of Mass Button
        #
        self.COMButton = qt.QPushButton("Center of Mass")
        self.COMButton.toolTip = " Calculate and move to the center of mass of a ROI indicated by fiducials"
        self.COMButton.enabled = True
        ImageRegistrationFormLayout.addRow(self.COMButton)
        self.COMButton.connect('clicked(bool)', self.goToCenterOfMass)
        #
        # ROI Systematic Search Button
        #
        self.ROIsearchButton = qt.QPushButton("ROI Systematic Search")
        self.ROIsearchButton.toolTip = " "
        self.ROIsearchButton.enabled = True
        ImageRegistrationFormLayout.addRow(self.ROIsearchButton)
        self.ROIsearchButton.connect('clicked(bool)', self.ROIsearch)
        self.ROIsearchButton.setStyleSheet("background-color: green")


        self.layout.addStretch(1)

    def cleanup(self):
        pass

    def onHomeButton(self, SerialIGTLNode):
        self.onSerialIGLTSelectorChanged()
        self.logic.home()

    def onActivateKeyboardShortcuts(self):
        self.logic.declareShortcut(serialIGTLNode=self.inputSelector.currentNode())
        print "Shortcuts activated."

    # update SerialIGTL Node and double array Node to accomodate changes in the printer and spectra
    def onSerialIGLTSelectorChanged(self):
        self.logic.setSerialIGTLNode(serialIGTLNode=self.inputSelector.currentNode())
        pass  # call self.logic.setSerial...(new value of selector)

    def ondoubleArrayNodeChanged(self):
        self.logic.setdoubleArrayNode(doubleArrayNode=self.inputSelector.currentNode())
        pass

    def onLearnSpectraButton(self):
        self.ondoubleArrayNodeChanged()
        self.onSerialIGLTSelectorChanged()
        self.logic.getSpectralData(self.outputArraySelector.currentNode())

    def onFiducialMarkerChecked(self):
        self.logic.fiducialMarkerChecked()

    def onScanButton(self):
        # TODO: fix bugs at low / high resolution!!
        # 1 by 1 resolution breaks it for some reason
        self.onSerialIGLTSelectorChanged()
        # systematic movement
        self.timeValue = self.timeDelay_spinbox.value
        xResolution = self.xResolution_spinbox.value
        yResolution = self.yResolution_spinbox.value
        self.logic.xLoop(self.timeValue, xResolution,yResolution)  # calls a loop to toggle printer back and forth in the x direction
        self.logic.yLoop(self.timeValue, yResolution, xResolution)  # calls a loop to increment the printer back in the y direction

        # tissue analysis
        self.tumorTimer = qt.QTimer()
        self.iterationTimingValue = 0

        stopsToVisitX = 120 / xResolution
        stopsToVisitY = 120 / yResolution
        for self.iterationTimingValue in xrange(0, (stopsToVisitX * stopsToVisitY * self.timeValue) + (10*self.timeValue), self.timeValue):
            self.tumorTimer.singleShot(self.iterationTimingValue, lambda: self.tissueDecision())
            self.iterationTimingValue = self.iterationTimingValue + self.timeValue

    def tissueDecision(self):
        self.ondoubleArrayNodeChanged()
        self.onSerialIGLTSelectorChanged()
        UVthreshold = self.UVthresholdBar.value
        print UVthreshold
        # places a fiducial in the correct coordinate if tissue decision returns the same spectra as the reference spectra
        # Note: for UV the spectrum comparison does not compare the average differences, instead the intensity at a particular wavelength
        if (self.laserSelector.currentIndex) == 0 :
         if self.logic.spectrumComparisonUV(self.outputArraySelector.currentNode(), UVthreshold ) == False:  # add a fiducial if the the tumor detecting function returns false
            self.logic.get_coordinates()
        elif (self.laserSelector.currentIndex) == 1:
          if self.logic.spectrumComparison(self.outputArraySelector.currentNode()) == False:  # add a fiducial if the the tumor detecting function returns false
            self.logic.get_coordinates()
        else:
            return

    def onStopButton(self):
        self.onSerialIGLTSelectorChanged()
        self.logic.emergencyStop()
        # Note: the stop command uses G-code command M112 which requires slicer reboot and printer reboot after each usage.
    # Outline area of interest following systematic scan
    def onFindConvexHull(self):
         self.logic.convexHull()
    # Use to find the edge of the area of interest before independent edge tracing
    def onFindEdge(self):
        self.ondoubleArrayNodeChanged()
        self.onSerialIGLTSelectorChanged()
        self.logic.findAndMoveToEdge(self.outputArraySelector.currentNode())

    def onIndependentContourTrace(self):
        self.ondoubleArrayNodeChanged()
        self.onSerialIGLTSelectorChanged()
        self.logic.edgeTrace(self.outputArraySelector.currentNode())
    # oscillate between fiducials, updated with fiducial movement or addition
    def onPlaceFiducials(self):
        self.ondoubleArrayNodeChanged()
        self.onSerialIGLTSelectorChanged()
        self.logic.getLandmarkFiducialsCoordinate()

    def followFiducials(self):
        self.ondoubleArrayNodeChanged()
        self.onSerialIGLTSelectorChanged()
        self.logic.callFollowFiducials()
    # find the center of mass of a group of fiducials and move to it
    def goToCenterOfMass(self):
        self.ondoubleArrayNodeChanged()
        self.onSerialIGLTSelectorChanged()
        self.logic.findCenterOfMassOfFiducials()

    # TODO: fix delays
    def ROIsearch(self):
        self.ondoubleArrayNodeChanged()
        self.onSerialIGLTSelectorChanged()
        self.timeValue = self.timeDelay_spinbox.value
        xResolution = self.xResolution_spinbox.value
        yResolution = self.yResolution_spinbox.value
        xMin, xMax, yMin, yMax = self.logic.ROIsystematicSearch()
        self.logic.yMovement(0, yMin)
        self.logic.XMovement(0, xMin)
        self.logic.ROIsearchXLoop(self.timeValue, xResolution,yResolution, xMin, xMax)  # calls a loop to toggle printer back and forth in the x direction
        self.logic.ROIsearchYLoop(self.timeValue, yResolution, xResolution, yMin, yMax, xMin, xMax)  # calls a loop to increment the printer back in the y direction

        self.tumorTimer = qt.QTimer()
        self.iterationTimingValue = 0
        stopsToVisitX = (xMax - xMin) / xResolution
        stopsToVisitY = (yMax - yMin) / yResolution
        for self.iterationTimingValue in range(0, (stopsToVisitX * stopsToVisitY * self.timeValue) + 10 * self.timeValue,self.timeValue):
            self.tumorTimer.singleShot(self.iterationTimingValue, lambda: self.tissueDecision())
            self.iterationTimingValue = self.iterationTimingValue + self.timeValue


    def test(self):
        self.ondoubleArrayNodeChanged()
        self.onSerialIGLTSelectorChanged()
        xVal = self.xResolution_spinbox.value
        self.logic.controlledXMovement(xVal)

    def onICPregistration(self):
        self.logic.ICPRegistration()
#
# PrinterInteractorLogic
#

class PrinterInteractorLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
    # arrays for convex Hull
    _yHullArray = []
    _xHullArray = []
    # arrays for edge tracing
    _saveycoordinate = []
    _savexcoordinate = []
    # arrays for quadrant check (independent edge tracing)
    _tumorCheck = []
    # ROI boundary arrays
    _ROIxbounds = []
    _ROIybounds = []

    def __init__(self):
        # general instantiations
        self.serialIGTLNode = None
        self.doubleArrayNode = None
        self.spectrumImageNode = None
        self.observerTags = []
        self.outputArrayNode = None

        self.numberOfDataPoints = 100
        self.firstDataPointGenerated = 0
        self.spectraCollectedflag = 0
        self.fiducialIndex = 0
        self.fiducialIndex2 = 0
        self.averageSpectrumDifferences = 0
        self.fiducialMovementDelay = 0
        self.currentXcoordinate = 0
        self.currentYcoordinate = 0
        self.addedEdge = 0
        self.firstComparison = 0
        self.createTumorArray = 0
        self.startNext = 6000
        self.timerTracker = 0

        #polydata definitions
        self.referenceSpectra = vtk.vtkPolyData() 
        self.spectra = vtk.vtkPoints()
        self.pointsForHull = vtk.vtkPoints()
        self.currentSpectrum = vtk.vtkPoints()

        # coordinate class declaration
        self.xcoordinate = 0
        self.ycoordinate = 0
        self.zcoordinate = 0

        # independent edge tracing variables
        self.pointsForEdgeTracing = vtk.vtkPoints()
        self.edgeTracingTimerStart = 2000

       # instantiate coordinate values
        self.getCoordinateCmd = slicer.vtkSlicerOpenIGTLinkCommand()
        self.getCoordinateCmd.SetCommandName('SendText')
        self.getCoordinateCmd.SetCommandAttribute('DeviceId', "SerialDevice")
        self.getCoordinateCmd.SetCommandTimeoutSec(1.0)
        self.getCoordinateCmd.SetCommandAttribute('Text', 'M114')
        self.getCoordinateCmd.AddObserver(self.getCoordinateCmd.CommandCompletedEvent, self.onPrinterCommandCompleted)
        # instantiate landmark coordinate command
        self.landmarkCoordinateCmd = slicer.vtkSlicerOpenIGTLinkCommand()
        self.landmarkCoordinateCmd.SetCommandName('SendText')
        self.landmarkCoordinateCmd.SetCommandAttribute('DeviceId', "SerialDevice")
        self.landmarkCoordinateCmd.SetCommandTimeoutSec(1.0)
        self.landmarkCoordinateCmd.SetCommandAttribute('Text', 'M114')
        self.landmarkCoordinateCmd.AddObserver(self.getCoordinateCmd.CommandCompletedEvent, self.onLandmarkCoordinateCmd)
        # instantiate home command
        self.homeCmd = slicer.vtkSlicerOpenIGTLinkCommand()
        self.homeCmd.SetCommandName('SendText')
        self.homeCmd.SetCommandAttribute('DeviceId', "SerialDevice")
        self.homeCmd.SetCommandTimeoutSec(1.0)
        self.homeCmd.SetCommandAttribute('Text', 'G28 X Y ')
        # instantiate emergency stop command
        self.emergStopCmd = slicer.vtkSlicerOpenIGTLinkCommand()
        self.emergStopCmd.SetCommandName('SendText')
        self.emergStopCmd.SetCommandAttribute('DeviceId', "SerialDevice")
        self.emergStopCmd.SetCommandTimeoutSec(1.0)
        self.emergStopCmd.SetCommandAttribute('Text', 'M112')
        # instantiate x command
        self.xControlCmd = slicer.vtkSlicerOpenIGTLinkCommand()
        self.xControlCmd.SetCommandName('SendText')
        self.xControlCmd.SetCommandAttribute('DeviceId', "SerialDevice")
        self.xControlCmd.SetCommandTimeoutSec(1.0)
        # instantiate y command
        self.yControlCmd = slicer.vtkSlicerOpenIGTLinkCommand()
        self.yControlCmd.SetCommandName('SendText')
        self.yControlCmd.SetCommandAttribute('DeviceId', "SerialDevice")
        self.yControlCmd.SetCommandTimeoutSec(1.0)
        # instantiate move middle command
        self.printerControlCmd = slicer.vtkSlicerOpenIGTLinkCommand()
        self.printerControlCmd.SetCommandName('SendText')
        self.printerControlCmd.SetCommandAttribute('DeviceId', "SerialDevice")
        self.printerControlCmd.SetCommandTimeoutSec(1.0)
        # instantiate move X and Y command
        self.xyControlCmd = slicer.vtkSlicerOpenIGTLinkCommand()
        self.xyControlCmd.SetCommandName('SendText')
        self.xyControlCmd.SetCommandAttribute('DeviceId', "SerialDevice")
        self.xyControlCmd.SetCommandTimeoutSec(1.0)
        # instantiate move Z command
        self.zControlCmd = slicer.vtkSlicerOpenIGTLinkCommand()
        self.zControlCmd.SetCommandName('SendText')
        self.zControlCmd.SetCommandAttribute('DeviceId', "SerialDevice")
        self.zControlCmd.SetCommandTimeoutSec(1.0)

    def ICPRegistration(self):
        ICPregistration = vtk.vtkIterativeClosestPointTransform()
        ICPregistration.SetMaximumNumberOfLandmarks(10)


     # necessary to have this in a function activated by Active keyboard short cut function so that the movements can be instantiated after IGTL has already been instantiated.
    def declareShortcut(self, serialIGTLNode):
        self.installShortcutKeys(serialIGTLNode)

    def installShortcutKeys(self, serialIGTLNode):
        """Turn on editor-wide shortcuts.  These are active independent
        of the currently selected effect."""

          # not in PythonQt
        self.shortcuts = []
        keysAndCallbacks = (
            ('Right', lambda: self.keyboardControlledXMovementForward(serialIGTLNode)),
            ('Left', lambda: self.keyboardControlledXMovementBackwards(serialIGTLNode)),
            ('Up', lambda: self.keyboardControlledYMovementForward(serialIGTLNode)),
            ('Down', lambda: self.keyboardControlledYMovementBackwards(serialIGTLNode)),
            ( 'H', lambda: self.keyboardControlledHomeMovement(serialIGTLNode)),
              )

        for key, callback in keysAndCallbacks:
            shortcut = qt.QShortcut(slicer.util.mainWindow())
            shortcut.setKey(qt.QKeySequence(key))
            shortcut.connect('activated()', callback)
            self.shortcuts.append(shortcut)


    def setSerialIGTLNode(self, serialIGTLNode):
        self.serialIGTLNode = serialIGTLNode

    def setdoubleArrayNode(self, doubleArrayNode):
        self.doubleArrayNode = doubleArrayNode

    def addObservers(self):
        if self.spectrumImageNode:
            print "Add observer to {0}".format(self.spectrumImageNode.GetName())
            self.observerTags.append([self.spectrumImageNode, self.spectrumImageNode.AddObserver(vtk.vtkCommand.ModifiedEvent,self.onSpectrumImageNodeModified)])

    def removeObservers(self):
        print "Remove observers"
        for nodeTagPair in self.observerTags:
            nodeTagPair[0].RemoveObserver(nodeTagPair[1])

    def onSpectrumImageNodeModified(self, observer, eventid):

        if not self.spectrumImageNode or not self.outputArrayNode:
            return

        self.updateOutputArray()
        self.updateChart()

    def updateOutputArray(self, node):
        self.spectrumImageNode = node
        numberOfPoints = self.spectrumImageNode.GetImageData().GetDimensions()[0]
        numberOfRows = self.spectrumImageNode.GetImageData().GetDimensions()[1]
        if numberOfRows != 2:
            logging.error("Spectrum image is expected to have exactly 2 rows, got {0}".format(numberOfRows))
            return

        # Create arrays of data
        a = self.outputArrayNode.GetArray()
        a.SetNumberOfTuples(self.numberOfDataPoints)

        for row in xrange(numberOfRows):
            lineSource = vtk.vtkLineSource()
            lineSource.SetPoint1(0, row, 0)
            lineSource.SetPoint2(numberOfPoints - 1, row, 0)
            lineSource.SetResolution(self.numberOfDataPoints - 1)
            probeFilter = vtk.vtkProbeFilter()
            probeFilter.SetInputConnection(lineSource.GetOutputPort())
            if vtk.VTK_MAJOR_VERSION <= 5:
                probeFilter.SetSource(self.spectrumImageNode.GetImageData())
            else:
                probeFilter.SetSourceData(self.spectrumImageNode.GetImageData())
            probeFilter.Update()
            probedPoints = probeFilter.GetOutput()
            probedPointScalars = probedPoints.GetPointData().GetScalars()
            for i in xrange(self.numberOfDataPoints):
                a.SetComponent(i, row, probedPointScalars.GetTuple(i)[0])

        for i in xrange(self.numberOfDataPoints):
            a.SetComponent(i, 2, 0)

        probedPoints.GetPointData().GetScalars().Modified()

    # collect spectra for reference and comparison
    def getSpectralData(self, outputArrayNode):
        self.referenceOutputArrayNode = outputArrayNode
        referencePointsArray = self.referenceOutputArrayNode.GetArray()

        self.spectra.SetNumberOfPoints(100)
        for i in xrange(0, 101, 1):
            self.spectra.SetPoint(i, referencePointsArray.GetTuple(i))

        self.spectraCollectedflag = 1
        print"Spectra collected."

    def setTumorBoundaries(self):
        self.referenceSpectra = vtk.vtkPolyData()
        self.referenceSpectra.SetPoints(self.spectra)
        print "Boundaries set."
        # 10 specifies coordinates to be float values


     # used for spectrum acquisition where there is a distinctive different between the spectra of the material of interest and surrounding material
    def spectrumComparison(self, outputArrayNode):

        if self.spectraCollectedflag == 0:
            print " Error: reference spectrum not collected."
            return

        self.currentOutputArrayNode = outputArrayNode
        currentPointsArray = self.currentOutputArrayNode.GetArray()

        self.currentSpectrum.SetNumberOfPoints(100)
        for i in xrange(0, 101, 1):
            self.currentSpectrum.SetPoint(i, currentPointsArray.GetTuple(i))

        self.averageSpectrumDifferences = 0

        for j in xrange(0, 101, 1):
            x = self.currentSpectrum.GetPoint(j)
            y = self.spectra.GetPoint(j)
            self.averageSpectrumDifferences = self.averageSpectrumDifferences + (y[1] - x[1])

        #useful for debugging purposed
        #print self.averageSpectrumDifferences

        if abs(self.averageSpectrumDifferences) <9 : # < 7 for white and black
            print " tumor"
            if self.firstComparison == 1:
                self.get_coordinates()
            if self.createTumorArray == 1:
                self._tumorCheck.append(1)
            return False
        else:
            print "healthy"
            if self.createTumorArray == 1:
                self._tumorCheck.append(0)
            return True

        # used with UV laser to distinguish between spectrums that vary in intensity by a small amount at a specific wavelength / data point
    def spectrumComparisonUV(self, outputArrayNode, UVthreshold):

        self.outputArrayNode = outputArrayNode
        pointsArray = self.outputArrayNode.GetArray()
            # point contains a wavelength and a corresponding intensity
            # each data point has 2 rows of data, one corresponding to wavelength and one corresponding to intensity
        self.componentIndexWavelength = 0
        self.componentIndexIntensity = 1
            # Data is acquired from probe in a double array with each index corresponding to either wavelength or intensity
            # There are 100 points (tuples) each consisting of one wavelength and a corresponding intensity
            # The first index (0) is where wavelength values are stored
            # The second index (1) is where intensities are stored
            # test lines that could be useful eventually
            # numberOfPoints = pointsArray.GetNumberOfTuples() #access the number of points received from the spectra
            # for pointIndex in xrange(numberOfPoints): #could potentially loop to check a certain range of data points
            # wavelengthValue = pointsArray.GetComponent(63,0) #checks the 187th point in the data stream
            # intensityValue = pointsArray.GetComponent(62, 1)

        #wavelengthCheck = pointsArray.GetComponent(26,0) # use to varify which wavelength the tumor Check intensity corresponds to
        tumorCheck = pointsArray.GetComponent(26,1)# check the 395th wavelength to determine if it sees the invisible ink or not

        if tumorCheck < UVthreshold: #threshold is variable using the slider widget on the GUI, useful because intensity difference is inconsistent
            print "tumor"
            return False
        else:
            print "healthy"
            return True

    def get_coordinates(self):
        slicer.modules.openigtlinkremote.logic().SendCommand(self.getCoordinateCmd, self.serialIGTLNode.GetID())

    def onPrinterCommandCompleted(self, observer, eventid):
        coordinateValues = self.getCoordinateCmd.GetResponseMessage()
        print("Command completed with status: " + self.getCoordinateCmd.StatusToString(self.getCoordinateCmd.GetStatus()))
        print("Response message: " + coordinateValues)
        print("Full response: " + self.getCoordinateCmd.GetResponseText())
        # parsing the string for specific coordinate values
        mylist = coordinateValues.split(" ")

        # Parse string for x coordinate value
        xvalues = mylist[0].split(":")
        self.xcoordinate = float(xvalues[1])

        # Parse string for y coordinate value
        yvalues = mylist[1].split(":")
        self.ycoordinate = float(yvalues[1])

        # Parse string for z coordinate value
        zvalues = mylist[2].split(":")
        self.zcoordinate = float(zvalues[1])

        # added for automated edge tracing
        if self.addedEdge == 0:
            self._savexcoordinate.append(self.xcoordinate)
            self._saveycoordinate.append(self.ycoordinate)
            self.addedEdge = 1

        self.dataCollection = self.createPolyDataPoint(self.xcoordinate, self.ycoordinate, self.zcoordinate)

        if self.fiducialIndex < 1:
            self.fiducialMarker(self.xcoordinate, self.ycoordinate, self.zcoordinate)
            self.fiducialIndex = self.fiducialIndex + 1
        elif self.fiducialIndex == 1234:
            return self.xcoordinate
        else:
            self.addToCurrentFiducialNode(self.xcoordinate, self.ycoordinate, self.zcoordinate)

        return self.xcoordinate

    def getLandmarkFiducialsCoordinate(self):
        slicer.modules.openigtlinkremote.logic().SendCommand(self.getCoordinateCmd, self.serialIGTLNode.GetID())

    def onLandmarkCoordinateCmd(self, observer, eventid):
        coordinateValues = self.getCoordinateCmd.GetResponseMessage()
        print("Command completed with status: " + self.getCoordinateCmd.StatusToString(
            self.getCoordinateCmd.GetStatus()))
        print("Response message: " + coordinateValues)
        print("Full response: " + self.getCoordinateCmd.GetResponseText())
        # parsing the string for specific coordinate values
        mylist = coordinateValues.split(" ")

        # Parse string for x coordinate value
        xvalues = mylist[0].split(":")
        self.xcoordinate = float(xvalues[1])

        # Parse string for y coordinate value
        yvalues = mylist[1].split(":")
        self.ycoordinate = float(yvalues[1])

        # Parse string for z coordinate value
        zvalues = mylist[2].split(":")
        self.zcoordinate = float(zvalues[1])


        if self.fiducialIndex2 < 1:
            self.landmarkFiducialMarker(self.xcoordinate, self.ycoordinate, self.zcoordinate)
            self.fiducialIndex2 = self.fiducialIndex2 + 1
        elif self.fiducialIndex == 1234:
            return self.xcoordinate
        else:
            self.addToLandmarkFiducialNode(self.xcoordinate, self.ycoordinate, self.zcoordinate)

    def landmarkFiducialMarker(self, xcoordinate, ycoordinate, zcoordinate):
        self.fiducialNode1 = slicer.vtkMRMLMarkupsFiducialNode()
        slicer.mrmlScene.AddNode(self.fiducialNode1)
        self.fiducialNode1.AddFiducial(xcoordinate, ycoordinate, zcoordinate)

    def addToLandmarkFiducialNode(self, xcoordinate, ycoordinate, zcoordinate):
        self.fiducialNode1.AddFiducial(xcoordinate, ycoordinate, zcoordinate)
        self.fiducialIndex = self.fiducialIndex + 1

    def fiducialMarkerChecked(self):
        self.fiducialIndex = 1234 # will break if 1234 fiducials is ever reached

    def fiducialMarker(self, xcoordinate, ycoordinate, zcoordinate):
        self.fiducialNode = slicer.vtkMRMLMarkupsFiducialNode()
        slicer.mrmlScene.AddNode(self.fiducialNode)
        self.fiducialNode.AddFiducial(xcoordinate, ycoordinate, zcoordinate)

    def addToCurrentFiducialNode(self, xcoordinate, ycoordinate, zcoordinate):
        self.fiducialNode.AddFiducial(xcoordinate, ycoordinate, zcoordinate)
        self.fiducialIndex = self.fiducialIndex + 1
        print(self.fiducialIndex)

    # independent edge tracing: the following code was developed using a series of qt single shot timers and a root searching algorithm 
    # to determine the approximate boundaries of an image without a systematic search. 
    
    def edgeTrace(self, outputArrayNode):

        for i in xrange(0,400000,9000):
            self.callQuadrantCheck(i, outputArrayNode) # checks which region to continue in
            self.callGetCoordinates(i+5500) #determines the coordinates of the edge point, places a fiducial there
            self.callNewOrigin(i+7000)

    def callNewOrigin(self, delay):
        originTimer = qt.QTimer()
        originTimer.singleShot(delay, lambda: self.newOrigin())

    def callQuadrantCheck(self, delay, outputArrayNode):
        quadTimer = qt.QTimer()
        quadTimer.singleShot(delay, lambda: self.checkQuadrantValues(outputArrayNode))

    def callPrintFunc(self,delay):
        self.edgeTraceTimer.singleShot(delay, lambda: self.printFunc())

    def callMovement(self,delay,xcoordinate,ycoordinate):
        self.cutInTimer = qt.QTimer()
        self.cutInTimer.singleShot(delay, lambda: self.controlledXYMovement(xcoordinate, ycoordinate))

    def callGetCoordinates(self, delay):
        coordTimer = qt.QTimer()
        coordTimer.singleShot(delay, lambda: self.get_coordinates())

    def call_getCoordinates(self, delay):
        self.edgeTraceTimer.singleShot(delay, lambda: self.get_coordinates())

    def findAndMoveToEdge(self, outputArrayNode):
        self.cutInTimer = qt.QTimer()
        self.edgeTraceTimer = qt.QTimer()
        # move forward until reference spectra is observed then return to that spot
        for y in xrange(0,62,2):
            delayMs = ((y/2)*500) + 500
            self.callMovement(delayMs,y,y)
        for x in xrange(0,15500, 500):
            self.readCoordinatesAtTimeInterval(x, outputArrayNode)
        self.moveBackToOriginalEdgePoint()

    def checkQuadrantValues(self, outputArrayNode):
        # go right, back, left, forward until you determine which quadrant to continue in
        self.printTimer = qt.QTimer()
        index = len(self._savexcoordinate) - 1
        print(self._savexcoordinate)
        print(index)
        self.callMovement(1000, (self._savexcoordinate[index] + 10), (self._saveycoordinate[index])) # right 10
        self.readCoordinatesAtTimeInterval2(2000,outputArrayNode)

        self.callMovement(2000, (self._savexcoordinate[index]), (self._saveycoordinate[index] - 10)) # back 10
        self.readCoordinatesAtTimeInterval2(3000, outputArrayNode)

        self.callMovement(3000, (self._savexcoordinate[index] - 10), (self._saveycoordinate[index])) # left 10
        self.readCoordinatesAtTimeInterval2(4000, outputArrayNode)

        self.callMovement(4000, (self._savexcoordinate[index]), (self._saveycoordinate[index] + 10)) # forward 10
        self.readCoordinatesAtTimeInterval2(5000, outputArrayNode)

        self.callMovement(5000, (self._savexcoordinate[index]), (self._saveycoordinate[index])) # back to center

        self.callPrintFunc(7000)
        self.startTrajectorySearch(outputArrayNode)
        self.timerTracker = self.timerTracker + 6000

    def printFunc(self):
        print(self._tumorCheck) # useful for debugging purposes

    def readCoordinatesAtTimeInterval(self, delay, outputArrayNode):
        self.firstComparison = 1
        self.edgeTraceTimer.singleShot(delay, lambda: self.spectrumComparison(outputArrayNode))

    def readCoordinatesAtTimeInterval2(self, delay, outputArrayNode):
        self.createTumorArray = 1
        self.edgeTraceTimer.singleShot(delay, lambda: self.spectrumComparison(outputArrayNode))

    def readCoordinatesAtTimeInterval3(self, delay, outputArrayNode):
        self.edgeTraceTimer.singleShot(delay, lambda: self.spectrumComparison(outputArrayNode)) # only difference was spectrum comparision 3 had < 7 rather than 9

    def moveBackToOriginalEdgePoint(self):
        x = len(self._savexcoordinate) - 1
        self.edgeTraceTimer.singleShot(16500, lambda: self.controlledXYMovement(self._savexcoordinate[x], self._saveycoordinate[x]))

    def findTrajectory(self, outputArrayNode):
        self.trajectoryTimer = qt.QTimer()
        index = len(self._tumorCheck)
        y = len(self._savexcoordinate) - 1

        if (self._tumorCheck[index - 4] ==1 and self._tumorCheck[index -3 ] == 0 and self._tumorCheck[index - 2] == 0 and self._tumorCheck[index -1 ] ==1) or ((self._tumorCheck[index - 4] == 0 and self._tumorCheck[index - 3] == 0 and self._tumorCheck[index - 2] == 0 and self._tumorCheck[index - 1] == 1)):
            print "Quadrant 2"
            self.callMovement(0,self._savexcoordinate[y] -4, self._saveycoordinate[y] + 6)

        if (self._tumorCheck[index - 4] == 1 and self._tumorCheck[index - 3] == 1 and self._tumorCheck[index - 2] == 0 and self._tumorCheck[index - 1] == 0) or (self._tumorCheck[index - 4] == 1 and self._tumorCheck[index - 3] == 0 and self._tumorCheck[index - 2] == 0 and self._tumorCheck[index - 1] == 0) or ((self._tumorCheck[index - 4] == 1 and self._tumorCheck[index - 3] == 1 and self._tumorCheck[index - 2] == 1 and self._tumorCheck[index - 1] == 0))  or ((self._tumorCheck[index - 4] == 1 and self._tumorCheck[index - 3] == 1 and self._tumorCheck[index - 2] == 1 and self._tumorCheck[index - 1] == 1)):
            print "Quadrant 1"
            self.callMovement(0, self._savexcoordinate[y] + 4, self._saveycoordinate[y] + 6)


        if (self._tumorCheck[index - 4] == 0 and self._tumorCheck[index - 3] == 0 and self._tumorCheck[index - 2] == 1 and self._tumorCheck[index - 1] == 1) or (self._tumorCheck[index - 4] == 0 and self._tumorCheck[index - 3] == 0 and self._tumorCheck[index - 2] == 1 and self._tumorCheck[index - 1] == 0) or ((self._tumorCheck[index - 4] == 1 and self._tumorCheck[index - 3] == 1 and self._tumorCheck[index - 2] == 1 and self._tumorCheck[index - 1] == 1)) or ((self._tumorCheck[index - 4] == 1 and self._tumorCheck[index - 3] == 0 and self._tumorCheck[index - 2] == 1 and self._tumorCheck[index - 1] == 1)):
            print "Quadrant 3"
            self.callMovement(0, self._savexcoordinate[y] - 4, self._saveycoordinate[y] - 6)


        if (self._tumorCheck[index - 4] == 0 and self._tumorCheck[index - 3] == 1 and self._tumorCheck[index - 2] == 1 and self._tumorCheck[index - 1] == 0) or (self._tumorCheck[index - 4] == 0 and self._tumorCheck[index - 3] == 1 and self._tumorCheck[index - 2] == 0 and self._tumorCheck[index - 1] == 0)or ((self._tumorCheck[index - 4] == 0 and self._tumorCheck[index - 3] == 1 and self._tumorCheck[index - 2] == 1 and self._tumorCheck[index - 1] == 1)):
            print "Quadrant 4"
            self.callMovement(0, self._savexcoordinate[y] + 4, self._saveycoordinate[y] - 6)

        self.addedEdge = 0
        self.call_getCoordinates(self.timerTracker + 1000)

    def newOrigin(self):
        self.addedEdge =0
        self.get_coordinates()
        if self.fiducialIndex < 1:
            self.fiducialMarker(self.xcoordinate, self.ycoordinate, self.zcoordinate)
            self.fiducialIndex = self.fiducialIndex + 1
        else:
             self.addToCurrentFiducialNode(self.xcoordinate, self.ycoordinate, self.zcoordinate)

    def startTrajectorySearch(self,outputArrayNode):
        trajTimer = qt.QTimer()
        trajTimer.singleShot(self.startNext,lambda: self.findTrajectory(outputArrayNode)) # was self.startNext

    # The following code was developed for contour tracing following a systamtic scan by determining the convex hull of a list of collected points
    def createPolyDataPoint(self, xcoordinate, ycoordinate, zcoordinate):
        if self.firstDataPointGenerated < 1:
            self.firstDataPointGenerated = self.firstDataPointGenerated + 1
            self.pointsForHull.InsertNextPoint(xcoordinate, ycoordinate, zcoordinate)
        else:
            self.pointsForHull.InsertNextPoint(xcoordinate, ycoordinate, zcoordinate)

    def convexHull(self):

        self.hullPolydata = vtk.vtkPolyData()
        self.hullPolydata.SetPoints(self.pointsForHull)

        hull = vtk.vtkConvexHull2D()
        hull.SetInputData(self.hullPolydata)
        hull.Update()

        pointLimit = hull.GetOutput().GetNumberOfPoints()
        for i in xrange(0, pointLimit):
            self.pointsForEdgeTracing.InsertNextPoint(hull.GetOutput().GetPoint(i))
        self.getCoordinatesForEdgeTracing(self.pointsForEdgeTracing, pointLimit)

    def getCoordinatesForEdgeTracing(self, pointsForEdgeTracing, pointLimit):

        for i in xrange(0,pointLimit):
            pointVal = pointsForEdgeTracing.GetPoint(i)
            xcoordinate = pointVal[0]
            ycoordinate = pointVal[1]
            self._xHullArray.append(xcoordinate)
            self._yHullArray.append(ycoordinate)
            self.slowEdgeTracing(xcoordinate, ycoordinate, self.edgeTracingTimerStart)

            self.edgeTracingTimerStart = self.edgeTracingTimerStart + 2000
        self.slowEdgeTracing(self._xHullArray[0], self._yHullArray[0], (2000*pointLimit + 2000))
        self.ZMovement(2000, -5) # moves the probe down (useful for actual tracing if probe is replaced by a marker)
        self.ZMovement(2000*pointLimit + 4000, 0) # moves the probe back up after edge tracing is finished 

    # Image Registration functions
    def callFollowFiducials(self):
        fiducialTimer = qt.QTimer()
        for delay in xrange(0,3000,1000):
            fiducialTimer.singleShot(delay, lambda: self.followFiducialCoordinates())
            
    def followFiducialCoordinates(self):
        fidList = slicer.util.getNode('MarkupsFiducial') # was F
        numFids = fidList.GetNumberOfFiducials()

        for i in xrange(numFids):
            ras = [0,0,0]
            pos = fidList.GetNthFiducialPosition(i, ras)
            world = [0,0,0,0]
            fidList.GetNthFiducialWorldCoordinates(0,world)
            self.fiducialMovementDelay= self.fiducialMovementDelay+ 1000
            xcoord = abs(int(ras[0]))
            ycoord = abs(int(ras[1]))
            if xcoord < 120 and ycoord < 120: # maintains that the coordinates stay within the test bed limitations
                self.xyMovement(xcoord, ycoord,self.fiducialMovementDelay)
            # ras is the coordinate of the fiducial
            
    def findCenterOfMassOfFiducials(self):
        fidList = slicer.util.getNode('MarkupsFiducial')
        numFids = fidList.GetNumberOfFiducials()
        centerOfMass = [0,0,0]
        sumPos = np.zeros(3)
        for i in xrange(numFids):
            pos = np.zeros(3)
            fidList.GetNthFiducialPosition(i,pos)
            sumPos += pos
        centerOfMass = sumPos / numFids
        xcoord = centerOfMass[0]
        ycoord = centerOfMass[1]
        self.controlledXYMovement(xcoord,ycoord)

    def ROIsystematicSearch(self):
        fidList = slicer.util.getNode('MarkupsFiducial')
        numFids = fidList.GetNumberOfFiducials()

        for i in xrange(numFids):
            ras = [0, 0, 0]
            pos = fidList.GetNthFiducialPosition(i, ras)
            world = [0, 0, 0, 0]
            fidList.GetNthFiducialWorldCoordinates(0, world)
            xcoord = int(ras[0])
            ycoord = int(ras[1])
            self._ROIxbounds.append(xcoord)
            self._ROIybounds.append(ycoord)
        print(self._ROIxbounds)
        print(self._ROIybounds)
        xMin = min(self._ROIxbounds)
        xMax = max(self._ROIxbounds)
        yMin = min(self._ROIybounds)
        yMax = max(self._ROIybounds)
        return xMin, xMax, yMin, yMax
        # For ROI searching
    def ROIsearchXLoop(self, timeValue, xResolution, yResolution, xMin, xMax):
            # necessary for looping the x commands on static intervals
        oscillatingTime = ((xMax- xMin) / yResolution) / 2  # determines how many times the scanner should oscillate back and forth
        lengthOfOneWidth = (((xMax-xMin) / xResolution) * 2) * timeValue # the amount of movements per oscillation back and forth
        for xCoordinateValue in xrange(xMin, (oscillatingTime * lengthOfOneWidth) + lengthOfOneWidth,lengthOfOneWidth):  # calls forwards and backwards as necessary
            self.ROIsearchXWidthForward(xCoordinateValue, timeValue, xResolution, xMin, xMax)
            self.ROIsearchXWidthBackward(xCoordinateValue, timeValue, xResolution, xMin, xMax)

    def ROIsearchXWidthForward(self, xCoordinate, timeValue, xResolution, xMin, xMax):  # used to be passed xCoordinate
        # Move the width of the bed forward in the positive x direction
        # Corresponds to a timer called in printer interactor widget
        self.scanTimer = qt.QTimer()
        for xValue in xrange(xMin, xMax, xResolution):
            for xValue in xrange(xMin, xMax, xResolution):  # increment by 10 until 120
                delayMs = xCoordinate + xValue * (timeValue / xResolution)  # xCoordinate ensures the clocks are starting at correct times and xValue * (timeValue / 10 ) increments according to delay
                self.XMovement(delayMs, xValue)

    def ROIsearchXWidthBackward(self, xCoordinate, timeValue, xResolution, xMin, xMax):
        # Move the width of the bed backwards in the negative x direction
        # Corresponds to a timer called in printer interactor widget
        self.scanTimer = qt.QTimer()
        for xValue in xrange(xMax, xMin, -xResolution):
            delayMs = abs(xValue -(xMax)) * (timeValue / xResolution) + ((xMax - xMin) / xResolution + 1) * timeValue + xCoordinate  # same principle as xWidth forwards but with abs value to account for decrementing values and 13*time value to offset starting interval
            self.XMovement(delayMs, xValue)

    def ROIsearchYLoop(self, timeValue, yResolution, xResolution, yMin, yMax, xMin, xMax):
        # specific intervals correspond to timeValues divisible by 1000
        # The variances in intervals were timed specifically to account for mechanical delays with the printer

        firstDistance = ((xMax-xMin) / xResolution)
        secondDistance = 2 * ((xMax-xMin) / xResolution)
        self.yMovement((firstDistance + 2) * timeValue, yResolution + yMin)
        self.yMovement((secondDistance + 1) * timeValue, (yResolution * 2)+ yMin )
        self.i = 0
        self.j = 0
        for yValue in xrange(yMin + (yResolution * 3), yMax + yResolution, yResolution * 2):
            delayMs = (((secondDistance + firstDistance)+ 2) * timeValue) + ((secondDistance * timeValue) * (self.i))
            self.yMovement(delayMs, yValue)
            self.i = self.i + 1
            print yValue
        for yValue in xrange(yMin + (yResolution * 4), yMax + yResolution, yResolution * 2):
            delayMs = ((((2 * secondDistance)+ 1)) * timeValue) + ((secondDistance * timeValue) * (self.j))
            self.yMovement(delayMs, yValue)
            print yValue
            self.j = self.j + 1
            
    # General Printer Movement Commands       
    def home(self):
        slicer.modules.openigtlinkremote.logic().SendCommand(self.homeCmd, self.serialIGTLNode.GetID())

    def emergencyStop(self):
        # Writes to the printer to automatically stop all motors
        # Requires reboot
        slicer.modules.openigtlinkremote.logic().SendCommand(self.emergStopCmd, self.serialIGTLNode.GetID())
        self.emergStopCmd.AddObserver(self.emergStopCmd.CommandCompletedEvent, self.onPrinterCommandCompleted)

    def yLoop(self, timeValue, yResolution, xResolution):
       # the following code was developed to execute a y Movement at the beginning and end of successive x oscillations to ensure that the platform
       # is systematically scanned along the y axis as well as the x
        firstDistance = (120 / xResolution) # distance of one x oscillation
        secondDistance = 2 * (120 / xResolution) # distance of two x oscillations
        self.yMovement((firstDistance + 2) * timeValue, yResolution) # call yMovement once the first oscillation in the x direction is finished
        self.yMovement((secondDistance + 1) * timeValue, yResolution * 2) # call yMovement again once the second oscillation in the x direction is finished
        self.i = 0
        self.j = 0
        if yResolution < 38 or yResolution == 40: # resolutions less than 40 will go right to the end of the platform, anything above 40 will stop at a distance %(120/yResolution) away
            for yValue in xrange(yResolution * 3, 120 + yResolution, yResolution * 2): # third iteration of yMovement
                delayMs = (((secondDistance + firstDistance) + 2) * timeValue) + ((secondDistance * timeValue) * (self.i))
                self.yMovement(delayMs, yValue)
                self.i = self.i + 1
            for yValue in xrange(yResolution * 4, 120 + yResolution, yResolution * 2): # got ride of + yResolution in max
                delayMs = ((((2 * secondDistance) + 1)) * timeValue) + ((secondDistance * timeValue) * (self.j))
                self.yMovement(delayMs, yValue)
                self.j = self.j + 1
        else:
           for yValue in xrange(yResolution * 3, 120, yResolution * 2):  # third iteration of yMovement
               delayMs = (((secondDistance + firstDistance) + 2) * timeValue) + (
                           (secondDistance * timeValue) * (self.i))
               self.yMovement(delayMs, yValue)
               self.i = self.i + 1
           for yValue in xrange(yResolution * 4, 120, yResolution * 2):  # got ride of + yResolution in max
               delayMs = ((((2 * secondDistance) + 1)) * timeValue) + ((secondDistance * timeValue) * (self.j))
               self.yMovement(delayMs, yValue)
               self.j = self.j + 1

    def xLoop(self, timeValue, xResolution, yResolution):
        # necessary for looping the x commands on static intervals
        oscillatingTime = (120 / yResolution) / 2  # determines how many times the scanner should oscillate back and forth
        lengthOfOneWidth = ((120 / xResolution) * 2) * timeValue # how long it takes to go back and forth once
        # lengthOfOneWidth = 25 * timeValue # the amount of movements per oscillation back and forth
        for xCoordinateValue in xrange(0, (oscillatingTime * lengthOfOneWidth) + lengthOfOneWidth, lengthOfOneWidth):  # calls forwards and backwards as necessary
            self.xWidthForward(xCoordinateValue, timeValue, xResolution)
            self.xWidthBackwards(xCoordinateValue, timeValue, xResolution)


    def xWidthForward(self, xCoordinate, timeValue, xResolution):  # used to be passed xCoordinate
        # Move the width of the bed forward in the positive x direction
        # Corresponds to a timer called in printer interactor widget
        self.scanTimer = qt.QTimer()
        if xResolution < 38 or xResolution == 40:
            for xValue in xrange(0, 120 + xResolution, xResolution):  # increment by 10 until 120
                delayMs = xCoordinate + xValue * ( timeValue / xResolution)  # xCoordinate ensures the clocks are starting at correct times and xValue * (timeValue / 10 ) increments according to delay
                self.XMovement(delayMs, xValue)
        else:
            for xValue in xrange(0, 120, xResolution):  # increment by 10 until 120
                delayMs = xCoordinate + xValue * ( timeValue / xResolution)  # xCoordinate ensures the clocks are starting at correct times and xValue * (timeValue / 10 ) increments according to delay
                self.XMovement(delayMs, xValue)

    def xWidthBackwards(self, xCoordinate, timeValue, xResolution):
        # Move the width of the bed backwards in the negative x direction
        # Corresponds to a timer called in printer interactor widget
        self.scanTimer = qt.QTimer()
        if xResolution < 38 or xResolution == 40:
            for xValue in xrange(120, -xResolution, -xResolution):
                delayMs = abs(xValue - 120) * (timeValue / xResolution) + (120 / xResolution + 1) * timeValue + xCoordinate  # same principle as xWidth forwards but with abs value to account for decrementing values and 13*time value to offset starting interval
                self.XMovement(delayMs, xValue)
        else:
            for xValue in xrange(120, 0, -xResolution):
                delayMs = abs(xValue - 120) * (timeValue / xResolution) + (120 / xResolution + 1) * timeValue + xCoordinate  # same principle as xWidth forwards but with abs value to account for decrementing values and 13*time value to offset starting interval
                self.XMovement(delayMs, xValue)

    def yMovement(self, timeValue, yResolution):
        self.randomScanTimer = qt.QTimer()
        self.randomScanTimer.singleShot(timeValue, lambda: self.controlledYMovement(yResolution))

    def XMovement(self, timevar, movevar):
        self.randomScanTimer = qt.QTimer()
        self.randomScanTimer.singleShot(timevar, lambda: self.controlledXMovement(movevar))

    def slowEdgeTracing(self, xcoordinate, ycoordinate, timevar):
        self.edgetimer = qt.QTimer()
        self.edgetimer.singleShot(timevar, lambda: self.controlledXYMovement(xcoordinate, ycoordinate))

    def xyMovement(self,xcoordinate, ycoordinate, timevar):
        self.randomScanTimer = qt.QTimer()
        self.randomScanTimer.singleShot(timevar, lambda: self.controlledXYMovement(xcoordinate,ycoordinate))

    def ZMovement(self, timeValue, zcoordinate):
        self.randomScanTimer = qt.QTimer()
        self.randomScanTimer.singleShot(timeValue, lambda: self.controlledZMovement(zcoordinate))

    def controlledXYMovement(self, xcoordinate, ycoordinate):
        self.xyControlCmd.SetCommandAttribute('Text', 'G1 X%d Y%d' % (xcoordinate, ycoordinate))
        slicer.modules.openigtlinkremote.logic().SendCommand(self.xyControlCmd, self.serialIGTLNode.GetID())

    def controlledXMovement(self, xCoordinate):  # x movement
        self.xControlCmd.SetCommandAttribute('Text', 'G1 X%d' % (xCoordinate))
        slicer.modules.openigtlinkremote.logic().SendCommand(self.xControlCmd, self.serialIGTLNode.GetID())

    def controlledYMovement(self, yCoordinate):  # y movement
        self.yControlCmd.SetCommandAttribute('Text', 'G1 Y%d' % (yCoordinate))
        slicer.modules.openigtlinkremote.logic().SendCommand(self.yControlCmd, self.serialIGTLNode.GetID())

    def controlledZMovement(self, zcoordinate):
        self.zControlCmd.SetCommandAttribute('Text', 'G1 Z%d' % (zcoordinate))
        slicer.modules.openigtlinkremote.logic().SendCommand(self.zControlCmd, self.serialIGTLNode.GetID())

    # specific movement commands for keyboard control, necessary because of serialIGTLNode declaration
    def keyboardControlledXMovementForward(self, serialIGTLNode):  # x movement
        if self.currentXcoordinate < 120:
            self.currentXcoordinate = self.currentXcoordinate + 5
        else:
            self.currentXcoordinate = self.currentXcoordinate - 5
        self.xControlCmd = slicer.vtkSlicerOpenIGTLinkCommand()
        self.xControlCmd.SetCommandName('SendText')
        self.xControlCmd.SetCommandAttribute('DeviceId', "SerialDevice")
        self.xControlCmd.SetCommandTimeoutSec(1.0)
        self.xControlCmd.SetCommandAttribute('Text', 'G1 X%d' % (self.currentXcoordinate))
        slicer.modules.openigtlinkremote.logic().SendCommand(self.xControlCmd, serialIGTLNode.GetID())

    def keyboardControlledXMovementBackwards(self, serialIGTLNode):  # x movement
        if self.currentXcoordinate > 5:
            self.currentXcoordinate = self.currentXcoordinate - 5
        else:
            self.currentXcoordinate = self.currentXcoordinate + 5
        self.xControlCmd = slicer.vtkSlicerOpenIGTLinkCommand()
        self.xControlCmd.SetCommandName('SendText')
        self.xControlCmd.SetCommandAttribute('DeviceId', "SerialDevice")
        self.xControlCmd.SetCommandTimeoutSec(1.0)
        self.xControlCmd.SetCommandAttribute('Text', 'G1 X%d' % (self.currentXcoordinate))
        slicer.modules.openigtlinkremote.logic().SendCommand(self.xControlCmd, serialIGTLNode.GetID())

    def keyboardControlledYMovementForward(self, serialIGTLNode):  # y movement
        if self.currentYcoordinate < 120:
            self.currentYcoordinate = self.currentYcoordinate + 5
        else:
            self.currentYcoordinate = self.currentYcoordinate - 5
        self.yControlCmd = slicer.vtkSlicerOpenIGTLinkCommand()
        self.yControlCmd.SetCommandName('SendText')
        self.yControlCmd.SetCommandAttribute('DeviceId', "SerialDevice")
        self.yControlCmd.SetCommandTimeoutSec(1.0)
        self.yControlCmd.SetCommandAttribute('Text', 'G1 Y%d' % (self.currentYcoordinate))
        slicer.modules.openigtlinkremote.logic().SendCommand(self.yControlCmd, serialIGTLNode.GetID())

    def keyboardControlledYMovementBackwards(self,serialIGTLNode):  # y movement
        if self.currentYcoordinate > 5:
            self.currentYcoordinate = self.currentYcoordinate - 5
        else:
            self.currentYcoordinate = self.currentYcoordinate + 5
        self.yControlCmd = slicer.vtkSlicerOpenIGTLinkCommand()
        self.yControlCmd.SetCommandName('SendText')
        self.yControlCmd.SetCommandAttribute('DeviceId', "SerialDevice")
        self.yControlCmd.SetCommandTimeoutSec(1.0)
        self.yControlCmd.SetCommandAttribute('Text', 'G1 Y%d' % (self.currentYcoordinate))
        slicer.modules.openigtlinkremote.logic().SendCommand(self.yControlCmd, serialIGTLNode.GetID())

    def keyboardControlledHomeMovement(self,serialIGTLNode):
        self.yControlCmd = slicer.vtkSlicerOpenIGTLinkCommand()
        self.yControlCmd.SetCommandName('SendText')
        self.yControlCmd.SetCommandAttribute('DeviceId', "SerialDevice")
        self.yControlCmd.SetCommandTimeoutSec(1.0)
        self.yControlCmd.SetCommandAttribute('Text', 'G28 X Y')
        slicer.modules.openigtlinkremote.logic().SendCommand(self.yControlCmd, serialIGTLNode.GetID())




class PrinterInteractorTest(ScriptedLoadableModuleTest):
    """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        """Run as few or as many tests as needed here.
    """
        self.setUp()
        self.test_PrinterInteractor1()

    def test_PrinterInteractor1(self):
        """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

        self.delayDisplay("Starting the test")
        #
        # first, get some data
        #
        import urllib
        downloads = (
            ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

        for url, name, loader in downloads:
            filePath = slicer.app.temporaryPath + '/' + name
            if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
                logging.info('Requesting download %s from %s...\n' % (name, url))
                urllib.urlretrieve(url, filePath)
            if loader:
                logging.info('Loading %s...' % (name,))
                loader(filePath)
        self.delayDisplay('Finished with download and loading')

        volumeNode = slicer.util.getNode(pattern="FA")
        logic = PrinterInteractorLogic()
        self.assertIsNotNone(logic.hasImageData(volumeNode))
        self.delayDisplay('Test passed!')