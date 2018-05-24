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
  #x = 0
  stopButtonPressed = False


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

    # Home Button

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

    #Port Selector

    self.portSelector = qt.QComboBox()
    self.portSelector.insertItem(1, "PORT 1")
    self.portSelector.insertItem(2, "PORT 2")
    self.portSelector.insertItem(3, "PORT 3")
    self.portSelector.insertItem(4, "PORT 4")
    connect_to_printerFormLayout.addRow("Port :", self.portSelector)

    #input array selector

    # input volume selector
    #
    self.spectrumImageSelector = slicer.qMRMLNodeComboBox()
    self.spectrumImageSelector.nodeTypes = (("vtkMRMLScalarVolumeNode"), "")
    self.spectrumImageSelector.selectNodeUponCreation = True
    self.spectrumImageSelector.addEnabled = False
    self.spectrumImageSelector.removeEnabled = False
    self.spectrumImageSelector.noneEnabled = False
    self.spectrumImageSelector.showHidden = False
    self.spectrumImageSelector.showChildNodeTypes = False
    self.spectrumImageSelector.setMRMLScene(slicer.mrmlScene)
    self.spectrumImageSelector.setToolTip("Pick the spectrum image to visualize.")
    connect_to_printerFormLayout.addRow("Input spectrum image: ", self.spectrumImageSelector)

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

    self.enablePlottingCheckBox = qt.QCheckBox()
    self.enablePlottingCheckBox.checked = 0
    self.enablePlottingCheckBox.setToolTip("If checked, then the spectrum plot will be updated in real-time")
    connect_to_printerFormLayout.addRow("Enable plotting", self.enablePlottingCheckBox)

    # connections
    self.enablePlottingCheckBox.connect('stateChanged(int)', self.setEnablePlotting)

    #X Y Z input

    #self.x_spinbox = qt.QSpinBox()
    #self.x_spinbox.setMinimum(0)
    #self.x_spinbox.setMaximum(120)
    #self.x_spinbox.setValue(0)
    #connect_to_printerFormLayout.addRow("X Pos (mm): ", self.x_spinbox)

    #self.y_spinbox = qt.QSpinBox()
   #self.y_spinbox.setMinimum(0)
    #self.y_spinbox.setMaximum(120)
   # self.y_spinbox.setValue(0)
    #connect_to_printerFormLayout.addRow("Y Pos (mm): ", self.y_spinbox)

    #self.z_spinbox = qt.QSpinBox()
   # self.z_spinbox.setMinimum(0)
    #self.z_spinbox.setMaximum(120)
    #self.z_spinbox.setValue(0)
    #connect_to_printerFormLayout.addRow("Z Pos (mm): ", self.z_spinbox)

    # Tumor distinction button

    self.tumorButton = qt.QPushButton("Tumor?")
    self.tumorButton.toolTip = "Run the algorithm"
    self.tumorButton.enabled = True
    connect_to_printerFormLayout.addRow(self.tumorButton)
    self.tumorButton.connect('clicked(bool)', self.onTumorButton)

    # Apply Button

   # self.applyButton = qt.QPushButton("Apply")
    #self.applyButton.toolTip = "Run the algorithm."
    #self.applyButton.enabled = True
    #connect_to_printerFormLayout.addRow(self.applyButton)
    # connections
    #self.applyButton.connect('clicked(bool)', self.onApplyButton)

    # Surface scan button

    self.scanButton = qt.QPushButton("Scan Surface")
    self.scanButton.toolTip = "Begin 2D surface scan"
    self.scanButton.enabled = True
    connect_to_printerFormLayout.addRow(self.scanButton)
    self.scanButton.connect('clicked(bool)', self.onScanButton)

    #stop button
    self.stopButton = qt.QPushButton("STOP")
    self.stopButton.toolTip = "stop scan."
    self.stopButton.enabled = True
    connect_to_printerFormLayout.addRow(self.stopButton)
    self.scanButton.connect('clicked(bool)', self.onStopButton)

    # Add vertical spacer
    self.layout.addStretch(1)

  def setEnablePlotting(self, enable):

    if enable:
      self.logic.startPlotting(self.spectrumImageSelector.currentNode(), self.outputArraySelector.currentNode())
    else:
      self.logic.stopPlotting()

  def cleanup(self):
    pass

  def onApplyButton(self):

    logic = PrinterInteractorLogic()
    port = self.portSelector.currentIndex + 1 # port is 1 greater than index
    x_value = self.x_spinbox.value
    y_value = self.y_spinbox.value
    z_value = self.z_spinbox.value
    igtl = self.inputSelector.currentNode()
    logic.run(igtl, port, x_value, y_value, z_value)

  def onHomeButton(self):
    logic = PrinterInteractorLogic()
    igtl = self.inputSelector.currentNode()
    logic.home(igtl)

  def onScanButton(self):
    logic = PrinterInteractorLogic()
    igtl = self.inputSelector.currentNode()
    if self.stopButtonPressed != True:
      logic.surfaceScan(igtl)
    else:
      logic.stop(igtl)

  def onStopButton(self):
    logic = PrinterInteractorLogic()
    igtl = self.inputSelector.currentNode()
    self.stopButtonPressed = True
    logic.stop(igtl)
    logic.home(igtl)

  def onTumorButton(self):
    logic = PrinterInteractorLogic()
    igtl = self.inputSelector.currentNode()

    logic.tumorDetection()


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
  #flagvariable = 0
  def __init__(self):
    self.baud_rate = 115200
    self.flagvariable = False

    self.chartNodeID = None

    self.spectrumImageNode = None
    self.observerTags = []
    self.outputArrayNode = None
    self.resolution = 100

  #def connect(self):
    #if self.flagvariable:
      #self.connectorNode = slicer.vtkMRMLIGTLConnectorNode()
      #self.connectorNode.SetTypeClient('127.0.0.1', 18944)
      #self.slicer.mrmlScene.AddNode(connectorNode)
      #self.connectorNode.Start()
      #self.flagvariable = False

  def addObservers(self):
    if self.spectrumImageNode:
      print "Add observer to {0}".format(self.spectrumImageNode.GetName())
      self.observerTags.append([self.spectrumImageNode, self.spectrumImageNode.AddObserver(vtk.vtkCommand.ModifiedEvent,
                                                                                           self.onSpectrumImageNodeModified)])
  def removeObservers(self):
    print "Remove observers"
    for nodeTagPair in self.observerTags:
      nodeTagPair[0].RemoveObserver(nodeTagPair[1])

  def home(self,igtl):
    #Return to home axis
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X0 Y0 Z40 ')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())


  def startPlotting(self, spectrumImageNode, outputArrayNode):
    # Change the layout to one that has a chart.  This created the ChartView
    ln = slicer.util.getNode(pattern='vtkMRMLLayoutNode*')
    ln.SetViewArrangement(24)

    self.removeObservers()
    self.spectrumImageNode = spectrumImageNode
    self.outputArrayNode = outputArrayNode

    # Start the updates
    self.addObservers()
    self.onSpectrumImageNodeModified(0, 0)

  def stopPlotting(self):
    self.removeObservers()

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

  def tumorDetection(self):


    if not self.spectrumImageNode or not self.outputArrayNode:
      return

      self.updateOutputArray()
    #self.outputArrayNode = outputArrayNode
    pointsArray = self.outputArrayNode.GetArray()
    # point contains a wavelength and a corresponding intensity

    componentIndexWavelength = 0
    componentIndexIntensity = 1

    numberOfPoints = pointsArray.GetNumberOfTuples()

    for pointIndex in xrange(numberOfPoints):
      wavelengthValue = pointsArray.GetComponent(0,pointIndex)
      intensityValue = pointsArray.GetComponent(1, pointIndex)
      while(wavelengthValue >700 and intensityValue < 1):
        print "Tumor"





      #greenValue = a.GetValue(700, row, probedPointScalars.GetTuple(700)[0])
      #if ( greenValue >= 0 and greenValue <= 1 ):
        #print('Tumor')

  def updateChart(self):

    # Get the first ChartView node
    cvn = slicer.util.getNode(pattern='vtkMRMLChartViewNode*')

    # If we already created a chart node and it is still exists then reuse that
    cn = None
    if self.chartNodeID:
      cn = slicer.mrmlScene.GetNodeByID(cvn.GetChartNodeID())
    if not cn:
      cn = slicer.mrmlScene.AddNode(slicer.vtkMRMLChartNode())
      self.chartNodeID = cn.GetID()
      # Configure properties of the Chart
      cn.SetProperty('default', 'title', 'Spectrum')
      cn.SetProperty('default', 'xAxisLabel', 'Wavelength (nm)')
      cn.SetProperty('default', 'yAxisLabel', 'Intensity')

    name = self.spectrumImageNode.GetName()
    cn.AddArray(name, self.outputArrayNode.GetID())

    # Set the chart to display
    cvn.SetChartNodeID(cn.GetID())
    cvn.Modified()

  def stop(self, igtl):
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'M0')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())

  def surfaceScan(self,igtl):
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X60')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X110')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y5')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X60')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X0')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y10')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X60')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X110')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y15')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X60')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X0')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y20')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X60')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X110')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y25')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X60')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X0')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y30')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X60')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X110')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y35')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X60')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X0')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y40')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X60')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X110')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y45')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X60')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X0')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y50')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X60')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X110')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y55')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X60')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X0')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y60')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X60')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X110')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y65')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X60')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X0')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y70')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X60')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X110')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y75')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X60')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X0')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y80')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X60')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X110')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y85')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X60')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X0')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y90')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X60')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X110')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y95')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X60')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X0')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y100')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X60')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X110')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y105')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X60')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X0')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 Y110')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X0 Y0 Z40')
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())




  def run(self, igtl, port, x_value=0, y_value=0, z_value=0):
    #Connect to the printer
    printerCmd = slicer.vtkSlicerOpenIGTLinkCommand()
    printerCmd.SetCommandName('SendText')
    printerCmd.SetCommandAttribute('DeviceId', "SerialDevice")
    printerCmd.SetCommandTimeoutSec(1.0)
    printerCmd.SetCommandAttribute('Text', 'G1 X%d Y%d Z%d' % (x_value,y_value,z_value))
    slicer.modules.openigtlinkremote.logic().SendCommand(printerCmd, igtl.GetID())

    #print x_value
    #print y
    #print z
    #print port
    logging.info('Processing completed')

    return True


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
