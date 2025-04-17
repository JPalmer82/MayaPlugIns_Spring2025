from MayaUtilities import IsJoint, IsMesh, QMayaWindow
from PySide2.QtGui import QIntValidator, QRegExpValidator
from PySide2.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMessageBox, QPushButton, QVBoxLayout, QWidget
import maya.cmds as mc

def TryAction(action):
    def wrapper(*args, **kwargs):
        try:
            action(*args, **kwargs)
        except Exception as e:
            QMessageBox().critical(None, "Error", f"{e}")

    return wrapper

class AnimClip:
    def __init__(self):
        self.subfix = ""
        self.frameMin = mc.playbackOptions(q = True, min = True)
        self.frameMax = mc.playbackOptions(q = True, max = True)
        self.shouldExport = True



class MayaToUE:
    def __init__(self):
        self.rootJoint = ""
        self.meshes = []
        self.animationClips : list[AnimClip] = []

    def AddNewAnimEntry(self):
        self.animationClips.append(AnimClip())
        return self.animationClips[-1]

    def SetSelectionAsRootJoint(self):
        selection = mc.ls(sl = True)
        if not selection:
            raise Exception("Nothing Selected! Please Select the Joint of the Rig!")
        
        selectedJoint = selection[0]
        if not IsJoint(selectedJoint):
            raise Exception(f"{selectedJoint} is not a joint, Please Select the Root Joint of the Rig!")
        
        self.rootJoint = selectedJoint

    def AddRootJoint(self):
        if (not self.rootJoint) or (not mc.objExists(self.rootJoint)):
            raise Exception("No Root Joint Assigned, please set the current root joint of the rig first!")
        
        currentRootJointPositionX, currentRootJointPositionY, currentRootJointPositionZ = mc.xform(self.rootJoint, q = True, t = True, ws = True)
        if currentRootJointPositionX == 0 and currentRootJointPositionY == 0 and currentRootJointPositionZ == 0:
            raise Exception("current root joint is already at origin, no need to make a new one!")
        
        mc.select(cl = True)
        rootJointName = self.rootJoint + "_root"
        mc.joint(n = rootJointName)
        mc.parent(self.rootJoint, rootJointName)
        self.rootJoint = rootJointName

    def AddMeshs(self):
        selection = mc.ls(sl = True)
        if not selection:
            raise Exception("No Mesh Selected!")
        
        meshes = set()

        for sel in selection:
            if IsMesh(sel):
                meshes.add(sel)

        if len(meshes) == 0:
            raise Exception("No Mesh Selected!")
        
        self.meshes = list(meshes)

