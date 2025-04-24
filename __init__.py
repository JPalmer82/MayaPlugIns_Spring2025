import os
import sys

initFilePath = os.path.abspath(__file__)
pluginDirectory = os.path.dirname(initFilePath)
sourceDirectory = os.path.join(pluginDirectory, "src")
unrealLibraryDirectory = os.path.join(pluginDirectory, "vendor", "unrealSDK")

def AddDirectoryToPath(dir):
    if dir not in sys.path:
        sys.path.append(dir)
        print(f"added {dir} to path")


AddDirectoryToPath(pluginDirectory)
AddDirectoryToPath(sourceDirectory)
AddDirectoryToPath(unrealLibraryDirectory)