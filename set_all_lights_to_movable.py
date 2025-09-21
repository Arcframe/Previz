"""Utility script to convert every light in the current level to Movable.

This script should be executed inside the Unreal Editor's Python environment.
It walks through every actor in the loaded levels, finds any light components
they own (including components that live inside Blueprint actors), and ensures
their mobility is set to ``Movable``.

Usage::

    # In the Unreal Editor Python console or a Python asset
    import set_all_lights_to_movable
    set_all_lights_to_movable.convert_all_lights_to_movable()

The script logs a short summary of the work that it performs.
"""

import unreal


LIGHT_COMPONENT_BASE_CLASS = unreal.LightComponentBase
MOVABLE = unreal.ComponentMobility.MOVABLE


def _gather_light_components(actor: unreal.Actor) -> list[unreal.LightComponentBase]:
    """Return every light component that belongs to ``actor``.

    ``Blueprint`` actors often expose their light components through the
    regular component interface, so querying by ``LightComponentBase`` will
    also surface lights that are created inside user Blueprints.
    """

    components = []

    # Some actor types (e.g. SkyLight, DirectionalLight, etc.) expose their
    # primary light component via ``get_light_component``.
    if hasattr(actor, "get_light_component"):
        try:
            light_component = actor.get_light_component()
        except Exception:
            light_component = None
        if isinstance(light_component, LIGHT_COMPONENT_BASE_CLASS):
            components.append(light_component)

    try:
        owned_components = actor.get_components_by_class(LIGHT_COMPONENT_BASE_CLASS)
    except Exception:
        owned_components = []

    if owned_components:
        components.extend(owned_components)

    # ``get_components_by_class`` already returns unique components, but the
    # explicit call above can yield duplicates when ``get_light_component`` is
    # also available.  Use ``dict.fromkeys`` to de-duplicate while preserving
    # ordering.
    unique_components = list(dict.fromkeys(components))
    return unique_components


def _set_mobility(component: unreal.LightComponentBase) -> bool:
    """Set ``component`` to Movable mobility.

    Returns ``True`` if the component's mobility was changed, ``False``
    otherwise.
    """

    if component is None:
        return False

    try:
        current_mobility = component.get_editor_property("mobility")
    except Exception:
        return False

    if current_mobility == MOVABLE:
        return False

    component.modify()
    component.set_editor_property("mobility", MOVABLE)
    component.post_edit_change()

    outer_package = component.get_outermost()
    if outer_package is not None:
        outer_package.mark_package_dirty()

    return True


def convert_all_lights_to_movable() -> None:
    """Convert every light component found in the current level to Movable."""

    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    total_components = 0
    updated_components = 0
    touched_levels: set[unreal.Package] = set()

    for actor in actors:
        light_components = _gather_light_components(actor)
        if not light_components:
            continue

        actor_changed = False
        for component in light_components:
            total_components += 1
            if _set_mobility(component):
                updated_components += 1
                actor_changed = True

        if actor_changed:
            actor.modify()
            actor.post_edit_change()

            level = actor.get_level()
            if level is not None:
                package = level.get_outermost()
                if package is not None:
                    touched_levels.add(package)

    for package in touched_levels:
        package.mark_package_dirty()

    unreal.log(
        f"Scanned {len(actors)} actors. "
        f"Found {total_components} light components and updated {updated_components} to Movable."
    )


if __name__ == "__main__":
    convert_all_lights_to_movable()
