import bpy, bmesh, sys, numpy as np
from mathutils import Vector
name=sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=f'glb/{name}.glb')
def obb(P):
    c=P.mean(0); Q=P-c
    w,v=np.linalg.eigh(np.cov(Q.T)+1e-12*np.eye(3))
    R=v[:,::-1]
    # snap: try axis-aligned first
    best=None
    for R_ in (np.eye(3),R):
        q=Q@R_; mn=q.min(0); mx=q.max(0); vol=np.prod(mx-mn+1e-6)
        if best is None or vol<best[0]*0.98: best=(vol,R_,mn,mx)
    vol,R_,mn,mx=best
    return c+((mn+mx)/2)@R_.T,(mx-mn),R_
for o in bpy.data.objects:
    if o.type!='MESH':
        print('EMPTY',o.name,[round(x,3) for x in o.matrix_world.translation], o.parent.name if o.parent else '', dict(o.items()))
        continue
    bm=bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
    bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-5)
    seen=set(); parts=[]
    for v in bm.verts:
        if v.index in seen: continue
        st=[v]; comp=[]
        seen.add(v.index)
        while st:
            x=st.pop(); comp.append(x)
            for e in x.link_edges:
                y=e.other_vert(x)
                if y.index not in seen: seen.add(y.index); st.append(y)
        parts.append(comp)
    print('MESH',o.name,'parent',o.parent.name if o.parent else None,'parts',len(parts),'mat',[m.name for m in o.data.materials])
    for comp in parts:
        P=np.array([o.matrix_world@v.co for v in comp])
        c,d,R=obb(P)
        ax='AA' if np.allclose(R,np.eye(3)) else 'ROT'
        print('   nv=%4d c=(%.3f %.3f %.3f) d=(%.3f %.3f %.3f) %s'%(len(comp),*c,*d,ax))
