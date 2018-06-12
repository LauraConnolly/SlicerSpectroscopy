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
    # Tumor Button
    #
    self.tumorButton = qt.QPushButton("Tumor?")
    self.tumorButton.toolTip = "Run the algorithm"
    self.tumorButton.enabled = True
    connect_to_printerFormLayout.addRow(self.tumorButton)
    self.tumorButton.connect('clicked(bool)', self.onTumorButton)
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
    self.logic.xLoop(self.timeValue, xResolution, yResolution) # calls a loop to toggle printer back and forth in the x direction
    self.logic.yLoop(self.timeValue, yResolution, xResolution) # calls a loop to increment the printer back in the y direction

    # tissue analysis
    self.tumorTimer = qt.QTimer()
    self.iterationTimingValue = 0
    stopsToVisitX = 120 / xResolution
    stopsToVisitY = 120/ yResolution
    for self.iterationTimingValue in range(0,(stopsToVisitX*stopsToVisitY*self.timeValue) + self.timeValue,self.timeValue): # 300 can be changed to x resolution by y resolution
      self.tumorTimer.singleShot(self.iterationTimingValue, lambda: self.tissueDecision())
      self.iterationTimingValue = self.iterationTimingValue + self.timeValue # COMMENT OUT MAYBE!


  def onTumorButton(self):
    self.onSerialIGLTSelectorChanged()
    self.logic.tumorDetection(self.outputArraySelector.currentNode())

  def onStopButton(self):
    self.onSerialIGLTSelectorChanged()
    self.logic.emergencyStop()




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

    #
    self.timePerXWidth = 26.5




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
      print "Healthy " # uncertain measurements, typically occur outside of tumor range
      return



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
    xcoordinate = float(xvalues[1])

    # Parse string for y coordinate value
    yvalues = mylist[1].split(":")
    ycoordinate = float(yvalues[1])

    # Parse string for z coordinate value
    zvalues = mylist[2].split(":")
    zcoordinate = float(zvalues[1])

    # Create 1 distance array to store distances from origin in order to determine the width of the specimen and the approximate surface area

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
      if self.iterationVariable < 27: # change to appropriate number of fiducials for accurate measurement
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

    slicer.modules.openigtlinkremote.logic().SendCommand(self.homeCmd, self.serialIGTLNode.GetID())

  def emergencyStop(self):
    # Writes to the printer to automatically stop all motors
    # Requires reboot
    slicer.modules.openigtlinkremote.logic().SendCommand(self.emergStopCmd, self.serialIGTLNode.GetID())
    self.emergStopCmd.AddObserver(self.emergStopCmd.CommandCompletedEvent, self.onPrinterCommandCompleted)



  def yLoop(self, timeValue, yResolution, xResolution):
    # specific intervals correspond to timeValues divisible by 1000
    # The variances in intervals were timed specifically to account for mechanical delays with the printer
    firstDistance = (120/ xResolution)
    secondDistance = 2*(120/ xResolution)
    self.yMovement((firstDistance+ 2)*timeValue, yResolution)
    self.yMovement((secondDistance+1)*timeValue, yResolution*2)
    self.i=0
    self.j=0
    for yValue in xrange(yResolution*3,120+yResolution, yResolution*2):
      delayMs = (((secondDistance + firstDistance)+ 2)*timeValue) + ((secondDistance*timeValue)*(self.i))
      self.yMovement(delayMs, yValue)
      self.i= self.i+1
    for yValue in xrange(yResolution*4, 120 + yResolution, yResolution*2):
      delayMs = ((((2*secondDistance)+1))*timeValue) + ((secondDistance*timeValue)*(self.j))
      self.yMovement(delayMs, yValue)
      self.j=self.j + 1

# Fix this so that it moves every 2 seconds not 1 second
  
  def xLoop(self, timeValue, xResolution, yResolution):
    # necessary for looping the x commands on static intervals
    oscillatingTime = (120 / yResolution)/2 # determines how many times the scanner should oscillate back and forth
    lengthOfOneWidth = ((120/ xResolution)*2) * timeValue
    #lengthOfOneWidth = 25 * timeValue # the amount of movements per oscillation back and forth
    for xCoordinateValue in xrange(0,(oscillatingTime*lengthOfOneWidth) + lengthOfOneWidth, lengthOfOneWidth): # calls forwards and backwards as necessary
      self.xWidthForward(xCoordinateValue, timeValue, xResolution)
      self.xWidthBackwards(xCoordinateValue, timeValue, xResolution)

  def xWidthForward(self, xCoordinate, timeValue, xResolution): #used to be passed xCoordinate
    # Move the width of the bed forward in the positive x direction
    # Corresponds to a timer called in printer interactor widget
    self.scanTimer = qt.QTimer()
    for xValue in xrange(0,120,xResolution): # increment by 10 until 120
      delayMs = xCoordinate + xValue * (timeValue / xResolution) # xCoordinate ensures the clocks are starting at correct times and xValue * (timeValue / 10 ) increments according to delay
      self.XMovement(delayMs, xValue)


  def xWidthBackwards(self, xCoordinate, timeValue, xResolution):
    # Move the width of the bed backwards in the negative x direction
    # Corresponds to a timer called in printer interactor widget
    self.scanTimer = qt.QTimer()
    for xValue in xrange(120,0,-xResolution):
      delayMs = abs(xValue-120)* (timeValue/xResolution) +(120/xResolution +1)*timeValue + xCoordinate # same principle as xWidth forwards but with abs value to account for decrementing values and 13*time value to offset starting interval
      self.XMovement(delayMs, xValue)


# Movement Controls (single shot, lambda timers for simple G Code message sending)

  def yMovement(self, timeValue, yResolution):
    self.randomScanTimer = qt.QTimer()
    self.randomScanTimer.singleShot(timeValue, lambda: self.controlledYMovement(yResolution))

  def XMovement(self,timevar, movevar):
    self.randomScanTimer = qt.QTimer()
    self.randomScanTimer.singleShot(timevar, lambda: self.controlledXMovement(movevar))


  def controlledXMovement(self, xCoordinate): # x movement
    self.xControlCmd.SetCommandAttribute('Text', 'G1 X%d' % (xCoordinate))
    slicer.modules.openigtlinkremote.logic().SendCommand(self.xControlCmd, self.serialIGTLNode.GetID())

  def controlledYMovement(self, yCoordinate): # y movement
    self.yControlCmd.SetCommandAttribute('Text', 'G1 Y%d' % (yCoordinate))
    slicer.modules.openigtlinkremote.logic().SendCommand(self.yControlCmd, self.serialIGTLNode.GetID())


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