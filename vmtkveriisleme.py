from vmtk import vmtkscripts
import pyvista as pv
import os
import numpy as np
import natsort
import xml.etree.ElementTree as ET
import vtk

def dosyabulma(anayol, sıralistesi):
    mevcutyol = anayol
    for sıra in sıralistesi:
        hepsi = os.listdir(mevcutyol)
        
        klasörler = natsort.natsorted([f for f in hepsi if os.path.isdir(os.path.join(mevcutyol, f))], 
                                      alg=natsort.IGNORECASE)
        
        dosyalar = natsort.natsorted([f for f in hepsi if os.path.isfile(os.path.join(mevcutyol, f))], 
                                     alg=natsort.IGNORECASE)
        
        pencerelistesi = klasörler + dosyalar
        
        if len(pencerelistesi) > sıra:
            mevcutyol = os.path.join(mevcutyol, pencerelistesi[sıra])
        else:
            return None
            
    return mevcutyol


meshklasörü = "/mnt/c/simvascularproje/modeller"
çıkışklasörü = "/mnt/c/simvascularproje/çıktıdataset/vmtkgirdileri"


for meshler in os.listdir(meshklasörü):
    print(f"\n{'='*50}")
    print(f"Processing model: {meshler}")
    print(f"{'='*50}")

    yol = os.path.join(meshklasörü,meshler)
    mesh = dosyabulma(yol,[0,2,1])
    mdlyolu = os.path.join(dosyabulma(yol,[0,3,0]))
    print(f"  Mesh file     : {mesh}")
    print(f"  MDL file      : {mdlyolu}")
    meshnesnesi = pv.read(mesh)
    print(f"  Mesh loaded   : {meshnesnesi.n_points} points, {meshnesnesi.n_cells} cells")


    tree = ET.parse(mdlyolu)
    root = tree.getroot()

    inflowid = []
    outflowid = []
    
    for face in root.iter('face'):
        face_type = face.get('type')
        face_id = int(face.get('id'))
        face_name = face.get('name')
        
        if face_type == 'cap':
            
            if 'inflow' in face_name.lower():
                inflowid.append(face_id)
            else:
                outflowid.append(face_id)

    print(f"  Inflow  IDs   : {inflowid}")
    print(f"  Outflow IDs   : {outflowid}")

    pvmesh_yolu = dosyabulma(yol,[0,2,1])
    pvmesh = pv.read(pvmesh_yolu)

    cap_array_name = None
    for name in pvmesh.cell_data.keys():
        if 'capid' in name.lower() or 'faceid' in name.lower() or 'groupid' in name.lower():
            cap_array_name = name
            break
    if not cap_array_name:
        raise ValueError(f"{dosyabulma(yol,[0,3,1])} içinde yüzey kimlik dizisi (CapID) bulunamadı!")
    print(f"  Cap array     : '{cap_array_name}'")
    
    source_points = []
    target_points = []

    for inf_id in inflowid:
        kapak_mesh = pvmesh.extract_cells(pvmesh.cell_data[cap_array_name] == inf_id)
        source_points.extend(kapak_mesh.center) # Atama değil, ekleme yapıyoruz

    for out_id in outflowid:
        kapak_mesh = pvmesh.extract_cells(pvmesh.cell_data[cap_array_name] == out_id)
        kapak_merkezi = kapak_mesh.center
        target_points.extend(kapak_merkezi)

    print(f"  Source points : {source_points}")
    print(f"  Target points : {target_points}")

    print("  Computing centerlines...")
    centerline_bot = vmtkscripts.vmtkCenterlines()
    centerline_bot.Surface = meshnesnesi 

    centerline_bot.SeedSelectorName = 'pointlist' 
    centerline_bot.SourcePoints = source_points    
    centerline_bot.TargetPoints = target_points     
    centerline_bot.Execute()
    print("  Centerlines computed.")

    print("  Computing centerline geometry...")
    geometri_bot = vmtkscripts.vmtkCenterlineGeometry()
    geometri_bot.Centerlines = centerline_bot.Centerlines
    geometri_bot.Execute()
    print("  Centerline geometry computed.")

    print("  Computing centerline attributes...")
    özellikler = vmtkscripts.vmtkCenterlineAttributes()
    # Centerline verisini artık geometri_bot'tan alıyoruz
    özellikler.Centerlines = geometri_bot.Centerlines 
    özellikler.Surface = meshnesnesi
    özellikler.Execute()
    print("  Centerline attributes computed.")

    özelliklerçıktı = özellikler.Centerlines

    dalayırıcı =vmtkscripts.vmtkBranchExtractor()
    dalayırıcı.Centerlines = özelliklerçıktı
    dalayırıcı.Execute()
    print("  Branches extracted.")
    nihaicenterline = dalayırıcı.Centerlines

    pvcenterline = pv.wrap(nihaicenterline)

    meshnoktaları = meshnesnesi.points
    noktalar = meshnesnesi.n_points

    vmtkgirdileri = []

    print(f"  Mapping {noktalar} surface points to centerline features...")
    for n_id in range(noktalar):
        yüzeykoordinatı = meshnoktaları[n_id]
        enyakıncbulma = pvcenterline.find_closest_point(yüzeykoordinatı)

        v_radius    = pvcenterline.point_data["MaximumInscribedSphereRadius"][enyakıncbulma]
        v_curvature = pvcenterline.point_data["Curvature"][enyakıncbulma]
        v_torsion   = pvcenterline.point_data["Torsion"][enyakıncbulma]
        hücre_listesi = vtk.vtkIdList()
        nihaicenterline.GetPointCells(enyakıncbulma, hücre_listesi)
        v_branch_id = hücre_listesi.GetId(0)

        girdisatırı = [
            yüzeykoordinatı[0], yüzeykoordinatı[1], yüzeykoordinatı[2],
            v_radius, v_curvature, v_torsion, v_branch_id
        ]

        vmtkgirdileri.append(girdisatırı)
    vmtkgirdileri = np.array(vmtkgirdileri)

    np.save(os.path.join(çıkışklasörü,f"{meshler}"), vmtkgirdileri)
    print(f"  Saved: {meshler}.npy  ({vmtkgirdileri.shape[0]} rows x {vmtkgirdileri.shape[1]} cols)")