import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging

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
    self.stopButton = qt.QPushButton("STOP")
    self.stopButton.toolTip = "stop scan."
    self.stopButton.enabled = True
    connect_to_printerFormLayout.addRow(self.stopButton)
    self.stopButton.connect('clicked(bool)', self.onStopButton)
    #
    #Move z button
    #
    self.zButton = qt.QPushButton("Z50")
    self.zButton.toolTip = "stop scan."
    self.zButton.enabled = True
    connect_to_printerFormLayout.addRow(self.zButton)
    self.zButton.connect('clicked(bool)', self.onZButton)
    #
    # Get coordinates button
    #
    self.coordinateButton = qt.QPushButton("Get coordinates")
    self.coordinateButton.toolTip = "stop scan."
    self.coordinateButton.enabled = True
    connect_to_printerFormLayout.addRow(self.coordinateButton)
    self.coordinateButton.connect('clicked(bool)', self.onCoordinateButton)
    # Add vertical spacer
    #
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

  def onScanButton(self, enable):
    self.onSerialIGLTSelectorChanged()
    self.logic.surfaceScan()


  def onStopButton(self):#SerialIGTLNode):
    self.onSerialIGLTSelectorChanged()
    self.logic.stop()

  def onTumorButton(self ):
    self.ondoubleArrayNodeChanged()
    self.logic.tumorDetection(self.outputArraySelector.currentNode())

  def onZButton(self):
    self.onSerialIGLTSelectorChanged()
    self.logic.move_z_motor()

  def onCoordinateButton(self):
    self.onSerialIGLTSelectorChanged()
    self.logic.get_coordinates()
    #self.printerCmd.AddObserver(printerCmd.CommandCompletedEvent, onPrinterCmdCompleted)



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
    global stopPressed
    stopPressed = False

  def setSerialIGTLNode(self, serialIGTLNode):
    self.serialIGTLNode = serialIGTLNode

  def setdoubleArrayNode(self, doubleArrayNode):
    self.doubleArrayNode = doubleArrayNode

  #def addPrinterObserver(self):
    #printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    #printerCmd.AddObserver(printerCmd.CommandCompletedEvent, self.onPrinterCommandCompleted(0,0))


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

  def updateOutputArray(self):

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
    #if not self.outputArrayNode:
      #print "no output array"

    #self.updateOutputArray()
      #print(outputArrayNode)
    self.outputArrayNode = outputArrayNode
    pointsArray = self.outputArrayNode.GetArray()
    # point contains a wavelength and a corresponding intensity

    self.componentIndexWavelength = 0
    self.componentIndexIntensity = 1

    numberOfPoints = pointsArray.GetNumberOfTuples()
    #print numberOfPoints
    #for pointIndex in xrange(30,numberOfPoints): # use to be number of points
    for pointIndex in xrange(187,188):
      wavelengthValue = pointsArray.GetComponent(0,pointIndex)
      intensityValue = pointsArray.GetComponent(1, pointIndex)
      #print(intensityValue)
      print(wavelengthValue)
      if intensityValue == 1:
        print "Healthy"
      else:
        print "Tumor"

  def stop(self):
    global stopPressed
    stopPressed = True

  def move_z_motor(self):
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Z50')
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

  def checkIfStopPressed(self):
    if stopPressed == True:
      self.printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
      self.printerCmd.SetCommandName('SendText')
      self.printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
      self.printerCmd.SetCommandTimeoutSec(1.0)
      self.printerCmd.SetCommandAttribute('Text', 'M112')
      slicer.modules.openigtlinkremote.logic().SendCommand(self.printerCmd, self.serialIGTLNode.GetID())
    else:
      return


  def surfaceScan(self):
    for y_value in range(0,110,5):
      for x_value in range(10, 120, 50):
        self.printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
        self.printerCmd.SetCommandName('SendText')
        self.printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
        self.printerCmd.SetCommandTimeoutSec(0.01)
        self.printerCmd.SetCommandAttribute('Text', 'G1 X%d Y%d' % (x_value, y_value))
        slicer.modules.openigtlinkremote.logic().SendCommand(self.printerCmd, self.serialIGTLNode.GetID())
        self.checkIfStopPressed()








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
