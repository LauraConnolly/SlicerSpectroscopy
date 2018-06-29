import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import time
import functools
import argparse
import math


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

        ScriptedLoadableModuleWidget.setup(self)

        # Instantiate and connect widgets ...
        self.logic = PrinterInteractorLogic()
        #
        # Parameters Area
        #
        connect_to_printerCollapsibleButton = ctk.ctkCollapsibleButton()
        connect_to_printerCollapsibleButton.text = "Connect to Printer"
        self.layout.addWidget(connect_to_printerCollapsibleButton)

        #geometricAnalysisCollapsibleButton = ctk.ctkCollapsibleButton()
        #geometricAnalysisCollapsibleButton.text = "Geometric Analysis"
        #self.layout.addWidget(geometricAnalysisCollapsibleButton)

        # Layout within the connect to printer collapsible button
        connect_to_printerFormLayout = qt.QFormLayout(connect_to_printerCollapsibleButton)

        # Layout within the geometric analysis collapsible button
        #geometricAnalysisCollapsibleButtonFormLayout = qt.QFormLayout(geometricAnalysisCollapsibleButton)

                                                    # Connect to printer buttons

        #
        # Home Button
        #
        self.homeButton = qt.QPushButton("Home")
        self.homeButton.toolTip = "Return to reference axis"
        self.homeButton.enabled = True
        connect_to_printerFormLayout.addRow(self.homeButton)
        self.homeButton.connect('clicked(bool)', self.onHomeButton)
        #
        #Center button
        #
        self.moveMiddleButton = qt.QPushButton("Center")
        self.moveMiddleButton.toolTip = "Move to the middle of the stage, helpful for acquiring reference spectrum ."
        self.moveMiddleButton.enabled = True
        connect_to_printerFormLayout.addRow(self.moveMiddleButton)
        self.moveMiddleButton.connect('clicked(bool)', self.onTestingButton)
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
        self.inputSelector.setToolTip("Pick the input to the algorithm.")
        connect_to_printerFormLayout.addRow("Connect to: ", self.inputSelector)
        #
        # Port Selector
        #
        #self.portSelector = qt.QComboBox()
        #self.portSelector.insertItem(1, "PORT 1")
        #self.portSelector.insertItem(2, "PORT 2")
        #self.portSelector.insertItem(3, "PORT 3")
        #self.portSelector.insertItem(4, "PORT 4")
        #connect_to_printerFormLayout.addRow("Port :", self.portSelector)
        #
        # Wavelength Selector
        #
        self.laserSelector = qt.QComboBox()
        self.laserSelector.insertItem(1, "UV: 395 nm ")
        self.laserSelector.insertItem(2, "RED: 660 nm")
        connect_to_printerFormLayout.addRow("Laser Wavelength :", self.laserSelector)
        #
        # Output array selector
        #
        self.outputArraySelector = slicer.qMRMLNodeComboBox()
        self.outputArraySelector.nodeTypes = (("vtkMRMLDoubleArrayNode"), "")
        self.outputArraySelector.addEnabled = True
        self.outputArraySelector.removeEnabled = True
        self.outputArraySelector.noneEnabled = False
        self.outputArraySelector.showHidden = False
        self.outputArraySelector.showChildNodeTypes = False
        self.outputArraySelector.setMRMLScene(slicer.mrmlScene)
        self.outputArraySelector.setToolTip("Pick the output to the algorithm.")
        connect_to_printerFormLayout.addRow("Output spectrum array: ", self.outputArraySelector)
        #
        # X Resolution
        #
        self.xResolution_spinbox = qt.QSpinBox()
        self.xResolution_spinbox.setMinimum(0)
        self.xResolution_spinbox.setMaximum(120)
        self.xResolution_spinbox.setValue(0)
        connect_to_printerFormLayout.addRow("X resolution (mm / step) :", self.xResolution_spinbox)
        #
        # Y Resolution
        #
        self.yResolution_spinbox = qt.QSpinBox()
        self.yResolution_spinbox.setMinimum(0)
        self.yResolution_spinbox.setMaximum(120)
        self.yResolution_spinbox.setValue(0)
        connect_to_printerFormLayout.addRow("Y resolution (mm/ step):", self.yResolution_spinbox)
        #
        # Time per reading
        #
        self.timeDelay_spinbox = qt.QSpinBox()
        self.timeDelay_spinbox.setMinimum(0)
        self.timeDelay_spinbox.setMaximum(5000)
        self.timeDelay_spinbox.setValue(1000)
        # self.timeDelay_spinbox.setSingleStep(1000)
        connect_to_printerFormLayout.addRow("Time for data delay (ms) :", self.timeDelay_spinbox)
        #
        #edge tracing button
        #
        self.createModelButton = qt.QPushButton("Trace Edges")
        self.createModelButton.toolTip = "B"
        self.createModelButton.enabled = True
        connect_to_printerFormLayout.addRow(self.createModelButton)
        self.createModelButton.connect('clicked(bool)', self.onFindConvexHull)

        # learn spectra button

        self.learnSpectraButton = qt.QPushButton("Learn Spectra (necessary for 660 nm wavelength)")
        self.learnSpectraButton.toolTip = "Begin systematic surface scan"
        self.learnSpectraButton.enabled = True
        connect_to_printerFormLayout.addRow(self.learnSpectraButton)
        self.learnSpectraButton.connect('clicked(bool)', self.onLearnSpectraButton)
        #
        # Surface scan button
        #
        self.scanButton = qt.QPushButton("GO")
        self.scanButton.toolTip = "Begin systematic surface scan"
        self.scanButton.enabled = True
        connect_to_printerFormLayout.addRow(self.scanButton)
        self.scanButton.connect('clicked(bool)', self.onScanButton)
        self.scanButton.setStyleSheet("background-color: green; font: bold")

        #
        # Stop button
        #
        self.stopButton = qt.QPushButton("STOP")
        self.stopButton.toolTip = "Requires restart."
        self.stopButton.enabled = True
        connect_to_printerFormLayout.addRow(self.stopButton)
        self.stopButton.connect('clicked(bool)', self.onStopButton)
        self.stopButton.setStyleSheet("background-color: red; font: bold")

        # Testing button
        self.testButton = qt.QPushButton("test")
        self.testButton.toolTip = "Requires restart."
        self.testButton.enabled = True
        connect_to_printerFormLayout.addRow(self.testButton)
        self.testButton.connect('clicked(bool)', self.onTestButton)

        self.wheretoButton = qt.QPushButton("where to next?")
        self.wheretoButton.toolTip = "Requires restart."
        self.wheretoButton.enabled = True
        connect_to_printerFormLayout.addRow(self.wheretoButton)
        self.wheretoButton.connect('clicked(bool)', self.onWhereToNext)

        self.findTrajectoryButton = qt.QPushButton("Find Trajectory")
        self.findTrajectoryButton.toolTip = "Requires restart."
        self.findTrajectoryButton.enabled = True
        connect_to_printerFormLayout.addRow(self.findTrajectoryButton)
        self.findTrajectoryButton.connect('clicked(bool)', self.go)

        self.singleShotButton = qt.QPushButton("test 2")
        self.singleShotButton.toolTip = "Requires restart."
        self.singleShotButton.enabled = True
        connect_to_printerFormLayout.addRow(self.singleShotButton)
        self.singleShotButton.connect('clicked(bool)', self.checkTimer)

                                                # geometric analysis buttons
        #
        # Shape Selector
        #
        #self.shapeSelector = qt.QSpinBox()
        #self.shapeSelector.setMinimum(0)
        #self.shapeSelector.setMaximum(6)
        #self.shapeSelector.setValue(0)
        #geometricAnalysisCollapsibleButtonFormLayout.addRow("Number of vertices:", self.shapeSelector)
        #
        # geometric analysis button
        #
        #self.geometricAnalysisButton = qt.QPushButton("Geometric Analysis")
        #self.geometricAnalysisButton.toolTip = "Requires restart."
        #self.geometricAnalysisButton.enabled = True
        #geometricAnalysisCollapsibleButtonFormLayout.addRow(self.geometricAnalysisButton)
        #self.geometricAnalysisButton.connect('clicked(bool)', self.onGeometricAnalysis)




        self.layout.addStretch(1)

    def onStopMotorButton(self):
        self.scanTimer.stop()

    def cleanup(self):
        pass

    def onSerialIGLTSelectorChanged(self):
        self.logic.setSerialIGTLNode(serialIGTLNode=self.inputSelector.currentNode())
        pass  # call self.logic.setSerial...(new value of selector)

    def ondoubleArrayNodeChanged(self):
        self.logic.setdoubleArrayNode(doubleArrayNode=self.inputSelector.currentNode())
        pass


    def onHomeButton(self, SerialIGTLNode):
        self.onSerialIGLTSelectorChanged()
        self.logic.home()

        # TODO: change name, this is the function that moves middle
    def onTestingButton(self):
        self.ondoubleArrayNodeChanged()
        self.onSerialIGLTSelectorChanged()
        self.logic.middleMovement()

    def onScanButton(self):
        self.onSerialIGLTSelectorChanged()

        # Controlled printer movement
        # resolution can be changed as necessary
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
        for self.iterationTimingValue in range(0, (stopsToVisitX * stopsToVisitY * self.timeValue) + 10*self.timeValue, self.timeValue):  # 300 can be changed to x resolution by y resolution
            self.tumorTimer.singleShot(self.iterationTimingValue, lambda: self.tissueDecision())
            self.iterationTimingValue = self.iterationTimingValue + self.timeValue  # COMMENT OUT MAYBE!

    def onTumorButton(self):
        self.onSerialIGLTSelectorChanged()
        self.logic.spectrumComparisonUV(self.outputArraySelector.currentNode())

    def onStopButton(self):
        self.onSerialIGLTSelectorChanged()
        self.logic.emergencyStop()

        #changed to spectrum comparison UV
    def tissueDecision(self):
        self.ondoubleArrayNodeChanged()
        self.onSerialIGLTSelectorChanged()

        if (self.laserSelector.currentIndex) == 0 :
         if self.logic.spectrumComparisonUV(self.outputArraySelector.currentNode()) == False:  # add a fiducial if the the tumor detecting function returns false
            self.logic.get_coordinates()
        elif (self.laserSelector.currentIndex) == 1:
          if self.logic.spectrumComparison(self.outputArraySelector.currentNode()) == False:  # add a fiducial if the the tumor detecting function returns false
            self.logic.get_coordinates()
        else:
            return

    def onTestButton(self):
        self.ondoubleArrayNodeChanged()
        self.onSerialIGLTSelectorChanged()
        #self.logic.spectrumComparisonUV(self.outputArraySelector.currentNode())
        self.logic.automatedEdgeTracing(self.outputArraySelector.currentNode())

        # May not need these
    def onFindConvexHull(self):
         self.logic.convexHull()


    #def onSetTumorBoundaries(self):
     #   self.ondoubleArrayNodeChanged()
      #  self.onSerialIGLTSelectorChanged()
       # self.logic.setTumorBoundaries()

    def onLearnSpectraButton(self):
        self.ondoubleArrayNodeChanged()
        self.onSerialIGLTSelectorChanged()
        self.logic.getSpectralData(self.outputArraySelector.currentNode())

    def onWhereToNext(self):
        self.ondoubleArrayNodeChanged()
        self.onSerialIGLTSelectorChanged()
        self.logic.checkQuadrantValues(self.outputArraySelector.currentNode())

    def go(self):
        self.ondoubleArrayNodeChanged()
        self.onSerialIGLTSelectorChanged()
        self.logic.findTrajectory(self.outputArraySelector.currentNode())

    def checkTimer(self):
        self.ondoubleArrayNodeChanged()
        self.onSerialIGLTSelectorChanged()
        self.logic.keepGoing(self.outputArraySelector.currentNode())

