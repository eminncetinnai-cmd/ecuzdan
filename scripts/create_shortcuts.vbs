Set oWS = WScript.CreateObject("WScript.Shell")

' 1. Normal Baslatici Kisayolu (E-Cuzdan.lnk)
sLinkFile1 = "C:\Users\e.cetin\Desktop\e-cuzdan\E-Cuzdan.lnk"
Set oLink1 = oWS.CreateShortcut(sLinkFile1)
oLink1.TargetPath = "C:\Users\e.cetin\Desktop\e-cuzdan\start_e_cuzdan.bat"
oLink1.WorkingDirectory = "C:\Users\e.cetin\Desktop\e-cuzdan"
oLink1.IconLocation = "C:\Users\e.cetin\Desktop\e-cuzdan\static\favicon.ico, 0"
oLink1.Description = "E-Cuzdan -- Akilli Varlik ve Finans Yonetim Platformu"
oLink1.Save

' 2. Sessiz Baslatici Kisayolu (E-Cuzdan Sessiz.lnk)
sLinkFile2 = "C:\Users\e.cetin\Desktop\e-cuzdan\E-Cuzdan Sessiz.lnk"
Set oLink2 = oWS.CreateShortcut(sLinkFile2)
oLink2.TargetPath = "C:\Users\e.cetin\Desktop\e-cuzdan\start_silent.vbs"
oLink2.WorkingDirectory = "C:\Users\e.cetin\Desktop\e-cuzdan"
oLink2.IconLocation = "C:\Users\e.cetin\Desktop\e-cuzdan\static\favicon.ico, 0"
oLink2.Description = "E-Cuzdan -- Arka Planda Sessiz Baslat"
oLink2.Save
