import os
from MayaUtilities import IsJoint, IsMesh, QMayaWindow
from PySide2.QtCore import Signal
from PySide2.QtGui import QIntValidator, QRegExpValidator
from PySide2.QtWidgets import QCheckBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMessageBox, QPushButton, QVBoxLayout, QWidget
import maya.cmds as mc
import MayaPlugIns_Spring2025.src

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
        self.fileName = ""
        self.saveDirectory = ""

    def GetAllJoints(self):
        joints = []
        joints.append(self.rootJoint)
        children = mc.listRelatives(self.rootJoint, c = True, ad = True, type = "joint")
        if children:
            joints.extend(children)

        return joints

    def SaveFiles(self):
        allJoints = self.GetAllJoints()
        allMeshes = self.meshes

        allObjectToExport = allJoints + allMeshes
        mc.select(allObjectToExport, r = True)

        skeletalMeshExportPath = self.GetSkeletalMeshSavePath()

        mc.FBXResetExport()
        mc.FBXExportSmoothingGroups('-v', True)
        mc.FBXExportInputConnections('-v', False)

        # -f means file name, -s means export selected, -ea means export animation
        mc.FBXExport('-f', skeletalMeshExportPath, '-s', True, '-ea', False)

        os.makedirs(self.GetAnimationDirectoryPath(), exist_ok = True)
        mc.FBXExportBakeComplexAnimation('-v', True)
        for animClip in self.animationClips:
            if not animClip.shouldExport:
                continue

            animExportPath = self.GetSavePathForAnimClip(animClip)

            startFrame = animClip.frameMin
            endFrame = animClip.frameMax

            mc.FBXExportBakeComplexStart('-v', startFrame)
            mc.FBXExportBakeComplexEnd('-v', endFrame)
            mc.FBXExportBakeComplexStep('-v', 1)

            mc.playbackOptions(e = True, min = startFrame, max = endFrame)
            mc.FBXExport('-f', animExportPath, '-s', True, '-ea', True)

        self.SendToUnreal()

    def SendToUnreal(self):
        ueUtilPath = os.path.join(MayaPlugIns_Spring2025.src, "UnrealUtilities.py")
        ueUtilPath = os.path.normpath(ueUtilPath)

        meshPath = self.GetSkeletalMeshSavePath().replace("\\", "/")
        animDir = self.GetAnimDirPath().replace("\\", "/")

        commands = []
        with open(ueUtilPath, 'r') as ueUtilityFile:
            commands = ueUtilityFile.readlines

        commands.append(f"\nImportMeshAndAnimation(\'{meshPath}\', '{animDir}\')")

        command = "".join(commands)
        print(command)




    def GetAnimationDirectoryPath(self):
        path = os.path.join(self.saveDirectory, "animations")
        return os.path.normpath(path)

    def GetSavePathForAnimClip(self, animClip: AnimClip):
        path = os.path.join(self.GetAnimationDirectoryPath(), self.fileName + animClip.subfix + ".fbx")
        return os.path.normpath(path)

    def GetSkeletalMeshSavePath(self):
        path = os.path.join(self.saveDirectory, self.fileName + ".fbx")
        return os.path.normpath(path)

    def RemoveAnimClip(self, clipToRemove: AnimClip):
        self.animationClips.remove(clipToRemove)
        print(f"animation clip removed, now we have: {len(self.animationClips)} left")

    def AddNewAnimEntry(self):
        self.animationClips.append(AnimClip())
        print(f"animation clip added, now we have: {len(self.animationClips)} anim clip(s)")
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
    entryRemoved = Signal(AnimClip)
    entrySubfixChanged = Signal(str)
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
        self.entryRemoved.emit(self.animClip)
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
        self.entrySubfixChanged.emit(newText)

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
        addMeshButton.clicked.connect(self.AddMeshButtonClicked)
        self.masterLayout.addWidget(addMeshButton)

        addNewAnimClipEntryButton = QPushButton("Add Animation Clip")
        addNewAnimClipEntryButton.clicked.connect(self.AddNewAnimClipEntryButtonClicked)
        self.masterLayout.addWidget(addNewAnimClipEntryButton)

        self.animEntryLayout = QVBoxLayout()
        self.masterLayout.addLayout(self.animEntryLayout)

        self.saveFileLayout = QHBoxLayout()
        self.masterLayout.addLayout(self.saveFileLayout)
        fileNameLabel = QLabel("File Name: ")
        self.saveFileLayout.addWidget(fileNameLabel)

        self.fileNameLineEdit = QLineEdit()
        self.fileNameLineEdit.setFixedWidth(80)
        self.fileNameLineEdit.setValidator(QRegExpValidator("\w+"))
        self.fileNameLineEdit.textChanged.connect(self.FileNameLineEditChanged)
        self.saveFileLayout.addWidget(self.fileNameLineEdit)

        self.directoryLabel = QLabel("Save Directory: ")
        self.saveFileLayout.addWidget(self.directoryLabel)
        self.saveDirectoryLineEdit = QLineEdit()
        self.saveDirectoryLineEdit.setEnabled(False)
        self.saveFileLayout.addWidget(self.saveDirectoryLineEdit)
        self.pickDirectoryButton = QPushButton("...")
        self.pickDirectoryButton.clicked.connect(self.PickDirectoryButtonClicked)
        self.saveFileLayout.addWidget(self.pickDirectoryButton)

        self.savePreviewLabel = QLabel("")
        self.masterLayout.addWidget(self.savePreviewLabel)

        saveFileButton = QPushButton("Save Files")
        saveFileButton.clicked.connect(self.SaveFileButtonClicked)
        self.masterLayout.addWidget(saveFileButton)


    def SaveFileButtonClicked(self):
        self.mayaToUE.SaveFiles()

    def UpdateSavePreviewLabel(self):
        previewText = self.mayaToUE.GetSkeletalMeshSavePath()
        if not self.mayaToUE.animationClips:
            self.savePreviewLabel.setText(previewText)
            return
        
        for animClip in self.mayaToUE.animationClips:
            animSavePath = self.mayaToUE.GetSavePathForAnimClip(animClip)
            previewText += "\n" + animSavePath

        self.savePreviewLabel.setText(previewText)

    @TryAction
    def PickDirectoryButtonClicked(self):
        path = QFileDialog().getExistingDirectory()
        self.saveDirectoryLineEdit.setText(path)
        self.mayaToUE.saveDirectory = path
        self.UpdateSavePreviewLabel()

    @TryAction
    def FileNameLineEditChanged(self, newText):
        self.mayaToUE.fileName = newText
        self.UpdateSavePreviewLabel()


    @TryAction
    def AddNewAnimClipEntryButtonClicked(self):
        newEntry = self.mayaToUE.AddNewAnimEntry()
        newEntryWidget = AnimClipEntryWidget(newEntry)
        newEntryWidget.entryRemoved.connect(self.AnimClipEntryRemoved)
        newEntryWidget.entrySubfixChanged.connect(lambda x : self.UpdateSavePreviewLabel())
        self.animEntryLayout.addWidget(newEntryWidget)
        self.UpdateSavePreviewLabel()


    @TryAction
    def AnimClipEntryRemoved(self, animClip: AnimClip):
        self.mayaToUE.RemoveAnimClip(animClip)
        self.UpdateSavePreviewLabel()


    @TryAction
    def AddMeshButtonClicked(self):
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