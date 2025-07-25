Windows Photo Viewer Restore Tool (For Win 10/11 LTSC)
=============================================================

This package restores the classic Windows Photo Viewer and enables it as a selectable app for images. Also included are the latest packages (as of date of this document) to add HEIF/HEVC support to Windows Photo Viewer with a simple command listed below. Fuck your bloatware, Microsoft!

INSTRUCTIONS:
-------------
1. Right-click "EnablePhotoViewer.reg" and click MERGE.
   - You might need to run it as admin.
   - Reboot or log out/in afterward.

2. Right-click an image file > Open With > Choose another app
   - Click "More Apps"
   - Scroll down to "Look for another app on this PC"
   - Navigate to:
     C:\Program Files\Windows Photo Viewer\photoviewer.dll
   - Select it to open images with Photo Viewer.

NOTES:
------
- This works on stripped Win10/11 LTSC installs.
- `.HEIC` support still requires the HEIF extension (.appx).

ENABLING HEIC/HEVC SUPPORT: 
------
- Download the two AppXBundle files, open a Powershell terminal with admin rights.
- Run the following command to add HEIC/HEVC support (I needed both to get it working with photos):
  -  Add-AppxPackage "C:\PathToAppxFils\Microsoft*.appxbundle
