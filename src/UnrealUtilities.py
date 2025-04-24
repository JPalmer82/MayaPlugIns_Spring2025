import unreal
import os

def CreateBaseImportTask(importPath):
    importTask = unreal.AssetImportTask()
    importTask.filename = importPath

    fileName = os.path.basename(importPath).split(".")[0]
    importTask.destination_path = '/Game/' + fileName
    importTask.automated = True
    importTask.save = True
    importTask.replace_existing = True

    return importTask

def ImportSkeletalMesh(meshPath):
    importTask = CreateBaseImportTask(meshPath)

    importOption = unreal.FbxImportUI()
    importOption.import_mesh = True
    importOption.import_as_skeletal = True

    # This setting tells unreal to import the blendshapes
    importOption.skeletal_mesh_import_data.set_editor_property('import_morph_targets', True)
    # This setting tells unreal to use frame 0 as the default pose
    importOption.skeletal_mesh_import_data.set_editor_property('use_t0_as_ref_pose', True)

    importTask.options = importOption

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([importTask])

    return importTask.get_objects()[-1]

def ImportAnimation(mesh: unreal.SkeletalMesh, animPath):
    importTask = CreateBaseImportTask(animPath)
    meshDirectory = os.path.dirname(mesh.get_path_name())
    importTask.destination_path = meshDirectory + "/animations"

    importOptions = unreal.FbxImportUI()
    importOptions.import_mesh = False
    importOptions.import_as_skeletal = True
    importOptions.import_animations = True
    importOptions.skeleton = mesh.skeleton

    importOptions.set_editor_property('automated_import_should_detect_type', False)
    importOptions.set_editor_property('original_import_type', unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    importOptions.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_ANIMATION)

    importTask.options = importOptions

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([importTask])



def ImportMeshAndAnimation(meshPath, animDir):
    mesh = ImportSkeletalMesh(meshPath)
    for fileName in os.listdir(animDir):
        if ".fbx" in fileName:
            animPath = os.path.join(animDir, fileName)
            ImportAnimation(mesh, animPath)


# ImportMeshAndAnimation("D:/profile redirect/jvpalmer/Desktop/Tech_Dir/Alex_start/assets/Alex.fbx", 
 #                      "D:/profile redirect/jvpalmer/Desktop/Tech_Dir/Alex_start/assets/animations")