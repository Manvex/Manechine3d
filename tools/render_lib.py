import bpy, math
from mathutils import Vector
def scene_bounds():
    mn=Vector((1e9,)*3); mx=Vector((-1e9,)*3)
    for o in bpy.data.objects:
        if o.type!='MESH' or o.name.startswith('_'): continue
        for c in o.bound_box:
            w=o.matrix_world@Vector(c)
            for i in range(3):
                mn[i]=min(mn[i],w[i]); mx[i]=max(mx[i],w[i])
    return mn,mx
def setup(res=640, samples=48, az=-38, el=22):
    sc=bpy.context.scene
    sc.render.engine='CYCLES'; sc.cycles.samples=samples; sc.cycles.use_denoising=True
    sc.cycles.device='CPU'
    sc.render.resolution_x=sc.render.resolution_y=res
    sc.view_settings.view_transform='Standard'
    mn,mx=scene_bounds(); c=(mn+mx)/2; size=(mx-mn).length
    # floor / backdrop
    bpy.ops.mesh.primitive_plane_add(size=60, location=(c.x,c.y,mn.z-0.0005))
    fl=bpy.context.object; fl.name='_floor'
    m=bpy.data.materials.new('_floor'); m.use_nodes=True
    b=m.node_tree.nodes['Principled BSDF']; b.inputs['Base Color'].default_value=(0.80,0.81,0.83,1); b.inputs['Roughness'].default_value=0.65
    fl.data.materials.append(m)
    w=bpy.data.worlds.new('_w'); sc.world=w; w.use_nodes=True
    bg=w.node_tree.nodes['Background']; bg.inputs[0].default_value=(0.92,0.93,0.95,1); bg.inputs[1].default_value=0.55
    def light(name,loc,energy,sz):
        l=bpy.data.lights.new(name,'AREA'); l.energy=energy; l.size=sz
        o=bpy.data.objects.new(name,l); sc.collection.objects.link(o)
        o.location=c+Vector(loc)*size
        d=(c-o.location); o.rotation_euler=d.to_track_quat('-Z','Y').to_euler()
    e=size*size
    light('_key',(-0.9,-1.0,1.3),e*14,size*0.9)
    light('_fill',(1.2,-0.5,0.6),e*5,size*1.2)
    light('_rim',(0.3,1.2,1.0),e*7,size*0.8)
    global _C
    cam=bpy.data.cameras.new('_cam'); cam.lens=70
    co=bpy.data.objects.new('_cam',cam); sc.collection.objects.link(co); sc.camera=co
    a=math.radians(az); e_=math.radians(el)
    d=Vector((-math.sin(a)*math.cos(e_),math.cos(a)*math.cos(e_),math.sin(e_)))
    fov=cam.angle
    dist=(size/2)/math.tan(fov/2)*1.08
    co.location=c+d*dist
    co.rotation_euler=(c-co.location).to_track_quat('-Z','Y').to_euler()
    cam.clip_end=dist*4
    _C=(co,c,dist)
def set_view(az,el):
    co,c,dist=_C
    a=math.radians(az); e_=math.radians(el)
    d=Vector((-math.sin(a)*math.cos(e_),math.cos(a)*math.cos(e_),math.sin(e_)))
    co.location=c+d*dist
    co.rotation_euler=(c-co.location).to_track_quat('-Z','Y').to_euler()
def render(path):
    bpy.context.scene.render.filepath=path
    bpy.ops.render.render(write_still=True)
