import bpy, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import render_lib
src,dst=sys.argv[-2],sys.argv[-1]
res=int(os.environ.get('RES','448'))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
render_lib.setup(res=res,samples=int(os.environ.get('SPP','32')))
render_lib.render(dst)
