import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import time


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

    self.testButton = qt.QPushButton("test")
    self.testButton.toolTip = "Run the algorithm"
    self.testButton.enabled = True
    connect_to_printerFormLayout.addRow(self.testButton)
    self.testButton.connect('clicked(bool)', self.onTestButton)
    # Surface scan button
    #
    self.scanButton = qt.QPushButton("Scan Surface")
    self.scanButton.toolTip = "Begin 2D surface scan"
    self.scanButton.enabled = True
    connect_to_printerFormLayout.addRow(self.scanButton)
    self.scanButton.connect('clicked(bool)', self.onScanButton)

    #
    #Stop button
    #
    self.stopButton = qt.QPushButton("EMERGENCY STOP")
    self.stopButton.toolTip = "stop scan."
    self.stopButton.enabled = True
    connect_to_printerFormLayout.addRow(self.stopButton)
    self.stopButton.connect('clicked(bool)', self.onStopButton)

    #
    # Get coordinates button
    #
    self.coordinateButton = qt.QPushButton("Get coordinates")
    self.coordinateButton.toolTip = "stop scan."
    self.coordinateButton.enabled = True
    connect_to_printerFormLayout.addRow(self.coordinateButton)
    self.coordinateButton.connect('clicked(bool)', self.onCoordinateButton)
    #
    #Short scan button
    #
    self.shortScanButton = qt.QPushButton("Short Scan")
    self.shortScanButton.toolTip = "Short scan."
    self.shortScanButton.enabled = True
    connect_to_printerFormLayout.addRow(self.shortScanButton)
    self.shortScanButton.connect('clicked(bool)', self.onShortScanButton)
    #
    #
    # stop button
    self.stopTimerButton = qt.QPushButton("Stop Timer")
    self.stopTimerButton.toolTip = "stop timer."
    self.stopTimerButton.enabled = True
    connect_to_printerFormLayout.addRow(self.stopTimerButton)
    self.stopTimerButton.connect('clicked(bool)', self.onStopTimerButton)
    #
    # Automated tumor detect
    #
    self.tumorDetectOn = qt.QPushButton("Analyze Tissue")
    self.tumorDetectOn.toolTip = "Turn on tumor detection"
    self.tumorDetectOn.enabled = True
    connect_to_printerFormLayout.addRow(self.tumorDetectOn)
    self.tumorDetectOn.connect('clicked(bool)', self.onTumorDetectOn)
    #
    # Tumor detection off
    #
    self.tumorDetectOff = qt.QPushButton("Turn tumor detection off")
    self.tumorDetectOff.toolTip = "Turn off tumor detection"
    self.tumorDetectOff.enabled = True
    connect_to_printerFormLayout.addRow(self.tumorDetectOff)
    self.tumorDetectOff.connect('clicked(bool)', self.onTumorDetectOff)

    self.layout.addStretch(1)



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
    self.scanTimer = qt.QTimer()
    self.scanTime = 0
    self.xvar = 0
    for self.waiting in xrange(0,10,1):
      self.scanTimer.singleShot(self.scanTime, lambda: self.logic.controlledMovement(self.xvar))
      self.scanTime = self.scanTime + 2000
      self.xvar = self.xvar + 10
      self.waiting = self.waiting + 1

  def onStopButton(self):#SerialIGTLNode):
    self.onSerialIGLTSelectorChanged()
    self.logic.emergencyStop()

  def onTumorButton(self):
    self.ondoubleArrayNodeChanged()
    self.onSerialIGLTSelectorChanged()
    self.logic.tumorDetection(self.outputArraySelector.currentNode())
    self.logic.get_coordinates()


  def onCoordinateButton(self):
    self.onSerialIGLTSelectorChanged()
    self.logic.get_coordinates()
    #self.printerCmd.AddObserver(printerCmd.CommandCompletedEvent, onPrinterCmdCompleted)

  def onShortScanButton(self):
    self.onSerialIGLTSelectorChanged()
    self.logic.shortScan()

  def onTestButton(self):
    self.ondoubleArrayNodeChanged()
    self.onSerialIGLTSelectorChanged()

    self.Timer = qt.QTimer()
    #self.logic.tumorDetection(self.outputArraySelector.currentNode())
    #self.Timer.timeout.connect(self.logic.get_coordinates)
    #self.Timer.timeout.connect( (self.Timer.timeout()), (self.logic.tumorDetection(self.outputArraySelector.currentNode())))
    self.Timer.timeout.connect(self.logic.get_coordinates)
    self.Timer.start(2000)

  def onStopTimerButton(self):
    self.Timer.stop()

  def onTumorDetectOn(self):
    self.ondoubleArrayNodeChanged()
    self.onSerialIGLTSelectorChanged()
    self.tumorTimer = qt.QTimer()
    self.waitTime = 2000
    self.tumorTimer.timeout.connect(self.logic.get_coordinates)
    self.tumorTimer.start(2000)
    for waitLoop in xrange(0,10,1):
      self.tumorTimer.singleShot(self.waitTime, lambda: self.logic.tumorDetection(self.outputArraySelector.currentNode()))
      self.waitTime = self.waitTime + 2000
      waitLoop = waitLoop + 1
      #
  def onTumorDetectOff(self):
    self.tumorTimer.stop()





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
    printerCmd.SetCommandAttribute('Text', 'G1 X0 Y0 Z40 ')
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


  def surfaceScan(self):

    for y_value in xrange(0,120,5):
      self.printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
      self.printerCmd.SetCommandName('SendText')
      self.printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
      self.printerCmd.SetCommandTimeoutSec(0.01)
      self.printerCmd.SetCommandAttribute('Text', 'G1 Y%d' % (y_value))
      slicer.modules.openigtlinkremote.logic().SendCommand(self.printerCmd, self.serialIGTLNode.GetID())
      for x_value in xrange(0,120,10):
        self.printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
        self.printerCmd.SetCommandName('SendText')
        self.printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
        self.printerCmd.SetCommandTimeoutSec(0.01)
        self.printerCmd.SetCommandAttribute('Text', 'G1 X%d' % (x_value))
        slicer.modules.openigtlinkremote.logic().SendCommand(self.printerCmd, self.serialIGTLNode.GetID())

    self.printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    self.printerCmd.SetCommandName('SendText')
    self.printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    self.printerCmd.SetCommandTimeoutSec(0.01)
    self.printerCmd.SetCommandAttribute('Text', 'G1 X0')
    slicer.modules.openigtlinkremote.logic().SendCommand(self.printerCmd, self.serialIGTLNode.GetID())

    #for y_value in range(0,110,5):
      #for x_value in range(10, 120, 50):
        #self.printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
        #self.printerCmd.SetCommandName('SendText')
        #self.printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
        #self.printerCmd.SetCommandTimeoutSec(0.01)
        #self.printerCmd.SetCommandAttribute('Text', 'G1 X%d Y%d' % (x_value, y_value))
        #slicer.modules.openigtlinkremote.logic().SendCommand(self.printerCmd, self.serialIGTLNode.GetID())

  def xControl(self, x_value, node, doubleArrayNode):


    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X%d' % (x_value))
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, self.serialIGTLNode.GetID())


  def controlledMovement(self, xvar):

    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X%d' % (xvar))
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
