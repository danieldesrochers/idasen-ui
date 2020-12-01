# idasen-ui
Python Graphical User Interface to control ikea IDÅSEN desk.

This application is built using the IdasenDesk API made by 'newAM/idasen' which was a heavily modified fork of 'rhyst/idasen-controller'.

The IDÅSEN desk is an electric sitting standing desk with a Linak controller sold by ikea.

The position of the desk can controlled by a physical switch on the desk or via bluetooth using an phone app.

This is a Graphical User Interface written in wx.Python to control the Idasen via bluetooth from a desktop computer.

Set Up
******

Prerequisites
=============

The desk should be connected and paired to the computer.

Install
=======

.. code-block:: bash

    Step 1: Pre-install Python3.8 
    Step 2: python3.8 -m pip install --upgrade idasen-ui
