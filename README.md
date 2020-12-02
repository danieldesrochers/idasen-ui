# idasen-ui
Application to control ikea IDÅSEN desk.

This application is built on top of the IdasenDesk API made by 'newAM/idasen' which was a heavily modified fork of 'rhyst/idasen-controller'.

IDÅSEN is an electric sitting-standing desk with a Linak bluetooth controller sold by ikea.

The position of the desk can controlled by a physical switch on the desk or via bluetooth using an phone app.

This application controls the Idasen desk via bluetooth from a desktop computer.

Prerequisites
=============
The desk should be connected and paired to the computer.

Install Idasen-UI
=================
Unzip the package to any <folder> with read-write user permissions (e.g.: c:/MyPrograms)

Browse to your extracted <folder>/idasen-ui 

Run 'idasen-ui.exe'

How To Use Idasen-UI
====================
Idasen Desk Control application is a simple graphical user interface.

Discover your desk
------------------
When application runs for the first time, no save configuration will be found.
Click Bluetooth button to discover your desk and save initial configuration.

You are connected!
------------------
Once connected to the desk, current desk position will be displayed and moving buttons will be enabled. 
Click Bluetooth button to discover your desk and save initial configuration.
- Press and maintain the up/down arrow the move the desk to the desired position.
- Press M(emory) button to save the current position to 1 or 2.
- Press position 1 or 2 to move the desk to the save position.
