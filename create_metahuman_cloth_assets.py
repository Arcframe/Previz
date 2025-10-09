"""Utility script to build a MetaHuman cloth asset, outfit and wardrobe item.

Update the configuration section before execution. The script expects that the
MetaHuman and Cloth editor plugins are enabled (UE 5.6 or newer).
"""

import unreal

# ---------------------------------------------------------------------------
# Configuration – update the asset paths/names below to match your project.
# ---------------------------------------------------------------------------

# Skeletal mesh for the MetaHuman base body that will own the outfit.
BODY_SKELETAL_MESH_PATH = "/Game/MetaHumans/Common/Body/Medium/MH_Medium_Body"  # TODO: replace

# Skeletal meshes for every garment that should be merged into a single cloth asset.
CLOTHING_SKELETAL_MESH_PATHS = [
    "/Game/Characters/Outfits/SM_Top_A",  # TODO: replace
    "/Game/Characters/Outfits/SM_Pants_A",  # TODO: replace
]

# Folder (within /Game) where all new assets will be created.
TARGET_FOLDER = "/Game/MetaHumans/Generated/Wardrobe"

# Names for the new assets.
CLOTH_ASSET_NAME = "MH_Merged_Cloth"
OUTFIT_ASSET_NAME = "MH_Merged_Outfit"
WARDROBE_ITEM_NAME = "MH_Merged_WardrobeItem"


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _require_attr(module, attr_name):
    if not hasattr(module, attr_name):
        raise RuntimeError(f"Required Unreal type '{attr_name}' is not available.\n"
                           "Ensure the MetaHuman and Cloth Editor plugins are enabled.")
    return getattr(module, attr_name)


def load_asset(path, expected_type=None):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not asset:
        raise RuntimeError(f"Asset not found: {path}")
    if expected_type and not isinstance(asset, expected_type):
        raise RuntimeError(f"Asset '{path}' is not of type {expected_type.__name__}")
    return asset


