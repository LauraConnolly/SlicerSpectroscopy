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
    self.parent.title = "PrinterInteractor" # TODO make this more human readable by adding spaces
    self.parent.categories = ["SlicerSpectroscopy"]
    self.parent.dependencies = []
    self.parent.contributors = ["Laura Connolly PerkLab (Queen's University), Mark Asselin PerkLab (Queen's University)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This is an module developed to interface Slicer Software with the Monoprice Mini V2 3D Printer for spectroscopy 
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

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

    # Layout within the dummy collapsible button
    connect_to_printerFormLayout = qt.QFormLayout(connect_to_printerCollapsibleButton)
    #
    # Home Button
    #
    self.homeButton = qt.QPushButton("Home")
    self.homeButton.toolTip = "Return to reference axis"
    self.homeButton.enabled = True
    connect_to_printerFormLayout.addRow(self.homeButton)
    self.homeButton.connect('clicked(bool)', self.onHomeButton)
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
    self.inputSelector.setMRMLScene( slicer.mrmlScene )
    self.inputSelector.setToolTip( "Pick the input to the algorithm." )
    connect_to_printerFormLayout.addRow("Connect to: ", self.inputSelector)
    #
    #Port Selector
    #
    self.portSelector = qt.QComboBox()
    self.portSelector.insertItem(1, "PORT 1")
    self.portSelector.insertItem(2, "PORT 2")
    self.portSelector.insertItem(3, "PORT 3")
    self.portSelector.insertItem(4, "PORT 4")
    connect_to_printerFormLayout.addRow("Port :", self.portSelector)
    #
    #Output array selector
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
    # Tumor distinction button
    #
    #self.tumorButton = qt.QPushButton("Tumor?")
    #self.tumorButton.toolTip = "Run the algorithm"
    #self.tumorButton.enabled = True
    #connect_to_printerFormLayout.addRow(self.tumorButton)
    #self.tumorButton.connect('clicked(bool)', self.onTumorButton)
    #

    #
    # Random scanning
    #
    #self.randomScanButton = qt.QPushButton("Random Scan")
    #self.randomScanButton.toolTip = " Begin random surface scan"
    #self.randomScanButton.toolTip = True
    #connect_to_printerFormLayout.addRow(self.randomScanButton)
    #self.randomScanButton.connect('clicked(bool)', self.onRandomScanButton)
    #


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
    self.timeDelay_spinbox.setMinimum(500)
    self.timeDelay_spinbox.setMaximum(2000)
    self.timeDelay_spinbox.setValue(1000)
    connect_to_printerFormLayout.addRow("Time for data delay (ms) :", self.timeDelay_spinbox)
    # Testing button
    #
    #self.testingButton = qt.QPushButton("Test spectra")
    #self.testingButton.toolTip = "Immediately stop printer motors, requires restart."
    #self.testingButton.enabled = True
    #connect_to_printerFormLayout.addRow(self.testingButton)
    #self.testingButton.connect('clicked(bool)', self.onTestingButton)
    # Surface scan button
    #
    self.scanButton = qt.QPushButton("GO")
    self.scanButton.toolTip = "Begin systematic surface scan"
    self.scanButton.enabled = True
    connect_to_printerFormLayout.addRow(self.scanButton)
    self.scanButton.connect('clicked(bool)', self.onScanButton)
    #
    # Stop button
    #
    self.stopButton = qt.QPushButton("STOP")
    self.stopButton.toolTip = "Immediately stop printer motors, requires restart."
    self.stopButton.enabled = True
    connect_to_printerFormLayout.addRow(self.stopButton)
    self.stopButton.connect('clicked(bool)', self.onStopButton)
    self.layout.addStretch(1)

  def onStopMotorButton(self):
    self.scanTimer.stop()

  def cleanup(self):
    pass

  def onSerialIGLTSelectorChanged(self):
    self.logic.setSerialIGTLNode(serialIGTLNode= self.inputSelector.currentNode())
    pass # call self.logic.setSerial...(new value of selector)

  def ondoubleArrayNodeChanged(self):
    self.logic.setdoubleArrayNode(doubleArrayNode= self.inputSelector.currentNode())
    pass

  def onHomeButton(self, SerialIGTLNode):
    self.onSerialIGLTSelectorChanged()
    self.logic.home()

  def onScanButton(self):
    self.onSerialIGLTSelectorChanged()

    # Controlled printer movement
    # resolution can be changed as necessary
    self.timeValue = self.timeDelay_spinbox.value
    xResolution = self.xResolution_spinbox.value
    yResolution = self.yResolution_spinbox.value
    self.logic.xLoop(self.timeValue, xResolution) # calls a loop to toggle printer back and forth in the x direction
    self.logic.yLoop(self.timeValue) # calls a loop to increment the printer back in the y direction

    # tissue analysis
    self.tumorTimer = qt.QTimer()
    self.iterationTimingValue = 0

    for self.iterationTimingValue in range(0,300*self.timeValue,self.timeValue): # 300 can be changed to x resolution by y resolution
      self.tumorTimer.singleShot(self.iterationTimingValue, lambda: self.tissueDecision())
      self.iterationTimingValue = self.iterationTimingValue + self.timeValue

 # def onRandomScanButton(self):
 #   self.onSerialIGLTSelectorChanged()
 #   self.randomScanTimer = qt.QTimer()

    # Random data sets of 120 points from online generator
    #randomx = [84, 38, 74, 109, 48, 70, 17, 90, 92, 113, 115, 65, 67, 51, 114, 60, 108, 1, 119, 45, 5, 80, 20, 69, 75, 77, 52, 9, 41, 37, 95, 32, 7, 63, 118, 4, 72, 89, 50, 3, 78, 42, 64, 59, 104, 105, 100, 16, 55, 29, 68, 33, 117, 57, 56, 79, 53, 116, 26, 106, 22, 27, 23, 61, 111, 2, 86, 62, 73, 58, 101, 12, 110, 8, 91, 96, 25, 112, 46, 88, 54, 15, 85, 76, 120, 24, 71, 19, 81, 94, 93, 102, 49, 35, 47, 6, 34, 107, 103, 83, 44, 28, 82, 31, 40, 13, 10, 21, 14, 97, 18, 30, 0, 66, 87, 39, 43, 36, 11, 98]
    #randomy = [31, 42, 58, 76, 99, 71, 84, 32, 79, 98, 59, 34, 39, 12, 37, 91, 60, 104, 52, 46, 51, 82, 107, 100, 74, 38, 10, 96, 35, 41, 50, 27, 117, 67, 102, 112, 47, 69, 109, 25, 85, 97, 33, 73, 3, 2, 68, 88, 15, 0, 118, 65, 20, 11, 103, 21, 26, 80, 18, 57, 14, 17, 55, 101, 115, 81, 48, 106, 43, 30, 90, 45, 56, 40, 77, 86, 72, 61, 83, 92, 23, 63, 93, 105, 4, 16, 64, 78, 9, 24, 62, 1, 75, 13, 8, 70, 120, 95, 94, 116, 54, 89, 53, 19, 22, 66, 49, 44, 29, 119, 110, 28, 113, 5, 7, 6, 87, 111, 114, 108]

   # for arrayIndex in range(0, 120):
    #  delayMs = arrayIndex*7000 +7000; # largest distance to travel takes approximatley 7 seconds therefore the waitime between position movements is 7 seconds
     # self.logic.XMovement(delayMs, randomx[arrayIndex])
     # self.logic.YMovement(delayMs, randomy[arrayIndex])


    # tissue analysis
    # initiate a timer to distinguish the tissue every 2 seconds based on spectral reading
   # self.tumorTimer = qt.QTimer()

    #self.timeValue = 0
    #for self.timeValue in xrange(0,420000,2000):
     # self.tumorTimer.singleShot(self.timeValue, lambda: self.tissueDecision())
      #self.timeValue = self.timeValue + 2000


  def onStopButton(self):
    self.onSerialIGLTSelectorChanged()
    self.logic.emergencyStop()
    # self.tumorTimer.cancel()


  def onTumorButton(self):
    self.ondoubleArrayNodeChanged()
    self.onSerialIGLTSelectorChanged()
    self.logic.tumorDetection(self.outputArraySelector.currentNode())

    self.logic.get_coordinates()


  def tissueDecision(self):

    self.ondoubleArrayNodeChanged()
    self.onSerialIGLTSelectorChanged()
    if self.logic.tumorDetection(self.outputArraySelector.currentNode()) == False: #add a fiducial if the the tumor detecting function returns false
      self.logic.get_coordinates()





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

  def __init__(self):
    self.baud_rate = 115200
    self.serialIGTLNode = None
    self.doubleArrayNode = None
    self.spectrumImageNode = None
    self.observerTags = []
    self.outputArrayNode = None
    self.resolution = 100
    self.addNode = False
    self.fiducialNodeID = None
    self.nodeCreated = 0
    self.distanceArrayCreated = 0
    self.iterationVariable = 1
    # instantiate coordinate values
    self.getCoordinateCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    self.getCoordinateCmd.SetCommandName('SendText')
    self.getCoordinateCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    self.getCoordinateCmd.SetCommandTimeoutSec(1.0)
    self.getCoordinateCmd.SetCommandAttribute('Text', 'M114')
    self.getCoordinateCmd.AddObserver(self.getCoordinateCmd.CommandCompletedEvent, self.onPrinterCommandCompleted)


    # Timer stuff


  def setSerialIGTLNode(self, serialIGTLNode):
    self.serialIGTLNode = serialIGTLNode

  def setdoubleArrayNode(self, doubleArrayNode):
    self.doubleArrayNode = doubleArrayNode


  def addObservers(self):
    if self.spectrumImageNode:
      print "Add observer to {0}".format(self.spectrumImageNode.GetName())
      self.observerTags.append([self.spectrumImageNode, self.spectrumImageNode.AddObserver(vtk.vtkCommand.ModifiedEvent,
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
    a.SetNumberOfTuples(self.resolution)

    for row in xrange(numberOfRows):
      lineSource = vtk.vtkLineSource()
      lineSource.SetPoint1(0, row, 0)
      lineSource.SetPoint2(numberOfPoints - 1, row, 0)
      lineSource.SetResolution(self.resolution - 1)
      probeFilter = vtk.vtkProbeFilter()
      probeFilter.SetInputConnection(lineSource.GetOutputPort())
      if vtk.VTK_MAJOR_VERSION <= 5:
        probeFilter.SetSource(self.spectrumImageNode.GetImageData())
      else:
        probeFilter.SetSourceData(self.spectrumImageNode.GetImageData())
      probeFilter.Update()
      probedPoints = probeFilter.GetOutput()
      probedPointScalars = probedPoints.GetPointData().GetScalars()
      for i in xrange(self.resolution):
        a.SetComponent(i, row, probedPointScalars.GetTuple(i)[0])

    for i in xrange(self.resolution):
      a.SetComponent(i, 2, 0)

    probedPoints.GetPointData().GetScalars().Modified()

  def tumorDetection(self, outputArrayNode):
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
    #numberOfPoints = pointsArray.GetNumberOfTuples() #access the number of points received from the spectra
    #for pointIndex in xrange(numberOfPoints): #could potentially loop to check a certain range of data points
    #wavelengthValue = pointsArray.GetComponent(63,0) #checks the 187th point in the data stream
    #intensityValue = pointsArray.GetComponent(62, 1)

    tumorCheck = pointsArray.GetComponent(62,1) # Access the intensity value of the 62nd data point which corresponds to approximatley the 696th wavelength
    healthyCheck = pointsArray.GetComponent(68,1) # Access the intensity value of the 68th data point which corresponds to approximatley the 750th wavelength

    #Decision Loop
    if tumorCheck < 0.07:
      print "Tumor"
      return False
    elif tumorCheck ==1 and healthyCheck == 1:
      print "Healthy"
      return True
    else:
      print "Healthy 2" # uncertain measurements, typically occur outside of tumor range
      return



  def get_coordinates(self):
    #self.getCoordinateCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    #self.getCoordinateCmd.SetCommandName('SendText')
    #self.getCoordinateCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    #self.getCoordinateCmd.SetCommandTimeoutSec(1.0)
    #self.getCoordinateCmd.SetCommandAttribute('Text', 'M114')
    slicer.modules.openigtlinkremote.logic().SendCommand(self.getCoordinateCmd, self.serialIGTLNode.GetID())
    #self.getCoordinateCmd.AddObserver(self.getCoordinateCmd.CommandCompletedEvent, self.onPrinterCommandCompleted)


  def onPrinterCommandCompleted(self, observer, eventid):
    coordinateValues = self.getCoordinateCmd.GetResponseMessage()
    print("Command completed with status: " + self.getCoordinateCmd.StatusToString(self.getCoordinateCmd.GetStatus()))
    print("Response message: " + coordinateValues)
    print("Full response: " + self.getCoordinateCmd.GetResponseText())
    # parsing the string for specific coordinate values
    mylist = coordinateValues.split(" ")

    # Parse string for x coordinate value
    xvalues = mylist[0].split(":")
    xcoordinate = float(xvalues[1])

    # Parse string for y coordinate value
    yvalues = mylist[1].split(":")
    ycoordinate = float(yvalues[1])

    # Parse string for z coordinate value
    zvalues = mylist[2].split(":")
    zcoordinate = float(zvalues[1])

    # Create 1 distance array to store distances from origin in order to determine the width of the specimen

    self.numberOfFiducials = 28; # can be adjusted depending on how many fiducial points are required for an accurate reading
    if self.distanceArrayCreated < 1:
      self.distanceArray = [None] * self.numberOfFiducials  # create an array to store the distance of each fiducial point from point (0,0)
      self.distanceArrayCreated = 1

    if self.nodeCreated < 1: # make sure to only create one node
      self.fiducialMarker(xcoordinate,ycoordinate,zcoordinate)
      self.nodeCreated = self.nodeCreated + 1
      distance = self.calculateDistance(xcoordinate,ycoordinate)  # compute the distance of each fiducial from the point (0,0)
      self.distanceArray[0] = distance #  Store the first value in the first position in the array
    else:
      self.addToCurrentNode(xcoordinate, ycoordinate, zcoordinate) # add fiducials to existing node
      self.numberOfFiducials = self.numberOfFiducials + 1
      distance = self.calculateDistance(xcoordinate,ycoordinate) #compute the distance of each fiducial from the point (0,0)
      #for i in xrange(1,9,1): #should be len(distanceArray)
      self.distanceArray[self.iterationVariable] = distance
      if self.iterationVariable < 27:
        self.iterationVariable = self.iterationVariable + 1 # continue storing distances in the array until enough fiducials have been collected for an accurate measurement
        #print(self.distanceArray)
      else:
        width = self.calculateMetric(self.distanceArray)
        surfaceArea = width * width
        print('Width is: %.2f' % width)
        print('SurfaceArea is: %.2f' % surfaceArea)

  def calculateMetric(self, distanceArray):
    maxDistance = max(distanceArray)
    minDistance = min(distanceArray)
    Width = maxDistance - minDistance
    return Width

  def fiducialMarker(self, xcoordinate, ycoordinate, zcoordinate):
    self.fiducialNode = slicer.vtkMRMLMarkupsFiducialNode()
    slicer.mrmlScene.AddNode(self.fiducialNode)
    self.fiducialNode.AddFiducial(xcoordinate,ycoordinate,zcoordinate)

  def addToCurrentNode(self, xcoordinate, ycoordinate, zcoordinate):
    self.fiducialNode.AddFiducial(xcoordinate, ycoordinate, zcoordinate)

  def calculateDistance(self, xcoordinate, ycoordinate):
    distance = math.sqrt((xcoordinate * xcoordinate) + (ycoordinate * ycoordinate))
    return distance
  #
  # function written for testing and understanding spectral data acquisition
  def testFunc(self ,outputArrayNode):
    # Used to access specific wavelengths and intensitys of different data points
    self.outputArrayNode = outputArrayNode
    pointsArray = self.outputArrayNode.GetArray()
    # point contains a wavelength and a corresponding intensity
    # each data point has 2 rows of data, one corresponding to wavelength and one corresponding to intensity
    self.componentIndexWavelength = 0
    self.componentIndexIntensity = 1

    numberOfPoints = pointsArray.GetNumberOfTuples()  # access the number of points received from the spectra
    print(numberOfPoints)
    #for pointIndex in xrange(60,80): #loop through the 60th - 80th data points
    wavelengthValue = pointsArray.GetComponent(62, 0)  # checks the 187th point in the data stream, corresponds to the 650-700 nm wavelength (area of interest)
    intensityValue = pointsArray.GetComponent(62, 1)
    print(intensityValue)
    print(wavelengthValue)


  def home(self):
    # Return to home axis
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G28 X Y ')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, self.serialIGTLNode.GetID())

  def emergencyStop(self):
    # Writes to the printer to automatically stop all motors
    # Requires reboot
    self.printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    self.printerCmd.SetCommandName('SendText')
    self.printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    self.printerCmd.SetCommandTimeoutSec(1.0)
    self.printerCmd.SetCommandAttribute('Text', 'M112')
    slicer.modules.openigtlinkremote.logic().SendCommand(self.printerCmd, self.serialIGTLNode.GetID())
    self.printerCmd.AddObserver(self.printerCmd.CommandCompletedEvent, self.onPrinterCommandCompleted)

  def xLoop(self, timeValue, xResolution):
    # it takes 50000 seconds for the x to go back and forth once at a resolution of 10 mm per step

    lengthOfOneWidth = 25 * timeValue
    for xCoordinateValue in xrange(0,24*lengthOfOneWidth, lengthOfOneWidth): # 24 for the amount of times x must oscillate back and forth (eventually will be 120 / y resolution
      self.xWidthForward(xCoordinateValue, timeValue, xResolution)
      self.xWidthBackwards(xCoordinateValue, timeValue, xResolution)

  def yLoop(self, timeDelayMs):
    # y delay is increasing in alternating intervals therefore there are 2 for loops at alternating coordinates and times
    for yValue in xrange(5,120,10):
      #TODO: fix this interval (doesn't work sometimes)
      delayMs = (yValue-5)*2500 + 14*timeDelayMs # interval for y movement on righthand side of bed, will be 120/ xresolution * 14 * time value
      self.yMovement(delayMs,yValue)
    for yValue2 in xrange(10,120,10):
      delayMs2 = (yValue2-10)*2500 + 26*timeDelayMs # interval for y movement on lefthand side of bed, will be 120/ x resolution * 26 * time value
      self.yMovement(delayMs2, yValue2)

  def xWidthForward(self, xCoordinate, timeValue, xResolution): #used to be passed xCoordinate
    # Move the width of the bed forward in the positive x direction
    # Corresponds to a timer called in printer interactor widget
    self.scanTimer = qt.QTimer()
    for xValue in xrange(0,120,xResolution): # increment by 10 until 120
      delayMs  = xCoordinate + xValue*(timeValue/10) + timeValue
      self.XMovement(delayMs, xValue)


  def xWidthBackwards(self, xCoordinate, timeValue, xResolution):
    # Move the width of the bed backwards in the negative x direction
    # Corresponds to a timer called in printer interactor widget
    self.scanTimer = qt.QTimer()
    for xValue in xrange(120,0,-xResolution):
      delayMs = abs(xValue-120)* (timeValue/10) +13*timeValue + xCoordinate
      self.XMovement(delayMs, xValue)


  def yMovement(self, timevar, movevar):
    self.randomScanTimer = qt.QTimer()
    self.randomScanTimer.singleShot(timevar, lambda: self.controlledYMovement(movevar))

  def XMovement(self,timevar, movevar):
    self.randomScanTimer = qt.QTimer()
    self.randomScanTimer.singleShot(timevar, lambda: self.controlledXMovement(movevar))


  def controlledXMovement(self, xCoordinate): # x movement
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X%d' % (xCoordinate))
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, self.serialIGTLNode.GetID())

  def controlledYMovement(self, yCoordinate): # y movement
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y%d' % (yCoordinate))
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, self.serialIGTLNode.GetID())


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

    for url,name,loader in downloads:
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
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')