import os
import shutil
import maya.cmds as mc

def Install():
    projectPath = os.path.dirname(os.path.abspath(__file__))
    pluginName = os.path.split(projectPath)[-1]
    mayaScriptPath = os.path.join(mc.internalVar(uad = True), "scripts")
    
    pluginDestinationPath = os.path.join(mayaScriptPath, pluginName)
    if os.path.exists(pluginDestinationPath):
        shutil.rmtree(pluginDestinationPath)

    os.makedirs(pluginDestinationPath, exist_ok = True)
    sourceDirectoryName = "src"
    assetDirectoryName = "assets"

    shutil.copytree(os.path.join(projectPath, sourceDirectoryName), os.path.join(pluginDestinationPath, sourceDirectoryName))
    shutil.copytree(os.path.join(projectPath, assetDirectoryName), os.path.join(pluginDestinationPath, assetDirectoryName))
    shutil.copytree(os.path.join(projectPath, "vendor"), os.path.join(pluginDestinationPath, "vendor"))
    shutil.copy2(os.path.join(projectPath, "__init__.py"), os.path.join(pluginDestinationPath, "__init__.py"))

    def AddShelfButton(scriptName):
        currentShelf = mc.tabLayout("ShelfLayout", q = True, selectTab = True)
        mc.setParent(currentShelf)
        icon = os.path.join(pluginDestinationPath, assetDirectoryName, scriptName + ".PNG")
        mc.shelfButton(c = f"from {pluginName}.src import {scriptName};{scriptName}.Run()", image = icon)

    AddShelfButton("LimbRiggingTool")
    AddShelfButton("MayaToUE")
    AddShelfButton("ProxyRigger")