def ensure_directory(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def save_asset(asset):
    asset_path = asset.get_path_name()
    if not unreal.EditorAssetLibrary.save_asset(asset_path):
        raise RuntimeError(f"Failed to save asset: {asset_path}")


def create_asset(name, folder, asset_class, factory):
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset = asset_tools.create_asset(name, folder, asset_class, factory)
    if not asset:
        raise RuntimeError(f"Failed to create asset {folder}/{name}")
    return asset


# ---------------------------------------------------------------------------
# Cloth asset creation
# ---------------------------------------------------------------------------

def create_cloth_asset(clothing_meshes):
    cloth_asset_factory = _require_attr(unreal, "ClothAssetFactory")()
    cloth_asset_class = _require_attr(unreal, "ClothAsset")
    cloth_asset = create_asset(CLOTH_ASSET_NAME, TARGET_FOLDER, cloth_asset_class, cloth_asset_factory)

    cloth_subsystem = unreal.get_editor_subsystem(unreal.ClothAssetEditorSubsystem)
    if cloth_subsystem is None:
        raise RuntimeError("ClothAssetEditorSubsystem is not available. Enable the Cloth Editor plugin.")

    required_methods = [
        "reset_graph",
        "get_graph",
        "add_node",
        "get_output_pin",
        "get_input_pin",
        "connect_pins",
        "compile_cloth_asset",
        "get_terminal_node",
    ]
    for method_name in required_methods:
        if not hasattr(cloth_subsystem, method_name):
            raise RuntimeError(
                "ClothAssetEditorSubsystem is missing the method '{}' – this script requires Unreal Engine 5.6 or newer.".format(method_name)
            )

    # Reset the graph to a clean state.
    cloth_subsystem.reset_graph(cloth_asset)

    import_node_class = unreal.load_class(None, "/Script/ClothEditor.ClothAssetGraphNode_SkeletalMeshImport")
    merge_node_class = unreal.load_class(None, "/Script/ClothEditor.ClothAssetGraphNode_MergeClothCollection")
    if not import_node_class or not merge_node_class:
        raise RuntimeError("Failed to load cloth graph node classes. Check class paths and plugin availability.")

    terminal_node = cloth_subsystem.get_terminal_node(cloth_asset)
    if terminal_node is None:
        raise RuntimeError("Unable to locate the ClothAssetTerminal node in the new cloth asset.")

    previous_output_pin = None
    y_offset = 0

    graph = cloth_subsystem.get_graph(cloth_asset)
    if graph is None:
        raise RuntimeError("Cloth asset graph could not be retrieved.")

    for skeletal_mesh in clothing_meshes:
        import_node = cloth_subsystem.add_node(graph, import_node_class, unreal.Vector2D(-800.0, float(y_offset)))
        import_node.set_editor_property("skeletal_mesh", skeletal_mesh)
        import_node.set_editor_property("import_all_lods", True)

        output_pin = cloth_subsystem.get_output_pin(import_node)

        if previous_output_pin is None:
            previous_output_pin = output_pin
        else:
            merge_node = cloth_subsystem.add_node(graph, merge_node_class, unreal.Vector2D(-300.0, float(y_offset)))
            cloth_subsystem.connect_pins(previous_output_pin, cloth_subsystem.get_input_pin(merge_node, 0))
            cloth_subsystem.connect_pins(output_pin, cloth_subsystem.get_input_pin(merge_node, 1))
            previous_output_pin = cloth_subsystem.get_output_pin(merge_node)

        y_offset += 300

    if previous_output_pin is None:
        raise RuntimeError("No clothing meshes were processed.")

    cloth_subsystem.connect_pins(previous_output_pin, cloth_subsystem.get_input_pin(terminal_node, 0))
    cloth_subsystem.compile_cloth_asset(cloth_asset)

    save_asset(cloth_asset)
    return cloth_asset


# ---------------------------------------------------------------------------
# Outfit asset creation
# ---------------------------------------------------------------------------

def create_outfit_asset(cloth_asset, body_skeletal_mesh):
    outfit_factory = _require_attr(unreal, "MetaHumanOutfitAssetFactory")()
    outfit_class = _require_attr(unreal, "MetaHumanOutfitAsset")
    outfit_asset = create_asset(OUTFIT_ASSET_NAME, TARGET_FOLDER, outfit_class, outfit_factory)

    sized_source_struct = _require_attr(unreal, "MetaHumanSizedOutfitSource")()
    sized_source_struct.set_editor_property("source_asset", cloth_asset)
    sized_source_struct.set_editor_property("source_body_parts", [body_skeletal_mesh])

    outfit_asset.set_editor_property("sized_outfit_sources", [sized_source_struct])

    save_asset(outfit_asset)
    return outfit_asset


# ---------------------------------------------------------------------------
# Wardrobe item creation
# ---------------------------------------------------------------------------

def create_wardrobe_item(outfit_asset):
    wardrobe_factory = _require_attr(unreal, "MetaHumanWardrobeItemFactory")()
    wardrobe_class = _require_attr(unreal, "MetaHumanWardrobeItem")
    wardrobe_item = create_asset(WARDROBE_ITEM_NAME, TARGET_FOLDER, wardrobe_class, wardrobe_factory)

    wardrobe_item.set_editor_property("outfit_asset", outfit_asset)

    save_asset(wardrobe_item)
    return wardrobe_item


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    ensure_directory(TARGET_FOLDER)

    body_skeletal_mesh = load_asset(BODY_SKELETAL_MESH_PATH, unreal.SkeletalMesh)
    clothing_meshes = [load_asset(path, unreal.SkeletalMesh) for path in CLOTHING_SKELETAL_MESH_PATHS]

    cloth_asset = create_cloth_asset(clothing_meshes)
    outfit_asset = create_outfit_asset(cloth_asset, body_skeletal_mesh)
    wardrobe_item = create_wardrobe_item(outfit_asset)

    unreal.log(f"Created cloth asset: {cloth_asset.get_path_name()}")
    unreal.log(f"Created outfit asset: {outfit_asset.get_path_name()}")
    unreal.log(f"Created wardrobe item: {wardrobe_item.get_path_name()}")


if __name__ == "__main__":
    main()
