import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import time
import functools

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
This is an module developed to interface Slicer Software with the Monoprice Mini V2 3D Printer 
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
    self.tumorButton = qt.QPushButton("Tumor?")
    self.tumorButton.toolTip = "Run the algorithm"
    self.tumorButton.enabled = True
    connect_to_printerFormLayout.addRow(self.tumorButton)
    self.tumorButton.connect('clicked(bool)', self.onTumorButton)
    #
    #
    # Automated tumor detect
    #
    self.tumorDetectOn = qt.QPushButton("Analyze Tissue")
    self.tumorDetectOn.toolTip = "Receive tissue analysis for 10 seconds"
    self.tumorDetectOn.enabled = True
    connect_to_printerFormLayout.addRow(self.tumorDetectOn)
    self.tumorDetectOn.connect('clicked(bool)', self.onTumorDetectOn)
    #
    # Surface scan button
    #
    self.scanButton = qt.QPushButton("Systematic Scan")
    self.scanButton.toolTip = "Begin 2D surface scan"
    self.scanButton.enabled = True
    connect_to_printerFormLayout.addRow(self.scanButton)
    self.scanButton.connect('clicked(bool)', self.onScanButton)
    #
    #Short scan button
    #
    self.shortScanButton = qt.QPushButton("Short Scan")
    self.shortScanButton.toolTip = "Short scan."
    self.shortScanButton.enabled = True
    connect_to_printerFormLayout.addRow(self.shortScanButton)
    self.shortScanButton.connect('clicked(bool)', self.onShortScanButton)
    #
    # Stop button
    #
    self.stopButton = qt.QPushButton("EMERGENCY STOP")
    self.stopButton.toolTip = "Immediately stop printer motors, requires restart."
    self.stopButton.enabled = True
    connect_to_printerFormLayout.addRow(self.stopButton)
    self.stopButton.connect('clicked(bool)', self.onStopButton)
    #

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
    self.timerTimer = qt.QTimer()

    self.logic.xWidthForward(0)
    self.logic.yBackwards(26000,10)
    self.logic.xWidthBackwards(0)
    self.logic.yBackwards(54000,20)
    self.logic.xWidthForward(54000)
    self.logic.yBackwards(80000,30)
    self.logic.xWidthBackwards(54000)
    self.logic.yBackwards(106000,40)
    self.logic.xWidthForward(106000)
    self.logic.yBackwards(132000,50)
    self.logic.xWidthBackwards(106000)
    self.logic.yBackwards(158000,60)
    self.logic.xWidthForward(158000)
    self.logic.yBackwards(184000,70)
    self.logic.xWidthBackwards(158000)
    self.logic.yBackwards(210000,80)
    self.logic.xWidthForward(210000)
    self.logic.yBackwards(236000,90)
    self.logic.xWidthBackwards(210000)
    self.logic.yBackwards(262000,100)
    self.logic.xWidthForward(262000)
    self.logic.yBackwards(288000,110)
    self.logic.xWidthBackwards(262000)
    self.logic.yBackwards(314000,120)
    self.logic.xWidthForward(314000)

    # tissue analysis
    self.tumorTimer = qt.QTimer()

    self.timeValue = 0
    for self.timeValue in xrange(0,330000,2000):
      self.tumorTimer.singleShot(self.timeValue, lambda: self.logic.get_coordinates())
      self.tumorTimer.singleShot(self.timeValue, lambda: self.logic.tumorDetection(self.outputArraySelector.currentNode()))
      self.timeValue = self.timeValue + 2000


  def onStopButton(self):#SerialIGTLNode):
    self.onSerialIGLTSelectorChanged()
    self.logic.emergencyStop()


  def onTumorButton(self):
    self.ondoubleArrayNodeChanged()
    self.onSerialIGLTSelectorChanged()
    self.logic.tumorDetection(self.outputArraySelector.currentNode())
    self.logic.get_coordinates()


  def onShortScanButton(self):
    self.onSerialIGLTSelectorChanged()
    self.logic.shortScan()


  def onTumorDetectOn(self):
    self.ondoubleArrayNodeChanged()
    self.onSerialIGLTSelectorChanged()
    self.tumorTimer = qt.QTimer()
    #self.tumorTimer.timeout.connect(self.logic.get_coordinates)
    #self.tumorTimer.start(2000)

    self.timeValue = 0
    for self.timeValue in xrange(0,10000,2000):
      self.tumorTimer.singleShot(self.timeValue, lambda: self.logic.get_coordinates())
      self.tumorTimer.singleShot(self.timeValue, lambda: self.logic.tumorDetection(self.outputArraySelector.currentNode()))
      self.timeValue = self.timeValue + 2000






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

    # Timer stuff


  def setSerialIGTLNode(self, serialIGTLNode):
    self.serialIGTLNode = serialIGTLNode

  def setdoubleArrayNode(self, doubleArrayNode):
    self.doubleArrayNode = doubleArrayNode

  #def addPrinterObserver(self):
    #printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    #printerCmd.AddObserver(printerCmd.CommandCompletedEvent, self.onPrinterCommandCompleted(0,0))

  def tick(self):
    print "tick"


  def addObservers(self):
    if self.spectrumImageNode:
      print "Add observer to {0}".format(self.spectrumImageNode.GetName())
      self.observerTags.append([self.spectrumImageNode, self.spectrumImageNode.AddObserver(vtk.vtkCommand.ModifiedEvent,
                                                                                           self.onSpectrumImageNodeModified)])
  def removeObservers(self):
    print "Remove observers"
    for nodeTagPair in self.observerTags:
      nodeTagPair[0].RemoveObserver(nodeTagPair[1])

  def home(self):
    #Return to home axis
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G28 X Y ')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, self.serialIGTLNode.GetID())

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

    self.componentIndexWavelength = 0
    self.componentIndexIntensity = 1

    numberOfPoints = pointsArray.GetNumberOfTuples()
    #for pointIndex in xrange(numberOfPoints):
    wavelengthValue = pointsArray.GetComponent(0,187)
    intensityValue = pointsArray.GetComponent(1, 187)
    #print(intensityValue)
    #print(wavelengthValue)
    if intensityValue == 1:
      print "Healthy"

    else:
      print "Tumor"





  def shortScan(self):
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X110 Y110')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, self.serialIGTLNode.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X0 Y0')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, self.serialIGTLNode.GetID())

  def get_coordinates(self):
    self.printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    self.printerCmd.SetCommandName('SendText')
    self.printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    self.printerCmd.SetCommandTimeoutSec(1.0)
    self.printerCmd.SetCommandAttribute('Text', 'M114')
    slicer.modules.openigtlinkremote.logic().SendCommand(self.printerCmd, self.serialIGTLNode.GetID())
    self.printerCmd.AddObserver(self.printerCmd.CommandCompletedEvent, self.onPrinterCommandCompleted)

  def onPrinterCommandCompleted(self, observer, eventid):
    print("Command completed with status: " + self.printerCmd.StatusToString(self.printerCmd.GetStatus()))
    print("Response message: " + self.printerCmd.GetResponseMessage())
    print("Full response: " + self.printerCmd.GetResponseText())

  def emergencyStop(self):
    self.printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    self.printerCmd.SetCommandName('SendText')
    self.printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    self.printerCmd.SetCommandTimeoutSec(1.0)
    self.printerCmd.SetCommandAttribute('Text', 'M112')
    slicer.modules.openigtlinkremote.logic().SendCommand(self.printerCmd, self.serialIGTLNode.GetID())
    self.printerCmd.AddObserver(self.printerCmd.CommandCompletedEvent, self.onPrinterCommandCompleted)


  def xWidthForward(self, xvar):
    self.scanTimer = qt.QTimer()
    self.scanTimer.singleShot(xvar + 2000, lambda: self.controlledMovement(10))
    self.scanTimer.singleShot(xvar + 4000, lambda: self.controlledMovement(20))
    self.scanTimer.singleShot(xvar + 6000, lambda: self.controlledMovement(30))
    self.scanTimer.singleShot(xvar + 8000, lambda: self.controlledMovement(40))
    self.scanTimer.singleShot(xvar + 10000, lambda: self.controlledMovement(50))
    self.scanTimer.singleShot(xvar + 12000, lambda: self.controlledMovement(60))
    self.scanTimer.singleShot(xvar + 14000, lambda: self.controlledMovement(70))
    self.scanTimer.singleShot(xvar + 16000, lambda: self.controlledMovement(80))
    self.scanTimer.singleShot(xvar +18000, lambda: self.controlledMovement(90))
    self.scanTimer.singleShot(xvar +20000, lambda: self.controlledMovement(100))
    self.scanTimer.singleShot(xvar + 22000, lambda: self.controlledMovement(110))
    self.scanTimer.singleShot(xvar + 24000, lambda: self.controlledMovement(120))

  def xWidthBackwards(self, xvar):
    self.scanTimer = qt.QTimer()
    self.scanTimer.singleShot(xvar + 26000, lambda: self.controlledMovement(120))
    self.scanTimer.singleShot(xvar +28000, lambda: self.controlledMovement(110))
    self.scanTimer.singleShot(xvar + 30000, lambda: self.controlledMovement(100))
    self.scanTimer.singleShot(xvar + 32000, lambda: self.controlledMovement(90))
    self.scanTimer.singleShot(xvar + 34000, lambda: self.controlledMovement(80))
    self.scanTimer.singleShot(xvar + 36000, lambda: self.controlledMovement(70))
    self.scanTimer.singleShot(xvar + 38000, lambda: self.controlledMovement(60))
    self.scanTimer.singleShot(xvar + 40000, lambda: self.controlledMovement(50))
    self.scanTimer.singleShot(xvar + 42000, lambda: self.controlledMovement(40))
    self.scanTimer.singleShot(xvar + 44000, lambda: self.controlledMovement(30))
    self.scanTimer.singleShot(xvar + 46000, lambda: self.controlledMovement(20))
    self.scanTimer.singleShot(xvar + 48000, lambda: self.controlledMovement(10))
    self.scanTimer.singleShot(xvar + 50000, lambda: self.controlledMovement(0))

  def yBackwards(self, timevar, movevar):
    self.scanTimer = qt.QTimer()
    self.scanTimer.singleShot(timevar, lambda: self.controlledYMovement(movevar))

  def surfaceScan(self):
    self.timerTimer = qt.QTimer()
    for x,y in zip(range(2000,20000,2000), range(0,100,10)):
      self.timerTimer.singleShot(x, lambda: functools.partial(self.controlledMovement(y)))
      #x = x + 2000
      #y = y + 10
    #for y_value in xrange(0,120,5):
      #self.printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
      #self.printerCmd.SetCommandName('SendText')
      #self.printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
      #self.printerCmd.SetCommandTimeoutSec(0.01)
      #self.printerCmd.SetCommandAttribute('Text', 'G1 Y%d' % (y_value))
      #slicer.modules.openigtlinkremote.logic().SendCommand(self.printerCmd, self.serialIGTLNode.GetID())
      #for x_value in xrange(0,120,10):
      #  self.printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
       # self.printerCmd.SetCommandName('SendText')
       # self.printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
       # self.printerCmd.SetCommandTimeoutSec(0.01)
       #self.printerCmd.SetCommandAttribute('Text', 'G1 X%d' % (x_value))
        #slicer.modules.openigtlinkremote.logic().SendCommand(self.printerCmd, self.serialIGTLNode.GetID())

    #self.printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    #self.printerCmd.SetCommandName('SendText')
    #self.printerCmd.SetCommandTimeoutSec(0.01)
    #self.printerCmd.SetCommandAttribute('Text', 'G1 X0')
    #slicer.modules.openigtlinkremote.logic().SendCommand(self.printerCmd, self.serialIGTLNode.GetID())

    #for y_value in range(0,110,5):
      #for x_value in range(10, 120, 50):
        #self.printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
        #self.printerCmd.SetCommandName('SendText')
        #self.printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
        #self.printerCmd.SetCommandTimeoutSec(0.01)
        #self.printerCmd.SetCommandAttribute('Text', 'G1 X%d Y%d' % (x_value, y_value))
        #slicer.modules.openigtlinkremote.logic().SendCommand(self.printerCmd, self.serialIGTLNode.GetID())


  def controlledMovement(self, xvar):

    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X%d' % (xvar))
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, self.serialIGTLNode.GetID())

  def controlledYMovement(self, yvar):
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y%d' % (yvar))
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
