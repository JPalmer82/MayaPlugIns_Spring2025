from PySide2.QtGui import QColor, QPalette
import maya.cmds as mc # imports maya's cmd module so we can use it to run code in maya
import maya.mel as mel
from maya.OpenMaya import MVector

from PySide2.QtWidgets import (QLineEdit, 
                               QMainWindow, 
                               QMessageBox, 
                               QWidget, 
                               QVBoxLayout, 
                               QHBoxLayout, 
                               QLabel, 
                               QSlider,
                               QPushButton,
                               QColorDialog) # imports all of the widgets needed to build our ui 
from PySide2.QtCore import Qt # this has some values we can use to configure our widget, like our windowtype, or orientation

from MayaUtilities import QMayaWindow
    
class LimbRigger: # class where we define the different joints we will use
    def __init__(self):
        self.root = "" # gives the root joint an empty name to be used later
        self.mid = "" # gives the middle joint an empty name
        self.end = "" # gives the end joint an empty name
        self.controllerSize = 5 # initializes the controller size as 5

    def AutoFindJoints(self): # function to automatically find the root joint and it's child joints
        self.root = mc.ls(sl = True, type = "joint")[0] # finds the parent joint the user selects
        self.mid = mc.listRelatives(self.root, c = True, type = "joint")[0] # finds the joint parented underneath the root joint
        self.end = mc.listRelatives(self.mid, c = True, type = "joint")[0] # finds the joint parented underneath the mid joint

    def CreateFKControlForJoint(self, jointName): # function to create FK handle from a joint selection
        controlName = "ac_fk_" + jointName # takes the name of the joint and gives it a prefix for the controller
        controlGroupName = controlName + "_grp" # creates the group name for the new controller
        mc.circle(n = controlName, r = self.controllerSize, nr = (1, 0, 0)) # creates the controller and gives it a name and how big it is

        mc.group(controlName, n = controlGroupName) # groups the controller underneath it's grp
        mc.matchTransform(controlGroupName, jointName) # matches the transform of controller with the joint to align it
        mc.orientConstraint(controlName, jointName) # constrains the joint with the controller
        return controlName, controlGroupName # returns the new controller and it's group
    
    def CreateBoxController(self, name):
        mel.eval(f"curve -n {name} -d 1 -p -0.5 0.5 0.5 -p 0.5 0.5 0.5 -p 0.5 0.5 -0.5 -p -0.5 0.5 -0.5 -p -0.5 0.5 0.5 -p -0.5 -0.5 0.5 -p 0.5 -0.5 0.5 -p 0.5 0.5 0.5 -p 0.5 0.5 -0.5 -p 0.5 -0.5 -0.5 -p 0.5 -0.5 0.5 -p 0.5 -0.5 -0.5 -p -0.5 -0.5 -0.5 -p -0.5 0.5 -0.5 -p -0.5 -0.5 -0.5 -p -0.5 -0.5 0.5 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15 ;")
        mc.scale(self.controllerSize, self.controllerSize, self.controllerSize, name)
        mc.makeIdentity(name, apply = True) # this is freeze transformation

        grpName = name + "_grp"
        mc.group(name, n = grpName)
        return name, grpName
    
    def CreatePlusController(self, name):
        mel.eval(f"curve -n {name} -d 1 -p -15 4 0 -p -13 4 0 -p -13 6 0 -p -11 6 0 -p -11 8 0 -p -13 8 0 -p -13 10 0 -p -15 10 0 -p -15 8 0 -p -17 8 0 -p -17 6 0 -p -15 6 0 -p -15 4 0 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 ;")
        #mc.scale(self.controllerSize / 3, self.controllerSize / 3, self.controllerSize / 3)
        #mc.makeIdentity(name, apply = True) # this is freeze transformation

        grpName = name + "_grp"
        mc.group(name, n = grpName)
        return name, grpName

    def GetObjectLocation(self, objectName)->MVector:
        x, y, z = mc.xform(objectName, q = True, t = True, ws = True) # get the world space translation of the objectName
        return MVector(x, y, z)
    
    def PrintMVector(self, vectorToPrint):
        print(f"<{vectorToPrint.x}, {vectorToPrint.y}, {vectorToPrint.z}>")

    def RigLimb(self, r, g, b): # function to create the rig from the joints established before
        rootFKControl, rootFKControlGrp = self.CreateFKControlForJoint(self.root) # creates controller and it's group for the root joint
        midFKControl, midFKControlGrp = self.CreateFKControlForJoint(self.mid) # creates controller and it's group for the mid joint
        endFKControl, endFKControlGrp = self.CreateFKControlForJoint(self.end) # creates controller and it's group for the end joint

        mc.parent(midFKControlGrp, rootFKControl) # parents the grp for the mid joint control underneath the root control
        mc.parent(endFKControlGrp, midFKControl) # parents the grp for the end joint control underneath the mid control

        ikEndControl = "ac_ik_" + self.end
        ikEndControl, ikEndControlGrp = self.CreateBoxController(ikEndControl)
        mc.matchTransform(ikEndControlGrp, self.end)
        endOrientConstraint = mc.orientConstraint(ikEndControl, self.end)[0]

        rootJointLocation = self.GetObjectLocation(self.root)
        endJointLocation = self.GetObjectLocation(self.end)

        rootToEndVector = endJointLocation - rootJointLocation

        ikHandleName = "ikHandle_" + self.end
        mc.ikHandle(n = ikHandleName, sj = self.root, ee = self.end, sol = "ikRPsolver")
        ikPoleVectorValues = mc.getAttr(ikHandleName + ".poleVector")[0]
        ikPoleVector = MVector(ikPoleVectorValues[0], ikPoleVectorValues[1], ikPoleVectorValues[2])

        ikPoleVector.normalize()
        ikPoleVectorControlLocation = rootJointLocation + rootToEndVector / 2 + ikPoleVector * rootToEndVector.length()

        ikPoleVectorControlName = "ac_ik_" + self.mid
        mc.spaceLocator(n = ikPoleVectorControlName)
        ikPoleVectorControlGrp = ikPoleVectorControlName + "_grp"
        mc.group(ikPoleVectorControlName, n = ikPoleVectorControlGrp)
        mc.setAttr(ikPoleVectorControlGrp + ".t", ikPoleVectorControlLocation.x, ikPoleVectorControlLocation.y, ikPoleVectorControlLocation.z, typ = "double3")
        mc.poleVectorConstraint(ikPoleVectorControlName, ikHandleName)

        ikfkBlendControlName = "ac_ikfk_blend_" + self.mid
        ikfkBlendControlName, ikfkBlendControlGrp = self.CreatePlusController(ikfkBlendControlName)
        ikfkBlendControlLocation = rootJointLocation + MVector(rootJointLocation.x, 0, rootJointLocation.z)
        mc.setAttr(ikfkBlendControlGrp + ".t", ikfkBlendControlLocation.x, ikfkBlendControlLocation.y, ikfkBlendControlLocation.z, typ = "double3")

        ikfkBlendAttributeName = "ikfkBlend"
        mc.addAttr(ikfkBlendControlName, ln = ikfkBlendAttributeName, min = 0, max = 1, k = True)
        ikfkBlendAttribute = ikfkBlendControlName + "." + ikfkBlendAttributeName

        mc.expression(s = f"{ikHandleName}.ikBlend = {ikfkBlendAttribute}")
        mc.expression(s = f"{ikEndControlGrp}.v = {ikPoleVectorControlGrp}.v = {ikfkBlendAttribute}")
        mc.expression(s = f"{rootFKControlGrp}.v = 1 - {ikfkBlendAttribute}")
        mc.expression(s = f"{endOrientConstraint}.{endFKControl}W0 = 1 - {ikfkBlendAttribute}")
        mc.expression(s = f"{endOrientConstraint}.{ikEndControl}W1 = {ikfkBlendAttribute}")

        mc.parent(ikHandleName, ikEndControl)
        mc.setAttr(ikHandleName + ".v", 0)

        topGrpName = self.root + "_rig_grp"
        mc.group([rootFKControlGrp, ikEndControlGrp, ikPoleVectorControlGrp, ikfkBlendControlGrp], n = topGrpName)
        mc.setAttr(topGrpName + ".overrideEnabled", 1)
        mc.setAttr(topGrpName + ".overrideRGBColors", 1)
        mc.setAttr(topGrpName + ".overrideColorRGB", r, g, b, type = "double3")

