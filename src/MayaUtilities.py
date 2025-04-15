import maya.cmds as mc
import maya.OpenMayaUI as omui # this imports maya's open maya ai module, it can help find maya's main window
import shiboken2 # this helps with converting the maya main window to the pyside type

from PySide2.QtWidgets import (QMainWindow, QWidget) # imports all of the widgets needed to build our ui 
from PySide2.QtCore import Qt # this has some values we can use to configure our widget, like our windowtype, or orientation

def GetMayaMainWindow()->QMainWindow: # function to search for and return maya's main window to be used as a reference
    mayaMainWindow = omui.MQtUtil.mainWindow() # creates a reference for the main maya window
    print(mayaMainWindow) # prints the name of the main maya window
    return shiboken2.wrapInstance(int(mayaMainWindow), QMainWindow) # converts the value of the main maya window using shiboken2 library to be more easily worked with

def DeleteWindowWithName(name): # function to delete the old instance of the window we created if the user runs the code without first closing the old instance
    for window in GetMayaMainWindow().findChildren(QWidget, name):
        window.deleteLater() # looks for a previously created window we create for Maya and deletes it if it exists

class QMayaWindow(QWidget): # class we use to find the main maya window and create our new window to work with it
    def __init__(self):
        DeleteWindowWithName(self.GetWindowHash()) # looks for the previously created window with the hash we gave it
        super().__init__(parent = GetMayaMainWindow()) # parents our new window under the main maya window
        self.setWindowFlags(Qt.WindowType.Window) # sets the window we create as a window for maya to understand
        self.setObjectName(self.GetWindowHash()) # gives the window a hash to be used later to find and delete it


    def GetWindowHash(self): # function to get the hash for the window and return it to be used later
        return "ukvgiayvbavbabvafkuvbvbfvbdsjhvbvcskdv"
    


def IsMesh(object):
    shapes = mc.listRelatives(object, s = True)
    if not shapes:
        return False
    
    for s in shapes:
        if mc.objectType(s) == "mesh":
            return True
        
    return False

def IsSkin(object):
    return mc.objectType(object) == "skinCluster"

def IsJoint(object):
    return mc.objectType(object) == "joint"

def GetUpperStream(object):
    return mc.listConnections(object, s = True, d = False, sh = True)

def GetLowerStream(object):
    return mc.listConnections(object, s = False, d = True, sh = True)

def GetAllConnectionsIn(object, nextFunction, searchDepth = 10, Filter = None):
    AllFound = set()
    nexts = nextFunction(object)

    while nexts and searchDepth > 0:
        for next in nexts:
            AllFound.add(next)

        nexts = nextFunction(nexts)
        if nexts:
            nexts = [x for x in nexts if x not in AllFound]
        
        searchDepth -= 1

    if not Filter:
        return list(AllFound)
    
    filtered = []
    for found in AllFound:
        if Filter(found):
            filtered.append(found)

    return filtered