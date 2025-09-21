import unreal

# Root directories under the Content folder
SEQUENCES_ROOT = "/Game/Sequences"
SHOT_ROOT = f"{SEQUENCES_ROOT}/Shot"

# Ensure the Sequences/Shot directory exists
unreal.EditorAssetLibrary.make_directory(SHOT_ROOT)

# Shot numbers from Shot010 to Shot080 inclusive
shot_numbers = range(10, 81, 10)

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
sequence_factory = unreal.LevelSequenceFactoryNew()

for number in shot_numbers:
    shot_name = f"Shot{number:03d}"
    shot_path = f"{SHOT_ROOT}/{shot_name}"
    animations_path = f"{shot_path}/Animations"

    # Create Shot folder and Animations subfolder
    unreal.EditorAssetLibrary.make_directory(shot_path)
    unreal.EditorAssetLibrary.make_directory(animations_path)

    # Create LevelSequence asset named ShotXXX_01 if it doesn't already exist
    sequence_name = f"{shot_name}_01"
    sequence_asset_path = f"{shot_path}/{sequence_name}"
    if not unreal.EditorAssetLibrary.does_asset_exist(sequence_asset_path):
        asset_tools.create_asset(sequence_name, shot_path, unreal.LevelSequence, sequence_factory)