class ColorPicker(QWidget):
    def __init__(self):
        super().__init__()
        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)
        self.colorPickerButton = QPushButton("Set Color")
        self.colorPickerButton.setStyleSheet(f"background-color:black;")
        self.masterLayout.addWidget(self.colorPickerButton)
        self.colorPickerButton.clicked.connect(self.ColorPickButtonClicked)
        self.color = QColor(0, 0, 0)

    def ColorPickButtonClicked(self):
        self.color = QColorDialog.getColor()
        if self.color.isValid():
            self.colorPickerButton.setStyleSheet(f"background-color:{self.color};")

class ControllerColor(QWidget):
    def __init__(self):
        super().__init__()
        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)
        self.controllerTipLabel = QLabel("Select the Controller you want to change the color of, then click the Set Color button to change it's color.")
        self.masterLayout.addWidget(self.controllerTipLabel)
        self.controllerColorButton = QPushButton("Change Color of Controller")
        self.controllerColorButton.setStyleSheet(f"background-color:black;")
        self.masterLayout.addWidget(self.controllerColorButton)
        self.controllerColorButton.clicked.connect(self.ControllerColorButtonClicked)
        self.color = QColor(0, 0, 0)

    def ControllerColorButtonClicked(self):
        self.color = QColorDialog.getColor()
        self.controller = mc.ls(sl = True)[0]
        mc.setAttr(f"{self.controller}.overrideEnabled", 1)
        mc.setAttr(f"{self.controller}.overrideRGBColors", 1)
        mc.setAttr(f"{self.controller}.overrideColorRGB", self.color.redF(), self.color.blueF(), self.color.greenF(), type = "double3")
        

