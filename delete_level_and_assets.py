"""Utility to delete a selected level and any assets that are exclusively referenced by it."""

import unreal


DEP_OPTIONS = unreal.AssetRegistryDependencyOptions(
    include_hard=True,
    include_soft=False,
    include_searchable=False,
    include_manage_dependencies=False,
)


def _get_asset_class_name(asset_data: unreal.AssetData) -> str:
    """Return the class name of an asset data entry in a version compatible way."""
    class_path = getattr(asset_data, "asset_class_path", None)
    if class_path is not None:
        asset_name = getattr(class_path, "asset_name", None)
        if asset_name is not None:
            return str(asset_name)
        return str(class_path)
    legacy_name = getattr(asset_data, "asset_class", None)
    return str(legacy_name) if legacy_name is not None else ""


def _get_selected_level_asset_data() -> unreal.AssetData:
    """Return the single selected level asset data, or None if unavailable."""
    selected_assets = unreal.EditorUtilityLibrary.get_selected_asset_data()
    level_assets = [asset for asset in selected_assets if _get_asset_class_name(asset) == "World"]

    if not level_assets:
        unreal.log_error("No level asset selected. Please select exactly one level in the Content Browser.")
        return None
    if len(level_assets) > 1:
        unreal.log_error("Multiple level assets selected. Please select only one level.")
        return None
    return level_assets[0]


def _gather_recursive_dependencies(asset_registry: unreal.AssetRegistry, package_name: str) -> set[str]:
    """Gather all hard dependencies for the given package, recursively."""
    to_process = [package_name]
    visited: set[str] = set()
    dependencies: set[str] = set()

    while to_process:
        current = to_process.pop()
        if current in visited:
            continue
        visited.add(current)

        direct_dependencies = asset_registry.get_dependencies(current, DEP_OPTIONS)
        for dependency in direct_dependencies:
            if dependency == package_name:
                continue
            if dependency not in dependencies:
                dependencies.add(dependency)
            if dependency not in visited:
                to_process.append(dependency)

    dependencies.discard(package_name)
    return dependencies


def _compute_exclusive_assets(asset_registry: unreal.AssetRegistry, level_package: str, candidate_packages: set[str]) -> set[str]:
    """Return the subset of candidate packages that are only referenced by the level or other candidates."""
    exclusive = set(candidate_packages)
    changed = True

    while changed and exclusive:
        changed = False
        for package in list(exclusive):
            referencers = asset_registry.get_referencers(package, DEP_OPTIONS)
            for referencer in referencers:
                if referencer == level_package:
                    continue
                if referencer not in exclusive:
                    exclusive.remove(package)
                    changed = True
                    break
    return exclusive


def _delete_assets(asset_registry: unreal.AssetRegistry, package_names: set[str]) -> None:
    """Delete all assets contained in the provided packages."""
    for package_name in sorted(package_names):
        assets = asset_registry.get_assets_by_package_name(package_name)
        if not assets:
            unreal.log_warning(f"No assets found in package '{package_name}', skipping.")
            continue
        for asset_data in assets:
            object_path = asset_data.get_object_path_string()
            if unreal.EditorAssetLibrary.delete_asset(object_path):
                unreal.log(f"Deleted asset: {object_path}")
            else:
                unreal.log_error(f"Failed to delete asset: {object_path}")


def delete_selected_level_and_dependencies() -> None:
    """Delete the selected level and all assets uniquely referenced by it."""
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    level_asset_data = _get_selected_level_asset_data()
    if level_asset_data is None:
        return

    level_package = level_asset_data.package_name
    unreal.log(f"Gathering dependencies for level: {level_asset_data.object_path_string}")

    candidate_packages = _gather_recursive_dependencies(asset_registry, level_package)
    if not candidate_packages:
        unreal.log("No dependent assets found for the selected level.")
    else:
        unreal.log(f"Found {len(candidate_packages)} candidate dependent packages.")

    exclusive_packages = _compute_exclusive_assets(asset_registry, level_package, candidate_packages)

    shared_count = len(candidate_packages) - len(exclusive_packages)
    if shared_count:
        unreal.log_warning(f"Skipping {shared_count} shared packages that are referenced outside the selected level.")

    if exclusive_packages:
        unreal.log(f"Deleting {len(exclusive_packages)} exclusive dependent packages...")
        _delete_assets(asset_registry, exclusive_packages)
    else:
        unreal.log("No exclusive dependent assets to delete.")

    level_object_path = level_asset_data.get_object_path_string()
    if unreal.EditorAssetLibrary.delete_asset(level_object_path):
        unreal.log(f"Deleted level asset: {level_object_path}")
    else:
        unreal.log_error(f"Failed to delete level asset: {level_object_path}")


if __name__ == "__main__":
    delete_selected_level_and_dependencies()
