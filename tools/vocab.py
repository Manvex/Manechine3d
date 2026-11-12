import bpy, bmesh, sys, numpy as np, collections, math
names=sys.argv[sys.argv.index('--')+1:]
tot=collections.Counter(); odd=[]
def obb(P):
    c=P.mean(0); Q=P-c
    w,v=np.linalg.eigh(np.cov(Q.T)+1e-12*np.eye(3))
    best=None
    for R_ in (np.eye(3),v[:,::-1]):
        q=Q@R_; mn=q.min(0); mx=q.max(0); vol=np.prod(mx-mn+1e-9)
        if best is None or vol<best[0]*0.98: best=(vol,R_,mn,mx)
    vol,R_,mn,mx=best
    return mx-mn,vol
for name in names:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=f'echipamente/glb/{name}.glb')
    for o in bpy.data.objects:
        if o.type!='MESH': continue
        bm=bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-5)
        bm.verts.ensure_lookup_table()
        seen=set()
        for v in bm.verts:
            if v.index in seen: continue
            st=[v]; comp=[]; seen.add(v.index)
            while st:
                x=st.pop(); comp.append(x)
                for e in x.link_edges:
                    y=e.other_vert(x)
                    if y.index not in seen: seen.add(y.index); st.append(y)
            P=np.array([v.co for v in comp]); d,vol=obb(P)
            faces={f for v in comp for f in v.link_faces}
            mv=abs(sum(f.calc_center_median().dot(f.normal)*f.calc_area() for f in faces)/3)
            r=mv/vol; ds=sorted(d)
            if r>0.93: k='box'
            elif 0.72<r<0.80 and (abs(ds[0]-ds[1])<0.004 or abs(ds[1]-ds[2])<0.004): k='cyl'
            else: k='other'
            mat=o.data.materials[0].name
            tot[(mat,k,len(comp))]+=1
            if k=='other': odd.append((name,o.name.split('__',1)[1],len(comp),[round(x,3) for x in d],round(r,2)))
for k,v in sorted(tot.items()): print(k,v)
for x in odd: print(x)
