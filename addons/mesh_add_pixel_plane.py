#====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
#======================= END GPL LICENSE BLOCK ========================

# <pep8 compliant>
bl_info = {
    "name": "Add Pixel Plane",
    "author": "Dalai Felinto",
    "version": (1, 0),
    "blender": (2, 7, 5),
    "location": "Add Mesh Menu",
    "description": "Creates a plane made of quads forming a pixel grid",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Mesh"}


import bpy
from bpy.props import (
        IntProperty,
        FloatProperty,
        )


class AddPixelPlaneOperator(bpy.types.Operator):
    """Add a simple box mesh"""
    bl_idname = "mesh.pixel_plane_add"
    bl_label = "Add Pixel Plane"
    bl_options = {'REGISTER', 'UNDO'}

    pixels_width = IntProperty(name="Pixels Width", default=1920, min = 2, max=4096)
    pixels_height = IntProperty(name="Pixels Height", default=1080, min = 2, max=4096)
    plane_width = FloatProperty(name="Width", default=1.0, min = 0.1, max=10.0)

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=200)

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        col.prop(self, "plane_width", "Plane Width")
        col.separator()

        col.label(text="Pixels")
        row = col.row(align=True)
        row.prop(self, "pixels_width", text="Width")
        row.prop(self, "pixels_height", text="Height")


def menu_func(self, context):
    self.layout.operator(AddPixelPlaneOperator.bl_idname, icon='IMAGE_RGB')


def register():
    bpy.utils.register_class(AddPixelPlaneOperator)
    bpy.types.INFO_MT_mesh_add.append(menu_func)


def unregister():
    bpy.utils.unregister_class(AddPixelPlaneOperator)
    bpy.types.INFO_MT_mesh_add.remove(menu_func)


if __name__ == "__main__":
    register()

    # test call
    bpy.ops.mesh.pixel_plane_add()
