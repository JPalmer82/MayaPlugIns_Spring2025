import importlib
import MayaUtilities
importlib.reload(MayaUtilities)

from MayaUtilities import * # the * imports everything in the file be careful using this
from PySide2.QtWidgets import QPushButton, QVBoxLayout
import maya.cmds as mc

class ProxyRigger:
    def __init__(self):
        self.skin = ""
        self.model = ""
        self.joints = []

    def CreateProxyRigFromSelectedMesh(self):
        mesh = mc.ls(sl = True)[0]
        if not IsMesh(mesh):
            raise TypeError(f"{mesh} is not a mesh! Please select a mesh")
        
        self.model = mesh
        modelShape = mc.listRelatives(self.model, s = True)[0]
        print(f"found mesh {mesh}, and shape {modelShape}")

        skin = GetAllConnectionsIn(modelShape, GetUpperStream, 10, IsSkin)
        if not skin:
            raise Exception(f"{mesh} has no skin! Tool only works with a rigged model")
        
        self.skin = skin[0]

        joints = GetAllConnectionsIn(modelShape, GetUpperStream, 10, IsJoint)
        if not joints:
            raise Exception(f"{mesh} has no joints bound! Tool only works with a rigged model.")
        
        self.joints = joints

        print(f"start build with mesh: {self.model}, skin: {self.skin}, and joints: {self.joints}")

        jointVertMap = self.GenerateJointVertDict()
        segments = []
        controls = []
        for joint, verts in jointVertMap.items():
            print(f"joint {joints} controls {verts} primarily")
            newSeg = self.CreateProxyModelForJointAndVerts(joint, verts)
            if newSeg is None:
                continue

            newSkinCluster = mc.skinCluster(self.joints, newSeg)[0]
            mc.copySkinWeights(ss = self.skin, ds = newSkinCluster, nm = True, sa = "closestPoint", ia = "closestJoint")
            segments.append(newSeg)

            controlLocator = "ac_" + joint + "_proxy"
            mc.spaceLocator(n = controlLocator)
            controlLocatorGrp = controlLocator + "_grp"
            mc.group(controlLocator, n = controlLocatorGrp)
            mc.matchTransform(controlLocatorGrp, joint)

            visibilityAttr = "vis"
            mc.addAttr(controlLocator, ln = visibilityAttr, min = 0, max = 1, dv = 1, k = True)
            mc.connectAttr(controlLocator + "." + visibilityAttr, newSeg + ".v")
            controls.append(controlLocatorGrp)

        proxyTopGrp = self.model + "_proxy_grp"
        mc.group(segments, n = proxyTopGrp)

        controlTopGrp = "ac_" + self.model + "_proxy_grp"
        mc.group(controls, n = controlTopGrp)

        globalProxyControl = "ac_" + self.model + "_proxy_global"
        mc.circle(n = globalProxyControl, r = 30)
        mc.parent(proxyTopGrp, globalProxyControl)
        mc.parent(controlTopGrp, globalProxyControl)
        mc.setAttr(proxyTopGrp + ".inheritsTransform", 0)

        visibilityAttr = "vis"
        mc.addAttr(globalProxyControl, ln = visibilityAttr, min = 0, max = 1, dv = 1, k = True)
        mc.connectAttr(globalProxyControl + "." + visibilityAttr, proxyTopGrp + ".v")


    def CreateProxyModelForJointAndVerts(self, joint, verts):
        if not verts:
            return None
        
        faces = mc.polyListComponentConversion(verts, fromVertex = True, toFace = True)
        faces = mc.ls(faces, fl = True)

        labels = set() # a set is like a list, but it only holds unique elements, it is not ordered, and it is faster than a list when it comes to looking for things
        for face in faces:
            labels.add(face.replace(self.model, ""))
            
        dupe = mc.duplicate(self.model)[0]

        allDupeFaces = mc.ls(f"{dupe}.f[*]", fl = True)
        facesToDelete = []
        for dupeFace in allDupeFaces:
            label = dupeFace.replace(dupe, "")
            if label not in labels:
                facesToDelete.append(dupeFace)

        mc.delete(facesToDelete)

        dupeName = self.model + "_" + joint + "_proxy"
        mc.rename(dupe, dupeName)
        return dupeName


    def GenerateJointVertDict(self):
        dict = {}
        for joint in self.joints:
            dict[joint] = []

        verts = mc.ls(f"{self.model}.vtx[*]", fl = True)
        for vert in verts:
            owningJoint = self.GetJointWithMaxInfluence(vert, self.skin)
            dict[owningJoint].append(vert)

        return dict

    def GetJointWithMaxInfluence(self, vert, skin):
        weights = mc.skinPercent(skin, vert, q = True, v = True)
        joints = mc.skinPercent(skin, vert, q = True, t = None)

        maxWeightIndex = 0
        maxWeight = weights[0]

        for i in range(1, len(weights)):
            if weights[i] > maxWeight:
                maxWeight = weights[i]
                maxWeightIndex = i

        return joints[maxWeightIndex]
        

class ProxyRiggerWidget(QMayaWindow):
    def __init__(self):
        super().__init__()
        self.proxyRigger = ProxyRigger()
        self.setWindowTitle("Proxy Rigger")
        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)
        generateProxyRigButton = QPushButton("Generate Proxy Rig")
        self.masterLayout.addWidget(generateProxyRigButton)
        generateProxyRigButton.clicked.connect(self.GenerateProxyRigButtonClicked)

    def GenerateProxyRigButtonClicked(self):
        self.proxyRigger.CreateProxyRigFromSelectedMesh()

    def GetWindowHash(self):
        return "712890f8c1f9b099b91b6e9aa2fcc0830973ff04"

def Run():
    proxyRiggerWidget = ProxyRiggerWidget()
    proxyRiggerWidget.show()