class AnimClipEntryWidget(QWidget):
    def __init__(self, animClip: AnimClip):
        super().__init__()
        self.animClip = animClip
        self.masterLayout = QHBoxLayout()
        self.setLayout(self.masterLayout)

        shouldExportCheckbox = QCheckBox()
        shouldExportCheckbox.setChecked(self.animClip.shouldExport)
        self.masterLayout.addWidget(shouldExportCheckbox)
        shouldExportCheckbox.toggled.connect(self.ShouldExportCheckboxToggled)

        self.masterLayout.addWidget(QLabel("Subfix: "))

        subfixLineEdit = QLineEdit()
        subfixLineEdit.setValidator(QRegExpValidator("[a-zA-Z0-9_]+"))
        subfixLineEdit.setText(self.animClip.subfix)
        subfixLineEdit.textChanged.connect(self.SubfixTextChanged)
        self.masterLayout.addWidget(subfixLineEdit)

        self.masterLayout.addWidget(QLabel("Min: "))
        minFrameLineEdit = QLineEdit()
        minFrameLineEdit.setValidator(QIntValidator())
        minFrameLineEdit.setText(str(int(self.animClip.frameMin)))
        minFrameLineEdit.textChanged.connect(self.MinFrameChanged)
        self.masterLayout.addWidget(minFrameLineEdit)

        self.masterLayout.addWidget(QLabel("Max: "))
        maxFrameLineEdit = QLineEdit()
        maxFrameLineEdit.setValidator(QIntValidator())
        maxFrameLineEdit.setText(str(int(self.animClip.frameMax)))
        maxFrameLineEdit.textChanged.connect(self.MaxFrameChanged)
        self.masterLayout.addWidget(maxFrameLineEdit)

        setRangeButton = QPushButton("[-]")
        setRangeButton.clicked.connect(self.SetRangeButtonClicked)
        self.masterLayout.addWidget(setRangeButton)

        deleteButton = QPushButton("X")
        deleteButton.clicked.connect(self.DeleteButtonClicked)
        self.masterLayout.addWidget(deleteButton)

    def DeleteButtonClicked(self):
        self.deleteLater()

    def SetRangeButtonClicked(self):
        mc.playbackOptions(e = True, min = self.animClip.frameMin, max = self.animClip.frameMax)
        mc.playbackOptions(e = True, ast = self.animClip.frameMin, aet = self.animClip.frameMax)


    def MaxFrameChanged(self, newVal):
        self.animClip.frameMax = int(newVal)

    def MinFrameChanged(self, newVal):
        self.animClip.frameMin = int(newVal)

    def SubfixTextChanged(self, newText):
        self.animClip.subfix = newText


    def ShouldExportCheckboxToggled(self):
        self.animClip.shouldExport = not self.animClip.shouldExport

class MayaToUEWidget(QMayaWindow):
    def GetWindowHash(self):
        return "MayaToUEJP04172025745"
    
    def __init__(self):
        super().__init__()
        self.mayaToUE = MayaToUE()
        self.setWindowTitle("Maya To UE")

        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)

        self.rootJointText = QLineEdit()
        self.rootJointText.setEnabled(False)
        self.masterLayout.addWidget(self.rootJointText)

        setSelectionAsRootJointButton = QPushButton("Set Root Joint")
        setSelectionAsRootJointButton.clicked.connect(self.SetSelectionAsRootJointButtonClicked)
        self.masterLayout.addWidget(setSelectionAsRootJointButton)

        addRootJointButton = QPushButton("Add Root Joint")
        addRootJointButton.clicked.connect(self.AddRootJointButtonClicked)
        self.masterLayout.addWidget(addRootJointButton)

        self.meshList = QListWidget()
        self.masterLayout.addWidget(self.meshList)
        self.meshList.setFixedHeight(80)
        addMeshButton = QPushButton("Add Meshes")
        addMeshButton.clicked.connect(self.AddMeshButtonCLicked)
        self.masterLayout.addWidget(addMeshButton)

        addNewAnimClipEntryButton = QPushButton("Add Animation Clip")
        addNewAnimClipEntryButton.clicked.connect(self.AddNewAnimClipEntryButtonClicked)
        self.masterLayout.addWidget(addNewAnimClipEntryButton)

        self.animEntryLayout = QVBoxLayout()
        self.masterLayout.addLayout(self.animEntryLayout)

    def AddNewAnimClipEntryButtonClicked(self):
        newEntry = self.mayaToUE.AddNewAnimEntry()
        self.animEntryLayout.addWidget(AnimClipEntryWidget(newEntry))

    @TryAction
    def AddMeshButtonCLicked(self):
        self.mayaToUE.AddMeshs()
        self.meshList.clear()
        self.meshList.addItems(self.mayaToUE.meshes)

    @TryAction
    def AddRootJointButtonClicked(self):
        self.mayaToUE.AddRootJoint()
        self.rootJointText.setText(self.mayaToUE.rootJoint)

    @TryAction
    def SetSelectionAsRootJointButtonClicked(self):
        self.mayaToUE.SetSelectionAsRootJoint()
        self.rootJointText.setText(self.mayaToUE.rootJoint)

MayaToUEWidget().show()