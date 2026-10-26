# SPDX-License-Identifier: GPL-3.0-or-later
bl_info = {
    'name': 'Android Touch Transform Fix',
    'author': 'Connor / Codex',
    'version': (1, 1, 0),
    'blender': (5, 3, 0),
    'location': '3D View',
    'description': 'Keep Android touch transforms relative and confirm on finger release',
    'category': '3D View',
}
import bpy
import ctypes
import sys
from bpy.app.handlers import persistent

SUPPORTED_BUILD = b'7dd3aa7e0e95'
_enabled = False
_generation = object()
_windows = {}
_log = None

def trace(*args):
    if _log:
        with open(_log, 'a') as f:
            f.write(repr(args)+'\n')

class _EventPrefix(ctypes.Structure):
    # Blender 5.3 wmEvent, through mval only. Never write pointers or other data.
    _fields_ = [('next',ctypes.c_void_p),('prev',ctypes.c_void_p),
                ('type',ctypes.c_int16),('val',ctypes.c_int16),
                ('xy',ctypes.c_int32*2),('mval',ctypes.c_int32*2)]

def event_prefix(event):
    native = _EventPrefix.from_address(event.as_pointer())
    types = bpy.types.Event.bl_rna.properties['type'].enum_items
    values = bpy.types.Event.bl_rna.properties['value'].enum_items
    # Fail closed before any write if the installed binary's layout differs.
    if (native.type != types[event.type].value or native.val != values[event.value].value
            or tuple(native.xy) != (event.mouse_x,event.mouse_y)
            or tuple(native.mval) != (event.mouse_region_x,event.mouse_region_y)):
        raise RuntimeError('Android touch fix: unsupported event layout')
    return native

def move_event(event,target):
    native = event_prefix(event)
    dx,dy=target[0]-native.xy[0],target[1]-native.xy[1]
    native.xy[0]+=dx; native.xy[1]+=dy
    native.mval[0]+=dx; native.mval[1]+=dy

def confirm_event(event):
    native = event_prefix(event)
    event_type = bpy.types.Event.bl_rna.properties['type'].enum_items['RET'].value
    event_value = bpy.types.Event.bl_rna.properties['value'].enum_items['PRESS'].value
    native.type = event_type
    native.val = event_value

def active_transform(window):
    for op in window.modal_operators:
        if op.bl_idname.startswith('TRANSFORM_OT_') or op.bl_idname in {
            'MESH_OT_extrude_region_move', 'MESH_OT_extrude_context_move',
            'MESH_OT_extrude_region_shrink_fatten', 'MESH_OT_extrude_faces_move',
            'MESH_OT_extrude_edges_move', 'MESH_OT_extrude_vertices_move',
            'MESH_OT_duplicate_move', 'OBJECT_OT_duplicate_move',
            'OBJECT_OT_duplicate_move_linked', 'MESH_OT_loopcut_slide',
        }:
            return (op.as_pointer(), op.bl_idname)
    return None

class WM_OT_android_touch_transform(bpy.types.Operator):
    bl_idname = 'wm.android_touch_transform'
    bl_label = 'Android Touch Transform Input'
    bl_options = {'INTERNAL', 'MODAL_PRIORITY'}

    def invoke(self, context, event):
        self.generation = _generation
        self.window_token = object()
        self.window_id = context.window.as_pointer()
        self.last_xy = (event.mouse_x, event.mouse_y)
        self.held = False
        self.active = None
        self.anchor = None
        self.origin = None
        self.direct = False
        self.loopcut_wait = False
        _windows[self.window_id] = self.window_token
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if (not _enabled or self.generation is not _generation
                or _windows.get(self.window_id) is not self.window_token):
            if _windows.get(self.window_id) is self.window_token:
                _windows.pop(self.window_id, None)
            return {'CANCELLED', 'PASS_THROUGH'}
        try:
            return self.handle_event(context, event)
        except Exception as exc:
            # All native layout checks happen before writes. Stop this patch on error.
            print('Android Touch Transform Fix disabled:', exc)
            self.report({'ERROR'}, str(exc))
            unregister()
            return {'CANCELLED', 'PASS_THROUGH'}

    def handle_event(self, context, event):
        current = active_transform(context.window)
        if current != self.active:
            self.active = current
            self.anchor = self.last_xy
            self.origin = None
            self.direct = self.held
            self.loopcut_wait = bool(current and current[1] == 'MESH_OT_loopcut_slide')
            trace('active',current,'anchor',self.anchor,'direct',self.direct)
        xy = (event.mouse_x, event.mouse_y)
        if not current or self.direct or self.loopcut_wait or event.is_tablet:
            if event.type == 'LEFTMOUSE':
                if event.value in {'PRESS', 'RELEASE'}:
                    self.held = event.value == 'PRESS'
                if current and self.loopcut_wait and event.value == 'RELEASE':
                    self.loopcut_wait = False
                    self.direct = False
                    self.anchor = xy
                    self.origin = None
            if event.type in {'MOUSEMOVE','LEFTMOUSE'}:
                self.last_xy = xy
            return {'PASS_THROUGH'}
        if event.type == 'MOUSEMOVE':
            if self.origin is None:
                self.origin = xy
                trace('first_contact',xy)
            target = (self.anchor[0]+xy[0]-self.origin[0], self.anchor[1]+xy[1]-self.origin[1])
            move_event(event,target)
            self.last_xy = xy
            return {'PASS_THROUGH'}
        if event.type == 'LEFTMOUSE':
            self.held = event.value == 'PRESS'
            self.last_xy = xy
            if event.value == 'RELEASE':
                trace('confirm_release',xy)
                confirm_event(event)
                return {'PASS_THROUGH'}
            return {'RUNNING_MODAL'}
        return {'PASS_THROUGH'}

def ensure_handlers():
    if not _enabled:
        return None
    for window in bpy.context.window_manager.windows:
        # Popup-launched operators can be inserted ahead of MODAL_PRIORITY
        # handlers (wm_handler_operator_insert stops at popup UI handlers).
        # Re-arm through Blender's public API once such an operator appears.
        # The per-window token retires the previous handler on its next event.
        operators = list(window.modal_operators)
        patch_index = next((i for i, op in enumerate(operators)
                            if op.bl_idname == 'WM_OT_android_touch_transform'), None)
        transform = active_transform(window)
        needs_priority = (transform is not None and patch_index is not None
                          and any(op.as_pointer() == transform[0]
                                  for op in operators[:patch_index]))
        if window.as_pointer() not in _windows or needs_priority:
            with bpy.context.temp_override(window=window):
                bpy.ops.wm.android_touch_transform('INVOKE_DEFAULT')
    return .025

@persistent
def on_load(_):
    global _generation
    _generation = object()
    _windows.clear()

def register():
    global _enabled, _generation
    if (sys.platform != 'android' or bpy.app.build_hash != SUPPORTED_BUILD
            or ctypes.sizeof(ctypes.c_void_p) != 8):
        raise RuntimeError('This touch patch supports only Android Blender build 7dd3aa7e0e95')
    _generation = object()
    _windows.clear()
    bpy.utils.register_class(WM_OT_android_touch_transform)
    _enabled = True
    bpy.app.handlers.load_post.append(on_load)
    bpy.app.timers.register(ensure_handlers,first_interval=.5,persistent=True)

def unregister():
    global _enabled
    _enabled = False
    _windows.clear()
    if on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(on_load)
    if bpy.app.timers.is_registered(ensure_handlers):
        bpy.app.timers.unregister(ensure_handlers)
    bpy.utils.unregister_class(WM_OT_android_touch_transform)
