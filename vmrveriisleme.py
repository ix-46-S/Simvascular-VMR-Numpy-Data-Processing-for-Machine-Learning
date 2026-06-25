import natsort
import os
import pyvista as pv 
import numpy as np

sonuçlar = r"C:\simvascularproje\sonuçlar"
modeller = r"C:\simvascularproje\modeller"

print("🚀 Code fired up! Running checks...")

if not os.path.exists(modeller) or len(os.listdir(modeller)) == 0:
    print("❌ ERROR: 'modeller' folder not found or empty!")
else:
    print(f"📂 Found {len(os.listdir(modeller))} patient folders in the modeller directory.")

if not os.path.exists(sonuçlar) or len(os.listdir(sonuçlar)) == 0:
    print("⚠️ WARNING: 'sonuçlar' folder either doesn't exist or is EMPTY! That might be why the loop isn't running!")
else:
    print(f"📊 Found {len(os.listdir(sonuçlar))} result files in the sonuçlar directory.")

anaklasör = r"C:\simvascularproje"
ciktidosya = r"C:\simvascularproje\çıktıdataset"

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


for modeladı in os.listdir(modeller): #//! burası
    print(f"\n==================== 🏥 PATIENT: {modeladı} being processed ====================")
    modeleleman = os.path.join(modeller, modeladı)

    flowveri_yolu = dosyabulma(modeleleman,[0,0,1])
    print(f"🔎 [1/3] Was the flow data path found? -> {flowveri_yolu}")
    flowveri = np.loadtxt(flowveri_yolu)
    flowzaman = flowveri [:,0]
    flowdebi = flowveri [:,1]
    print(f"✅ Flow data read. {len(flowzaman)} rows found.")
    np.save(os.path.join(ciktidosya, "flowverisi", f"hasta_{modeladı}_flow.npy"), flowveri)

    meshyolu = dosyabulma(modeleleman,[0,2,1])
    print(f"🔎 [2/3] Was the mesh file path found? -> {meshyolu}")
    mesh = pv.read(meshyolu)
    noktasayısı = mesh.n_points
    koordinatlar = mesh.points
    print(f"✅ Mesh read. Number of points: {noktasayısı}")


    sabitler = (dosyabulma(modeleleman,[0,6,1]))
    print(f"🔎 [3/3] Was the constants (XML) file path found? -> {sabitler}")
    
    import xml.etree.ElementTree as ET
    ağaç = ET.parse(sabitler)
    kök = ağaç.getroot()
    
    fluiddensity = 0
    fluidviscosity = 0
    DT = 0

    dirençkapılarıliste = {}
    dirençkapılarıliste[modeladı] = {}
    sabitlerliste = {}

    for prop in kök.findall(".//prop"):
        key = prop.get("key")
        value = prop.get("value")

        if key == "Fluid Density":
            fluiddensity = float(value)
        elif key == "Fluid Viscosity":
            fluidviscosity = float(value)
        elif key == "Time Step Size":
            DT = float(value)         

    sabitlerliste[modeladı] = {
        "F_D" : fluiddensity,
        "F_V" : fluidviscosity,
    }
        
    os.makedirs(os.path.join(ciktidosya, "traingirdi2"), exist_ok=True)
    np.save(os.path.join(ciktidosya, "traingirdi2", f"hasta_{modeladı}_sabit.npy"), sabitlerliste)
    print(f"💾 [Constants] Saved fluid constants for {modeladı} -> traningirdi2/hasta_{modeladı}_sabit.npy")


    print(f"⚙️  XML constants read -> Density: {fluiddensity}, Viscosity: {fluidviscosity}, Time Step(DT): {DT}")


    for cap in kök.findall(".//cap"): #//! burası
        capname = cap.get("name")  

        bctype_prop = cap.find("./prop[@key='BC Type']")
        
        if bctype_prop is not None and bctype_prop.get("value") == "RCR":
            
            values_prop = cap.find("./prop[@key='Values']")
            
            if values_prop is not None and values_prop.get("value"):
                rcr_listesi = values_prop.get("value").split()
                
                if len(rcr_listesi) >= 3:
                    rp = float(rcr_listesi[0])  
                    c  = float(rcr_listesi[1])  
                    rd = float(rcr_listesi[2])  
                    
                    dirençkapılarıliste[modeladı][capname] = {
                        "Rp": rp,
                        "C": c,
                        "Rd": rd
                    }

    os.makedirs(os.path.join(ciktidosya, "traingirdi3"), exist_ok=True)
    np.save(os.path.join(ciktidosya, "traingirdi3", f"hasta_{modeladı}_rcr.npy"), dirençkapılarıliste)  
    print(f"💾 [RCR] Saved RCR boundary conditions for {modeladı} -> traingirdi3/hasta_{modeladı}_rcr.npy")

    print(f"🚪 RCR caps scanned. Number of caps found: {len(dirençkapılarıliste[modeladı])} -> {list(dirençkapılarıliste[modeladı].keys())}")

    eşleşmebulundu = False
    for sonuçadı in os.listdir(sonuçlar):
        if sonuçadı != modeladı:  
            continue

        eşleşmebulundu = True
        print(f"🔗 Match found! '{modeladı}' has a corresponding folder in the results directory: '{sonuçadı}'")

        sonuçeleman = os.path.join(sonuçlar, sonuçadı)

        vtpyolu = dosyabulma(sonuçeleman, [0])
        print(f"🔎 Was the VTP file path found? -> {vtpyolu}")
        işlenecekmesh = pv.read(vtpyolu)
        tümdiziler = işlenecekmesh.point_data.keys()

        wssverisi = sorted([dizi for dizi in tümdiziler if dizi.startswith("vWSS_")])
        print(f"📈 Number of time steps (vWSS_) found: {len(wssverisi)}")
        if len(wssverisi) == 0:
            print(f"⚠️ WARNING: No data starting with 'vWSS_' found in '{sonuçadı}'! This patient looks like it will be skipped.")
        
        os.makedirs(os.path.join(ciktidosya, "traningirdi"), exist_ok=True)
        os.makedirs(os.path.join(ciktidosya, "trainçıktı"), exist_ok=True)

        Tüm_girdiler = []
        Tüm_çıktılar = []

        for wssadı in wssverisi:
            zamanadımı = (wssadı.split("_")[1])
            
            hizadı = f"velocity_{zamanadımı}" 

            wssvektörleri = np.nan_to_num(işlenecekmesh.point_data[wssadı])
            hızvektörleri = np.nan_to_num(işlenecekmesh.point_data[hizadı]) if hizadı in tümdiziler else np.zeros((noktasayısı, 3))

            if hizadı not in tümdiziler:
                print(f"   ⚠️ Time step {zamanadımı}: '{hizadı}' not found, velocity taken as zero vector.")

            Tüm_girdiler.append(koordinatlar)

            çıktı_bloğu = np.hstack((wssvektörleri, hızvektörleri))
            Tüm_çıktılar.append(çıktı_bloğu)

        print(f"📦 number of blocks collected: {len(Tüm_girdiler)} zaman adımı × {noktasayısı} nokta = {len(Tüm_girdiler)*noktasayısı} satır")


        if len(Tüm_girdiler) > 0:
            X_nihai = np.vstack(Tüm_girdiler).astype(np.float32)
            y_nihai = np.vstack(Tüm_çıktılar).astype(np.float32)
            np.save(os.path.join(ciktidosya, "traningirdi", f"hasta_{modeladı}_input.npy"), X_nihai)
            np.save(os.path.join(ciktidosya, "trainçıktı", f"hasta_{modeladı}_target.npy"), y_nihai)
            
            print(f"✅ Patient {modeladı}'s AI dataset successfully prepared (Vectorized)!")
            print(f"💾 Saved -> input shape: {X_nihai.shape}, target shape: {y_nihai.shape}")
            
            del Tüm_girdiler, Tüm_çıktılar, X_nihai, y_nihai
        else:
            print(f"❌ No data was collected for {modeladı}, nothing was saved!")

    if not eşleşmebulundu:
        print(f"❌ WARNING: No matching subfolder found in 'sonuçlar' for '{modeladı}', this patient was skipped entirely!")

print("\n🏁 Loop completed for all patients.")