class LimbRigToolWidget(QMayaWindow): # class for the window we create for the limb rigging
    def __init__(self):
        super().__init__()
        self.rigger = LimbRigger() # creates the rigger from the LimbRigger class to be able to establish the root, mid, and end joints and use the class' functions

        self.masterLayout = QVBoxLayout() # establishes the layout for the window as the QVBoxLayout
        self.setLayout(self.masterLayout) # sets the masterlayout as the layout to be used

        self.tipLabel = QLabel("Select the First Joint of the Limb, and click the Auto Find Button") # creates a label to help the user understand how to use the window
        self.masterLayout.addWidget(self.tipLabel) # adds the label to the layout

        self.jointSelectionText = QLineEdit() # creates a textbox where the selected joints will be listed
        self.masterLayout.addWidget(self.jointSelectionText) # adds the textbox to the master layout
        self.jointSelectionText.setEnabled(False) # sets the ability to change what is in the text to false so the user does not accidentally interact and change the names of selected joints, causing errors

        self.autoFindButton = QPushButton("Auto Find Button") # creates a button for the auto find joints
        self.masterLayout.addWidget(self.autoFindButton) # adds the button to the master layout
        self.autoFindButton.clicked.connect(self.AutoFindButtonClicked) # gives functionality to the clicking of the button

        controlSliderLayout = QHBoxLayout() # creates a slider layout to be used in the window

        controlSizeSlider = QSlider() # creates a s;ider 
        controlSizeSlider.setValue(self.rigger.controllerSize) # sets the value of the slider to the value of that initial controller size which is 5
        controlSizeSlider.valueChanged.connect(self.ControlSizeValueChanged) # allows the value of the slider to be changed
        controlSizeSlider.setRange(1, 30) # sets the range for the value of the slider between 1 and 30
        controlSizeSlider.setOrientation(Qt.Horizontal) # changes the slider from vertical to horizontal
        controlSliderLayout.addWidget(controlSizeSlider) # adds the slider to the slider layout
        self.controlSizeLabel = QLabel(f"{self.rigger.controllerSize}") # adds a label that is named after the controller's size to be set
        controlSliderLayout.addWidget(self.controlSizeLabel) # adds the label to the slider layout

        self.masterLayout.addLayout(controlSliderLayout) # adds the slider layout to the master layout of the window

        self.colorPicker = ColorPicker()
        self.masterLayout.addWidget(self.colorPicker)

        self.controllerColorChanger = ControllerColor()
        self.masterLayout.addWidget(self.controllerColorChanger)

        self.rigLimbButton = QPushButton("Rig Limb") # adds a button labeled "Rig Limb"
        self.masterLayout.addWidget(self.rigLimbButton) # adds the button to the master layout
        self.rigLimbButton.clicked.connect(self.RigLimbButtonClicked) # provides functionality to the button being clicked

        self.setWindowTitle("Limb Rigging Tool") # puts a title on top of the window named "Limb Rigging Tool"

    def ControlSizeValueChanged(self, newValue): # function for changing the value of the controller size is changed
        self.rigger.controllerSize = newValue # sets the value of the controller size to the new value the user sets on the slider
        self.controlSizeLabel.setText(f"{self.rigger.controllerSize}") # changes the label text to reflect the value of the controller's new size

    def RigLimbButtonClicked(self): # function for the RigLimbButton being clicked
        self.rigger.RigLimb(self.colorPicker.color.redF(), self.colorPicker.color.greenF(), self.colorPicker.color.blueF()) # runs the RigLimb() function

    def AutoFindButtonClicked(self): # function for the AutoFindButton being clicked
        try: # tries to find the child joints underneath the selected joint and sets the text to reflect the selection
            self.rigger.AutoFindJoints()
            self.jointSelectionText.setText(f"{self.rigger.root}, {self.rigger.mid}, {self.rigger.end}")
        except Exception as e: # if the button encounters an error, it will display an error message for the user
            QMessageBox.critical(self, "Error", "Wrong Selection, please select the first joint of a limb!")

def Run():
    limbRigToolWidget = LimbRigToolWidget() # creates the Limb Rig Tool for the user in Maya
    limbRigToolWidget.show() # displays the Limb Rig Tool