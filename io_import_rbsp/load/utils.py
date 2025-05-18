from typing import Any

from bpy.types import Collection


def change_collection(blender_object: Any, collection: Collection):
    # move to entity_collection
    linked_collections = blender_object.users_collection
    for collection in linked_collections:
        collection.unlink(blender_object)
    collection.link(blender_object)