# in order to access and read specific data points use this function
# def onTestingButton(self):

# self.logic.testFunc(self.outputArraySelector.currentNode())


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
    _distanceArray = []
    _yHeightArray = []
    _yHullArray = []
    _xHullArray = []

    # arrays for edge tracing
    _saveycoordinate = []
    _savexcoordinate = []

    # arrays for quadrant checker
    _tumorCheck = []
    _tumorCheck2 = []

    _returnValue = []


    def __init__(self):
        # some of these need to go
        self.baud_rate = 115200
        self.serialIGTLNode = None
        self.doubleArrayNode = None
        self.spectrumImageNode = None
        self.observerTags = []
        self.outputArrayNode = None
        self.numberOfDataPoints = 100
        self.pointGenerated = 0
        self.pointNumber = 1
        self.spectraCollectedflag = 0
        self.maxXforY = 0
        self.fiducialCount = 0
        self.foundTumor = 0
        # Polydata attributes
        # self.dataCollection = vtk.vtkPolyData()
        self.dataPoints = vtk.vtkPoints()
        self.referenceSpectra = vtk.vtkPolyData()
        self.spectra = vtk.vtkPoints()
        self.pointsForHull = vtk.vtkPoints()

        self.timerValue = 0

        # coordinate class declaration
        self.xcoordinate = 0
        self.ycoordinate = 0
        self.zcoordinate = 0

        self.pointsForEdgeTracing = vtk.vtkPoints()
        self.timeVariable = 2000

        self.currentSpectrum = vtk.vtkPoints()
        self.stopVal = 10000

        self.averageDifferences = 0


        self.saveIterationValue = 0

        self.checkingQuadrants = 0

        self.tumorFlag = 0

        self.addedEdge = 0



        # instantiate coordinate values
        self.getCoordinateCmd = slicer.vtkSlicerOpenIGTLinkCommand()
        self.getCoordinateCmd.SetCommandName('SendText')
        self.getCoordinateCmd.SetCommandAttribute('DeviceId', "SerialDevice")
        self.getCoordinateCmd.SetCommandTimeoutSec(1.0)
        self.getCoordinateCmd.SetCommandAttribute('Text', 'M114')
        self.getCoordinateCmd.AddObserver(self.getCoordinateCmd.CommandCompletedEvent, self.onPrinterCommandCompleted)
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

        #
        self.timePerXWidth = 26.5
        self.startNext = 0
        self.x = 0
        self.delayMs = 1000
        # Timer stuff

    def setSerialIGTLNode(self, serialIGTLNode):
        self.serialIGTLNode = serialIGTLNode

    def setdoubleArrayNode(self, doubleArrayNode):
        self.doubleArrayNode = doubleArrayNode

    def addObservers(self):
        if self.spectrumImageNode:
            print "Add observer to {0}".format(self.spectrumImageNode.GetName())
            self.observerTags.append(
                [self.spectrumImageNode, self.spectrumImageNode.AddObserver(vtk.vtkCommand.ModifiedEvent,
                                                                            self.onSpectrumImageNodeModified)])

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

        self.averageDifferences = 0

        for j in xrange(0, 101, 1):
            x = self.currentSpectrum.GetPoint(j)
            y = self.spectra.GetPoint(j)
            self.averageDifferences = self.averageDifferences + (y[1] - x[1])

        print(self.averageDifferences)



        if abs(self.averageDifferences) <7 : # < 7 for white and black
            print " tumor"
            self.get_coordinates() # THIS LINE WILL BREAK ORIGINAL CODE
            return False
        else:
            print "healthy"
            return True


        # used with UV laser to distinguish between spectrums that vary by an insignificant amount at a specific wavelength / data point

    def spectrumComparisonUV(self, outputArrayNode):

        self.outputArrayNode = outputArrayNode
        pointsArray = self.outputArrayNode.GetArray()
            # point contains a wavelength and a corresponding intensity
            # each data point has 2 rows of data, one corresponding to wavelength and one corresponding to intensity
        self.componentIndexWavelength = 0
        self.componentIndexIntensity = 1
            # TODO: fix this data aquisition
            # commented out lines are possible improvements or useful for different probes
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





        if tumorCheck < 0.5: #0.85- 0.9 on white paper
            print "tumor"
            return False

        else:
            print "healthy"
            return True

    def get_coordinates(self):
        slicer.modules.openigtlinkremote.logic().SendCommand(self.getCoordinateCmd, self.serialIGTLNode.GetID())

    def onPrinterCommandCompleted(self, observer, eventid):
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

        # added for automated edge tracing
        if self.addedEdge == 0:
            self._savexcoordinate.append(self.xcoordinate)
            self._saveycoordinate.append(self.ycoordinate)
            self.addedEdge = 1


        self.dataCollection = self.createPolyDataPoint(self.xcoordinate, self.ycoordinate, self.zcoordinate)
                #  DON'T DELETE HOW WE ADD FIDUCIALS
       # if self.fiducialCount < 1:

            #self.fiducialMarker(self.xcoordinate, self.ycoordinate, self.zcoordinate)
            #self.fiducialCount = self.fiducialCount + 1
        #else:
          #  self.addToCurrentNode(self.xcoordinate, self.ycoordinate, self.zcoordinate)


         # random issues with this distance array

        #distance = self.calculateDistance(xcoordinate, ycoordinate)
        #self._distanceArray.append(distance)
        #self._yHeightArray.append(ycoordinate)
        #print(self._distanceArray)


                                             # automated edge tracing
    def edgeTrace(self, outputArrayNode):
        self.checkQuadrantValues(outputArrayNode)



    def automatedEdgeTracing(self, outputArrayNode):
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
        self.callMovement(1000, (self._savexcoordinate[index] + 10), (self._saveycoordinate[index])) # right 10
        self.readCoordinatesAtTimeInterval2(2000,outputArrayNode)

        self.callMovement(2000, (self._savexcoordinate[index]), (self._saveycoordinate[index] - 10)) # back 10
        self.readCoordinatesAtTimeInterval2(3000, outputArrayNode)

        self.callMovement(3000, (self._savexcoordinate[index] - 10), (self._saveycoordinate[index])) # left 10
        self.readCoordinatesAtTimeInterval2(4000, outputArrayNode)

        self.callMovement(4000, (self._savexcoordinate[index]), (self._saveycoordinate[index] + 10)) # forward 10
        self.readCoordinatesAtTimeInterval2(5000, outputArrayNode)

        self.callMovement(5000, (self._savexcoordinate[index]), (self._saveycoordinate[index])) # back to center
        self.readCoordinatesAtTimeInterval2(6000, outputArrayNode)

        self.callPrintFunc(6000)
        self.startNext = 6000
        self.startTrajectorySearch(outputArrayNode)

    def printFunc(self):
        print(self._tumorCheck)

    def callPrintFunc(self,delay):
        self.edgeTraceTimer.singleShot(delay, lambda: self.printFunc())

    def callMovement(self,delay,xcoordinate,ycoordinate):
        self.cutInTimer.singleShot(delay, lambda: self.controlledXYMovement(xcoordinate, ycoordinate))


    def readCoordinatesAtTimeInterval(self, delay, outputArrayNode):
        self.edgeTraceTimer.singleShot(delay, lambda: self.spectrumComparison(outputArrayNode))

    def readCoordinatesAtTimeInterval2(self, delay, outputArrayNode):
        self.edgeTraceTimer.singleShot(delay, lambda: self.spectrumComparison2(outputArrayNode))

    def readCoordinatesAtTimeInterval3(self, delay, outputArrayNode):
        self.edgeTraceTimer.singleShot(delay, lambda: self.spectrumComparison3(outputArrayNode))

    def moveBackToOriginalEdgePoint(self):
        x = len(self._savexcoordinate) - 1
        self.edgeTraceTimer.singleShot(16500, lambda: self.controlledXYMovement(self._savexcoordinate[x], self._saveycoordinate[x]))

    def spectrumComparison2(self, outputArrayNode):

        if self.spectraCollectedflag == 0:
            print " Error: reference spectrum not collected."
            return

        self.currentOutputArrayNode = outputArrayNode
        currentPointsArray = self.currentOutputArrayNode.GetArray()

        self.currentSpectrum.SetNumberOfPoints(100)
        for i in xrange(0, 101, 1):
            self.currentSpectrum.SetPoint(i, currentPointsArray.GetTuple(i))

        self.averageDifferences = 0

        for j in xrange(0, 101, 1):
            x = self.currentSpectrum.GetPoint(j)
            y = self.spectra.GetPoint(j)
            self.averageDifferences = self.averageDifferences + (y[1] - x[1])

        print(self.averageDifferences)

        if abs(self.averageDifferences) < 7:  # < 7 for white and black
            print " tumor"
            self._tumorCheck.append(1)
            return False
        else:
            print "healthy"
            self._tumorCheck.append(0)
            return True

    def spectrumComparison3(self, outputArrayNode):

        if self.spectraCollectedflag == 0:
            print " Error: reference spectrum not collected."
            return

        self.currentOutputArrayNode = outputArrayNode
        currentPointsArray = self.currentOutputArrayNode.GetArray()

        self.currentSpectrum.SetNumberOfPoints(100)
        for i in xrange(0, 101, 1):
            self.currentSpectrum.SetPoint(i, currentPointsArray.GetTuple(i))

        self.averageDifferences = 0

        for j in xrange(0, 101, 1):
            x = self.currentSpectrum.GetPoint(j)
            y = self.spectra.GetPoint(j)
            self.averageDifferences = self.averageDifferences + (y[1] - x[1])

        print(self.averageDifferences)

        if abs(self.averageDifferences) < 7:  # < 7 for white and black
            print " tumor"
            #self._tumorCheck.append(1)
            return False
        else:
            print "healthy"
            #self._tumorCheck.append(0)
            self._returnValue.append(1)
            return True

    def findTrajectory(self, outputArrayNode):

        self.trajectoryTimer = qt.QTimer()
        index = len(self._tumorCheck)
        y = len(self._savexcoordinate) - 1

        if self._tumorCheck[index - 4] ==1 and self._tumorCheck[index -3 ] == 0 and self._tumorCheck[index - 2] == 0 and self._tumorCheck[index -1 ] ==1:
            print "Quadrant 2"
            #for x in xrange(0, 2500, 500):
                #self.readCoordinatesAtTimeInterval(x, outputArrayNode)

            self.callMovement(0,self._savexcoordinate[y] -5, self._saveycoordinate[y] + 5)
            #self.readCoordinatesAtTimeInterval3(0, outputArrayNode)

            self.checkArray(outputArrayNode, -10, 1000)

            #self.checkArray(outputArrayNode, -15,  2000)
            #self.checkArray(outputArrayNode, -20,  3000)

        if self._tumorCheck[index - 4] == 1 and self._tumorCheck[index - 3] == 1 and self._tumorCheck[index - 2] == 0 and self._tumorCheck[index - 1] == 0:
            print "Quadrant 1"
            # for x in xrange(0, 2500, 500):
            # self.readCoordinatesAtTimeInterval(x, outputArrayNode)

            self.callMovement(0, self._savexcoordinate[y] + 5, self._saveycoordinate[y] + 5)
            # self.readCoordinatesAtTimeInterval3(0, outputArrayNode)

            self.checkArray(outputArrayNode, 10, 1000)
            self.checkArray(outputArrayNode, 15, 2000)
            self.checkArray(outputArrayNode, 20, 3000)

        if self._tumorCheck[index - 4] == 0 and self._tumorCheck[index - 3] == 1 and self._tumorCheck[index - 2] == 1 and self._tumorCheck[index - 1] == 0:
            print "Quadrant 3"
            # for x in xrange(0, 2500, 500):
            # self.readCoordinatesAtTimeInterval(x, outputArrayNode)

            self.callMovement(0, self._savexcoordinate[y] + 5, self._saveycoordinate[y] + 5)
            # self.readCoordinatesAtTimeInterval3(0, outputArrayNode)

            self.checkArray(outputArrayNode, 10, 1000)
            self.checkArray(outputArrayNode, 15, 2000)
            self.checkArray(outputArrayNode, 20, 3000)

        if self._tumorCheck[index - 4] == 0 and self._tumorCheck[index - 3] == 1 and self._tumorCheck[index - 2] == 1 and self._tumorCheck[index - 1] == 0:
            print "Quadrant 4"
            # for x in xrange(0, 2500, 500):
            # self.readCoordinatesAtTimeInterval(x, outputArrayNode)

            self.callMovement(0, self._savexcoordinate[y] - 5, self._saveycoordinate[y] + 5)
            # self.readCoordinatesAtTimeInterval3(0, outputArrayNode)

            self.checkArray(outputArrayNode, -10, 1000)
            self.checkArray(outputArrayNode, -15, 2000)
            self.checkArray(outputArrayNode, -20, 3000)

        self.restart()
    def restart(self):
        self.addedEdge == 0



    def if1(self, outputArrayNode, stepVal, delay):
        if len(self._returnValue) != 0:
            self.get_coordinates()
            print "yay"
            return
        else:
            self.callMovement(delay, self._savexcoordinate[0] + stepVal, self._saveycoordinate[0] + abs(stepVal))
            self.readCoordinatesAtTimeInterval3(delay, outputArrayNode)
            return




    def checkArray(self, outputArrayNode, stepVal, delay):
        checkingTimer = qt.QTimer()
        checkingTimer.singleShot(delay, lambda: self.if1(outputArrayNode, stepVal, delay))



    def startTrajectorySearch(self,outputArrayNode):
        trajTimer = qt.QTimer()
        trajTimer.singleShot(self.startNext,lambda: self.findTrajectory(outputArrayNode))

    #def checkForVal(self):
     #   self.x = len(self._returnValue)


            #print(len(self._returnValue))

            #self.trajectoryTimer.connect(self.controlledXYMovement(self._savexcoordinate[0] - 20, self._saveycoordinate[0] + 20))
            #if self.tumorFlag == 1:
                #self.trajectoryTimer.stop()
                #print " off path"


        # testing single shot timer stop

    def singleShotTimer(self):
        testingTimer = qt.QTimer()
        testingTimer.setInterval(10000)
        testingTimer.setSingleShot(True)
        testingTimer.connect(self.printer)
        testingTimer.start()









    def printer(self):
        print " tick"




    def fiducialMarker(self, xcoordinate, ycoordinate, zcoordinate):
        self.fiducialNode = slicer.vtkMRMLMarkupsFiducialNode()
        slicer.mrmlScene.AddNode(self.fiducialNode)
        self.fiducialNode.AddFiducial(xcoordinate, ycoordinate, zcoordinate)

    def addToCurrentNode(self, xcoordinate, ycoordinate, zcoordinate):
        self.fiducialNode.AddFiducial(xcoordinate, ycoordinate, zcoordinate)
        self.fiducialCount = self.fiducialCount + 1
        print(self.fiducialCount)

    def createPolyDataPoint(self, xcoordinate, ycoordinate, zcoordinate):
        if self.pointGenerated < 1:
            self.dataPoints.SetNumberOfPoints(700)  # allocate space for up to 100 data points
            self.pointGenerated = self.pointGenerated + 1
            self.pointsForHull.InsertNextPoint(xcoordinate, ycoordinate, zcoordinate)
            self.dataPoints.SetPoint(0, xcoordinate, ycoordinate, zcoordinate)
        else:
            self.dataPoints.SetPoint(self.pointNumber, xcoordinate, ycoordinate, zcoordinate)  # 10 specifies coordinates to be float values
            self.pointsForHull.InsertNextPoint(xcoordinate, ycoordinate, zcoordinate)
            self.pointNumber = self.pointNumber + 1

    def convexHull(self):


        self.hullPolydata = vtk.vtkPolyData()
        self.hullPolydata.SetPoints(self.pointsForHull)

        hull = vtk.vtkConvexHull2D()
        hull.SetInputData(self.hullPolydata)
        hull.Update()

        #print(hull.GetOutput())

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
            self.slowEdgeTracing(xcoordinate, ycoordinate, self.timeVariable)

            self.timeVariable = self.timeVariable + 2000
        self.slowEdgeTracing(self._xHullArray[0], self._yHullArray[0], (2000*pointLimit + 2000))
        self.ZMovement(2000, -5) # could be 35 or -5 depending on the last state
        self.ZMovement(2000*pointLimit + 4000, 0) #back to 40

    def createModel(self):
        # not necessary
        self.dataCollection = vtk.vtkPolyData()
        self.dataCollection.SetPoints(self.dataPoints)
        slicer.modules.models.logic().AddModel(self.dataCollection)

    #
    # function written for testing and understanding spectral data acquisition
    def testFunc(self, outputArrayNode):
        # Used to access specific wavelengths and intensitys of different data points
        self.outputArrayNode = outputArrayNode
        pointsArray = self.outputArrayNode.GetArray()
        # point contains a wavelength and a corresponding intensity
        # each data point has 2 rows of data, one corresponding to wavelength and one corresponding to intensity
        self.componentIndexWavelength = 0
        self.componentIndexIntensity = 1

        numberOfPoints = pointsArray.GetNumberOfTuples()  # access the number of points received from the spectra
        print(numberOfPoints)
        # for pointIndex in xrange(60,80): #loop through the 60th - 80th data points
        wavelengthValue = pointsArray.GetComponent(62,0)  # checks the 187th point in the data stream, corresponds to the 650-700 nm wavelength (area of interest)
        intensityValue = pointsArray.GetComponent(62, 1)
        print(intensityValue)
        print(wavelengthValue)

    def home(self):

        slicer.modules.openigtlinkremote.logic().SendCommand(self.homeCmd, self.serialIGTLNode.GetID())

    def emergencyStop(self):
        # Writes to the printer to automatically stop all motors
        # Requires reboot
        slicer.modules.openigtlinkremote.logic().SendCommand(self.emergStopCmd, self.serialIGTLNode.GetID())
        self.emergStopCmd.AddObserver(self.emergStopCmd.CommandCompletedEvent, self.onPrinterCommandCompleted)

    def yLoop(self, timeValue, yResolution, xResolution):
        # specific intervals correspond to timeValues divisible by 1000
        # The variances in intervals were timed specifically to account for mechanical delays with the printer
        firstDistance = (120 / xResolution)
        secondDistance = 2 * (120 / xResolution)
        self.yMovement((firstDistance + 2) * timeValue, yResolution)
        self.yMovement((secondDistance + 1) * timeValue, yResolution * 2)
        self.i = 0
        self.j = 0
        for yValue in xrange(yResolution * 3, 120 + yResolution, yResolution * 2):
            delayMs = (((secondDistance + firstDistance) + 2) * timeValue) + ((secondDistance * timeValue) * (self.i))
            self.yMovement(delayMs, yValue)
            self.i = self.i + 1
        for yValue in xrange(yResolution * 4, 120 + yResolution, yResolution * 2):
            delayMs = ((((2 * secondDistance) + 1)) * timeValue) + ((secondDistance * timeValue) * (self.j))
            self.yMovement(delayMs, yValue)
            self.j = self.j + 1



    def xLoop(self, timeValue, xResolution, yResolution):
        # necessary for looping the x commands on static intervals
        oscillatingTime = (
                                  120 / yResolution) / 2  # determines how many times the scanner should oscillate back and forth
        lengthOfOneWidth = ((120 / xResolution) * 2) * timeValue
        # lengthOfOneWidth = 25 * timeValue # the amount of movements per oscillation back and forth
        for xCoordinateValue in xrange(0, (oscillatingTime * lengthOfOneWidth) + lengthOfOneWidth,
                                       lengthOfOneWidth):  # calls forwards and backwards as necessary
            self.xWidthForward(xCoordinateValue, timeValue, xResolution)
            self.xWidthBackwards(xCoordinateValue, timeValue, xResolution)

    def xWidthForward(self, xCoordinate, timeValue, xResolution):  # used to be passed xCoordinate
        # Move the width of the bed forward in the positive x direction
        # Corresponds to a timer called in printer interactor widget
        self.scanTimer = qt.QTimer()
        for xValue in xrange(0, 120, xResolution):  # increment by 10 until 120
            delayMs = xCoordinate + xValue * ( timeValue / xResolution)  # xCoordinate ensures the clocks are starting at correct times and xValue * (timeValue / 10 ) increments according to delay
            self.XMovement(delayMs, xValue)

    def xWidthBackwards(self, xCoordinate, timeValue, xResolution):
        # Move the width of the bed backwards in the negative x direction
        # Corresponds to a timer called in printer interactor widget
        self.scanTimer = qt.QTimer()
        for xValue in xrange(120, 0, -xResolution):
            delayMs = abs(xValue - 120) * (timeValue / xResolution) + (120 / xResolution + 1) * timeValue + xCoordinate  # same principle as xWidth forwards but with abs value to account for decrementing values and 13*time value to offset starting interval
            self.XMovement(delayMs, xValue)

    # Movement Controls (single shot, lambda timers for simple G Code message sending)


    def yMovement(self, timeValue, yResolution):
        self.randomScanTimer = qt.QTimer()
        self.randomScanTimer.singleShot(timeValue, lambda: self.controlledYMovement(yResolution))

    def XMovement(self, timevar, movevar):
        self.randomScanTimer = qt.QTimer()
        self.randomScanTimer.singleShot(timevar, lambda: self.controlledXMovement(movevar))

    def slowEdgeTracing(self, xcoordinate, ycoordinate, timevar):
        self.edgetimer = qt.QTimer()
        self.edgetimer.singleShot(timevar, lambda: self.controlledXYMovement(xcoordinate, ycoordinate))

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

    def controlledZMovement(self, zcoordinate):  # y movement
        self.zControlCmd.SetCommandAttribute('Text', 'G1 Z%d' % (zcoordinate))
        slicer.modules.openigtlinkremote.logic().SendCommand(self.zControlCmd, self.serialIGTLNode.GetID())

    def middleMovement(self):
        self.printerControlCmd.SetCommandAttribute('Text', 'G1 X60 Y60')
        slicer.modules.openigtlinkremote.logic().SendCommand(self.printerControlCmd, self.serialIGTLNode.GetID())

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