# Simvascular-VMR-Numpy-Data-Processing-for-Machine-Learning
It saves the features of the models in the Simvascular VMR database and the simulation results with data mining, and adds various features with VMTK.

I wanted to share the code I use when processing data myself. Unfortunately, the code contains Turkish names, and you'll need to update the file paths according to your setup, sorry about that.

These codes save the fluid density, fluid viscosity, time-dependent flow rate, and the resistance values of the inlet and outlet surfaces for each model. At the same time, by generating a centerline, they record the coordinates of each point on the vessel surface, time-dependent WSS and velocity data, the branch it belongs to, curvature, torsion, and radius information.

REQUİRED LİBRARİES
  numpy
  pyvista
  vmtk
  vtk preferably 9.2.6
  natsort
  os
  xml.etree.ElementTree

  I used Windows VS Code directly for "vmrveriisleme." I ran the "vmtkveriisleme" code on Ubuntu.


After downloading the "model" and "results" files from VMR, you need to delete the first two lines of the ".sjb" file inside the "Simulations" folder. The same goes for the ".mdl" file in the "Models" folder. Otherwise, they'll show up as corrupted XML files.

The "dosyabulma" function lets you browse through files. The command dosyabulma(mainPath, [0,1,2]) gives you the 3rd item inside the 2nd item inside the 1st item in mainPath (as a string). Note: The file/folder order is based on default Windows display settings.

Recommended Structure
  simvascularproje/              
│
├── modeller/                   
│   ├── patient_01/       
│   └── patient_02/
│
├── sonuçlar/                  
│   ├── patient_01/           
│   └── patient_02/
│
├── çıktıdataset/               
│   ├── flowverisi/             
│   ├── traingirdi2/           
│   ├── traingirdi3/            
│   ├── traningirdi/            
│   ├── trainçıktı/             
│   └── vmtkgirdileri/          
│
├── vmrveriisleme.py           
├── vmtkveriisleme.py                     
└── README.md

Note: In the current code, the same models in 'models' and 'results' need to have the same name
