# IDASEN UI - DESK CONTROL
# TODO: log to file control by config
# TODO: implement 4 buttons version
# TODO: right-click to menu 
#         - move window to other screen

import wx
import wx.adv
import wx.lib.agw.gradientbutton as GB
import wx.lib.agw.aquabutton as AB
import wx.lib.buttons as GBB
import functools

from idasen import IdasenDesk
from typing import Callable
from typing import List
from typing import Optional
from threading import *
import asyncio
import logging
import os
import sys
import voluptuous as vol
import yaml
import time
import clr

HOME = os.path.expanduser("~")
IDASEN_CONFIG_DIRECTORY = os.path.join(HOME, ".config", "idasen-ui")
IDASEN_CONFIG_PATH = os.path.join(IDASEN_CONFIG_DIRECTORY, "idasen-ui.yaml")
LOG_TO_CONSOLE = True

DEFAULT_CONFIG = {
    "mac_address": "AA:AA:AA:AA:AA:AA",
    "positions": {"pos2": 1.1, "pos1": 0.70},
    "always_on_top": 0,
    "log_to_file": 1,
}

CONFIG_SCHEMA = vol.Schema(
    {
        "mac_address": vol.All(str, vol.Length(min=17, max=17)),
        "positions": {
            str: vol.All(
                vol.Any(float, int),
                vol.Range(min=IdasenDesk.MIN_HEIGHT, max=IdasenDesk.MAX_HEIGHT),
            )
        },
        "always_on_top": vol.All(int),
        "log_to_file": vol.All(int),
    },
    extra=False,
)
       
def log(msg):
    if LOG_TO_CONSOLE:
        print(msg)
    else:
        logging.info(msg)
            
def message_to_user(msg):
        dlg = wx.MessageDialog(None, msg, "Message", wx.OK|wx.ICON_EXCLAMATION)
        dlg.ShowModal()
        dlg.Destroy()        
                     
def align_bottom_right(win):
    dw, dh = wx.DisplaySize()
    w, h = win.GetSize()
    x = dw - w
    y = dh - h - 35
    win.SetPosition((x, y))
    
def save_config(config: dict, path: str = IDASEN_CONFIG_PATH):
    with open(path, "w") as f:
        yaml.dump(config, f)


def load_config(path: str = IDASEN_CONFIG_PATH) -> dict:
    """ Load user config. """
    try:
        with open(path, "r") as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
    except FileNotFoundError:
        return {}

    # convert old config file format
    if "always_on_top" not in config:
        config["always_on_top"] = 0
        save_config(config, path)
        
    if "log_to_file" not in config:
        config["log_to_file"] = 1
        save_config(config, path)
        
    try:
        config = CONFIG_SCHEMA(config)
    except vol.Invalid as e:
        message_to_user(f"Invalid configuration: {e}", file=sys.stderr)
        
    return config
        
async def discover_desk() -> bool:
    mac = await IdasenDesk.discover()
    global config
    if mac is not None:
        log(f"Discovered desk's MAC address: {mac}")
        if os.path.isfile(IDASEN_CONFIG_PATH):
            #update existing config
            config = load_config()
            config["mac_address"] = mac            
            save_config(config)
        else:
            #create new config file
            DEFAULT_CONFIG["mac_address"] = mac
            os.makedirs(IDASEN_CONFIG_DIRECTORY, exist_ok=True)            
            config = DEFAULT_CONFIG
            save_config(config)            
        return True
    else:
        return False
                
########################################################################
# Thread class that executes processing
class DeskWorkerThread(Thread):
    """Worker Thread Class."""
    def __init__(self, parent_window):
        """Init Worker Thread Class."""                
        Thread.__init__(self)
        self._parent_window = parent_window
        self.current_height = 0.0
        self.desk_height_target = 0.0
        self.workerThread = False

    def connect(self) -> bool:
        self.idasen_desk = IdasenDesk(config["mac_address"], exit_on_fail=False)      
        self.idasen_desk.RETRY_COUNT = 0
        asyncio.run(self.idasen_desk._connect())            
        self.connected = asyncio.run(self.idasen_desk.is_connected())
        return self.connected    

    def start_running_loop(self):
        # This starts the thread running loop
        self.workerThread = True
        self.start()

    def stop_running_loop(self):
        self.workerThread = False        

    def is_connected(self) -> bool:
        return self.connected    

    def move_to_height(self, height):
        if height > self.idasen_desk.MAX_HEIGHT:
            log(f"target height of {height:.3f} meters exceeds maximum of {self.MAX_HEIGHT:.3f}")
            self.desk_height_target  = 0.0
        elif height < self.idasen_desk.MIN_HEIGHT:
            log(f"target height of {height:.3f} meters exceeds minimum of {self.MIN_HEIGHT:.3f}")
            self.desk_height_target  = 0.0    
        else:
            log(f"moving to target height of {height:.3f} meters")
            self.desk_height_target = height            

    def run(self):
        """Run Worker Thread."""   
        log("Starting worker thread...")

        deskMovingAutomatically = False
        deskMovingUp = False
        deskMovingDown = False
        previous_difference = 0.0
        bug_protection_counter = 0
        bug_protection_retry = 0
        refresh_counter_limit = 10
        refresh_auto_counter = refresh_counter_limit        

        try:
            while self.workerThread:
                # pseudo-realtime running loop, everything in there should be quick
                # move up sequence
                if self._parent_window.buttonUpPressed:
                    log("moving up...")
                    asyncio.run(self.idasen_desk.move_up())
                    deskMovingUp = True
                    deskMovingDown = False             
                    deskMovingAutomatically = False
                    self.desk_height_target = 0.0                
                    refresh_auto_counter = refresh_counter_limit #force refresh
                # move down sequence
                elif self._parent_window.buttonDownPressed:
                    log("moving down...")
                    asyncio.run(self.idasen_desk.move_down())
                    deskMovingUp = False
                    deskMovingDown = True 
                    deskMovingAutomatically = False                    
                    self.desk_height_target = 0.0   
                    refresh_auto_counter = refresh_counter_limit #force refresh
                # stop moving
                elif deskMovingUp or deskMovingDown:
                    log("stop moving up...")
                    asyncio.run(self.idasen_desk.stop())
                    deskMovingUp = False
                    deskMovingDown = False 
                    deskMovingAutomatically = False
                    self.desk_height_target = 0.0   
                    refresh_auto_counter = refresh_counter_limit #force refresh
                    
                # move_to_height button 1 or 2 pressed, let's move to target
                if self.desk_height_target != 0.0:
                    difference = self.desk_height_target - self.current_height
                    log(f"{self.desk_height_target=:.2f} {self.current_height=:.2f} {difference=:.2f}")  
                    #------------------------------------------
                    # ---- protection for idasen desk move issue
                    # ---- but only retry twice to reach the target height
                    # ---- required in case something blocks the desk from moving up or down
                    if previous_difference == difference:
                        bug_protection_counter = bug_protection_counter + 1
                    else:
                        bug_protection_counter = 0
                        bug_protection_retry = 0
                        previous_difference = difference                
                    if bug_protection_counter > 9:
                        log("waiting 1 sec for desk to catch up...")
                        time.sleep(1)
                        bug_protection_retry = bug_protection_retry + 1
                        bug_protection_counter = 0
                    if bug_protection_retry > 2:
                        log("Someting wrong... cancelling move_to_height")
                        asyncio.run(self.idasen_desk.stop())
                        deskMovingUp = False
                        deskMovingDown = False        
                        deskMovingAutomatically = False
                        self.desk_height_target = 0.0   
                        refresh_auto_counter = refresh_counter_limit #force refresh                         
                    # ---- end of protection                        
                    #------------------------------------------
                    if abs(difference) < 0.005:  # tolerance of 0.005 meters
                        log(f"reached target of {self.desk_height_target:.2f}")
                        self.desk_height_target = 0.0
                        deskMovingAutomatically = False
                        asyncio.run(self.idasen_desk.stop())                   
                    elif difference > 0:
                        log("moving up...")
                        asyncio.run(self.idasen_desk.move_up())  
                        if deskMovingAutomatically == False:
                            time.sleep(0.5)
                            deskMovingAutomatically = True  
                            log("waiting 500 msec for desk to workaround issue...")                                
                    elif difference < 0:
                        log("moving down...")
                        asyncio.run(self.idasen_desk.move_down())
                        if deskMovingAutomatically == False:
                            time.sleep(0.75)
                            deskMovingAutomatically = True
                            log("waiting 500 msec for desk to workaround issue...")                            
                    refresh_auto_counter = refresh_counter_limit #force refresh                   

                #auto-refresh current height label
                if refresh_auto_counter >= refresh_counter_limit:                
                    height = asyncio.run(self.idasen_desk.get_height())
                    if self.current_height != height:
                        self.current_height = height
                        self._parent_window.gbHeightBtn.SetLabel(f"{self.current_height:.2f}")
                        self._parent_window.gbHeightBtn.Refresh() 
                    refresh_auto_counter = 0
                else:
                    # we are IDLE... refresh UI slowly
                    refresh_auto_counter = refresh_auto_counter + 1
                    time.sleep(0.5)

            # End of while loop
            log("Returning from worker thread.")
        except Exception as e:
            log(e)
            self.connected = False
            self.workerThread = False 
            self._parent_window.showDisabledButton()
            sys.exit(1)
        
        
class MyForm(wx.Frame):
 
    #----------------------------------------------------------------------
    def __init__(self):
        size = wx.Size(465,85)
        self.defaultstyle = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX| wx.SYSTEM_MENU)
        self.myFrame = wx.MiniFrame.__init__(self,None, wx.ID_ANY, "Idasen - Desk Control Application v1.1.0", wx.DefaultPosition, size, self.defaultstyle, "")
        logging.debug('MyForm:_init_: miniframe created')
        
        # prepare the popmenu
        self._popmenu = PopMenu(self)

        if config["always_on_top"] == 1:
            self._popmenu._aotMenu.Check(True)
            self.SetWindowStyle(self.defaultstyle | wx.STAY_ON_TOP)            
        
        icon = wx.Icon()
        icon.CopyFromBitmap(wx.Bitmap("appicon.png", wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)   
        logging.debug('MyForm:_init_: appicon found')
        
        panel = wx.Panel(self, wx.ID_ANY)            
        panel.Bind(wx.EVT_RIGHT_DOWN, self.OnRightClick)        
        
        bmp = wx.Bitmap("bt-nc.png", wx.BITMAP_TYPE_ANY)          
        btsize = wx.Size(60,46)
        self.gbBluetoothBtn = GB.GradientButton(panel, bitmap=bmp, label="", size=btsize)                        
        self.gbBluetoothBtn.Bind(wx.EVT_BUTTON, self.onBtBtnPress) 
        self.gbBluetoothBtn.Bind(wx.EVT_RIGHT_DOWN, self.OnRightClick)
        self.gbBluetoothBtn.SetToolTip(wx.ToolTip("Make sure desk is connected and paired to computer.\nPress Bluetooth button to discover desk."))                         
                                  
        self.gbHeightBtn = GB.GradientButton(panel, label="N/A")
        size = wx.Size(75,46)
        font = wx.Font(wx.FontInfo(24).FaceName("Arial").Bold())
        self.gbHeightBtn.SetFont(font)
        self.gbHeightBtn.SetInitialSize(size)
        self.gbHeightBtn.Bind(wx.EVT_RIGHT_DOWN, self.OnRightClick)
        self.gbHeightBtn.Disable()
		
        bmp = wx.Bitmap("up-nc.png", wx.BITMAP_TYPE_ANY)
        self.gbUpBtn = GB.GradientButton(panel, bitmap=bmp, label="", size=btsize)        
        self.gbUpBtn.Bind( wx.EVT_LEFT_DOWN, self.onBtnUpPress)
        self.gbUpBtn.Bind( wx.EVT_LEFT_UP, self.onBtnUpRelease)
        self.gbUpBtn.Bind(wx.EVT_RIGHT_DOWN, self.OnRightClick)
        self.gbUpBtn.Disable()
        
        bmp = wx.Bitmap("down-nc.png", wx.BITMAP_TYPE_ANY)
        self.gbDownBtn = GB.GradientButton(panel, bitmap=bmp, label="", size=btsize)
        self.gbDownBtn.Bind( wx.EVT_LEFT_DOWN, self.onBtnDownPress)
        self.gbDownBtn.Bind( wx.EVT_LEFT_UP, self.onBtnDownRelease)
        self.gbDownBtn.Bind(wx.EVT_RIGHT_DOWN, self.OnRightClick)
        self.gbDownBtn.Disable()
        
        bmp = wx.Bitmap("pos1-nc.png", wx.BITMAP_TYPE_ANY)
        self.pos1Btn = GB.GradientButton(panel, bitmap=bmp, label="", size=btsize)
        self.pos1Btn.Bind(wx.EVT_BUTTON, self.onBtn1Press)  
        self.pos1Btn.Bind(wx.EVT_RIGHT_DOWN, self.OnRightClick)
        self.pos1Btn.Disable()       

        bmp = wx.Bitmap("pos2-nc.png", wx.BITMAP_TYPE_ANY)
        self.pos2Btn = GB.GradientButton(panel, bitmap=bmp, label="", size=btsize)
        self.pos2Btn.Bind(wx.EVT_BUTTON, self.onBtn2Press)   
        self.pos2Btn.Bind(wx.EVT_RIGHT_DOWN, self.OnRightClick)
        self.pos2Btn.Disable()       

        bmp = wx.Bitmap("m-nc.png", wx.BITMAP_TYPE_ANY)
        self.gbMBtn = GB.GradientButton(panel, bitmap=bmp, label="", size=btsize)
        self.gbMBtn.Bind(wx.EVT_BUTTON, self.onBtnMemoryPress)
        self.gbMBtn.Bind(wx.EVT_RIGHT_DOWN, self.OnRightClick)
        self.gbMBtn.Disable()


        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
        logging.debug('MyForm:_init_: all button created and bind')
        
        # Create desk instance that will be running in a separate thread        
        self.buttonUpPressed = False
        self.buttonDownPressed = False    
        self.buttonMemoryPressed = False
        
        logging.debug('MyForm:_init_: about to create DeskWorkerThread')
        self.idasen_desk = DeskWorkerThread(self) 
        logging.debug('MyForm:_init_: DeskWorkerThread created')
        # Try to connect to Idasen desk based on previous saved config
        try:            
            if self.idasen_desk.connect():            
                self.showConnectedButton()
                self.idasen_desk.start_running_loop()        
        except Exception as e:
            log("No saved config found")
            
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.gbBluetoothBtn, 0, wx.ALL, 1)
        sizer.Add(self.gbHeightBtn, 0, wx.ALL, 1)
        sizer.Add(self.gbUpBtn, 0, wx.ALL, 1)
        sizer.Add(self.gbDownBtn, 0, wx.ALL, 1)
        sizer.Add(self.pos1Btn, 0, wx.ALL, 1)
        sizer.Add(self.pos2Btn, 0, wx.ALL, 1)
        sizer.Add(self.gbMBtn, 0, wx.ALL, 1)
        
        panel.SetSizer(sizer)

    #----------------------------------------------------------------------
    def OnRightClick(self, e): 
        # sow popu menu 
        log("OnRightClick")              
        self.PopupMenu(self._popmenu, e.GetPosition()) 
        
    def OnClose(self, event):
        self.idasen_desk.stop_running_loop()
        time.sleep(0.5) #wait for thread to exit
        event.Skip()
        
    def showDisabledButton(self):                
        self.gbBluetoothBtn.SetBitmapLabel(wx.Bitmap("bt-nc.png", wx.BITMAP_TYPE_ANY))
        self.gbBluetoothBtn.Enable()
        self.gbHeightBtn.SetLabel("N/A")
        self.gbHeightBtn.Refresh() 
        self.gbUpBtn.SetBitmapLabel(wx.Bitmap("up-nc.png", wx.BITMAP_TYPE_ANY))        
        self.gbUpBtn.Disable()        
        self.gbDownBtn.SetBitmapLabel(wx.Bitmap("down-nc.png", wx.BITMAP_TYPE_ANY))
        self.gbDownBtn.Disable()        
        self.pos1Btn.SetBitmapLabel(wx.Bitmap("pos1-nc.png", wx.BITMAP_TYPE_ANY))
        self.pos1Btn.Disable()               
        self.pos2Btn.SetBitmapLabel(wx.Bitmap("pos2-nc.png", wx.BITMAP_TYPE_ANY))
        self.pos2Btn.Disable()               
        self.gbMBtn.SetBitmapLabel(wx.Bitmap("m-nc.png", wx.BITMAP_TYPE_ANY))
        self.gbMBtn.Disable()        

    def showConnectedButton(self):        
        self.gbBluetoothBtn.SetBitmapLabel(wx.Bitmap("bt.png", wx.BITMAP_TYPE_ANY))
        self.gbBluetoothBtn.Disable()
        self.gbUpBtn.SetBitmapLabel(wx.Bitmap("up.png", wx.BITMAP_TYPE_ANY))        
        self.gbUpBtn.Enable()        
        self.gbDownBtn.SetBitmapLabel(wx.Bitmap("down.png", wx.BITMAP_TYPE_ANY))
        self.gbDownBtn.Enable()        
        self.pos1Btn.SetBitmapLabel(wx.Bitmap("pos1.png", wx.BITMAP_TYPE_ANY))
        self.pos1Btn.Enable()               
        self.pos2Btn.SetBitmapLabel(wx.Bitmap("pos2.png", wx.BITMAP_TYPE_ANY))
        self.pos2Btn.Enable()               
        self.gbMBtn.SetBitmapLabel(wx.Bitmap("m.png", wx.BITMAP_TYPE_ANY))
        self.gbMBtn.Enable()
        
        
    def onBtBtnPress(self, event):
        """"""        
        log("BT button pressed! Trying to discover_desk...")
        if asyncio.run(discover_desk()):
            log("Desk found, trying to connect...")
            if self.idasen_desk.connect():
                log("Desk connected! Enabling and starting running loop...")
                self.showConnectedButton()
                self.idasen_desk.start_running_loop()
            else:
                log("Desk found but cannot connect to it.")
        else:
            message_to_user("Unable discover desk from Bluetooth devices.\nMake sure desk is connected and paired to the computer.")

    def onBtnUpPress(self, event):
        """"""
        self.buttonUpPressed = True
        
    def onBtnUpRelease(self, event):
        """"""
        self.buttonUpPressed = False
        
    def onBtnDownPress(self, event):
        """"""
        self.buttonDownPressed = True
        
    def onBtnDownRelease(self, event):
        """"""
        self.buttonDownPressed = False  

    def onBtn1Press(self, event):
        """"""
        if self.buttonMemoryPressed:
            self.disableSavePosition()
            self.saveCurrentHeightInConfig("pos1")
        else:        
            self.idasen_desk.move_to_height(config["positions"]["pos1"])
        
        
    def onBtn2Press(self, event):
        """"""
        if self.buttonMemoryPressed:
            self.disableSavePosition()
            self.saveCurrentHeightInConfig("pos2")
        else:
            self.idasen_desk.move_to_height(config["positions"]["pos2"])
        
        
    def onBtnMemoryPress(self, event):
        """"""
        if self.buttonMemoryPressed:
            self.disableSavePosition()
        else:
            self.buttonMemoryPressed = True
            bmp = wx.Bitmap("pos1-h.png", wx.BITMAP_TYPE_ANY)
            self.pos1Btn.SetBitmapLabel(bmp)
            bmp = wx.Bitmap("pos2-h.png", wx.BITMAP_TYPE_ANY)
            self.pos2Btn.SetBitmapLabel(bmp)
            self.gbUpBtn.Disable()
            self.gbDownBtn.Disable()        

    def saveCurrentHeightInConfig(self,savePos):
        config = load_config()
        config["positions"][savePos] = self.idasen_desk.current_height
        save_config(config)
    
    def disableSavePosition(self):
        self.buttonMemoryPressed = False
        bmp = wx.Bitmap("pos1.png", wx.BITMAP_TYPE_ANY)
        self.pos1Btn.SetBitmapLabel(bmp)
        bmp = wx.Bitmap("pos2.png", wx.BITMAP_TYPE_ANY)
        self.pos2Btn.SetBitmapLabel(bmp)
        self.gbUpBtn.Enable()
        self.gbDownBtn.Enable()        

# =============================================================================================
class PopMenu(wx.Menu):  
    def __init__(self, parent): 
        super(PopMenu, self).__init__() 
        self.parent = parent 
  
        # menu item 1         
        self._aotMenu = self.Append(wx.ID_ANY, 'Always on top', kind=wx.ITEM_CHECK) 
        self.Bind(wx.EVT_MENU, self.ToggleAlwaysOnTop, self._aotMenu)
                
        # menu item 2 
        #popmenu = wx.MenuItem(self, wx.ID_ANY, "Move to secondary screen") 
        #self.Append(popmenu) 

        # menu item 3
        #popmenu = wx.MenuItem(self, wx.ID_ANY, "Activate 4 positions") 
        #self.Append(popmenu) 

       
    def ToggleAlwaysOnTop(self, e):
        log("ToggleAlwaysOnTop")
                
        if self._aotMenu.IsChecked():
            log("ToggleAlwaysOnTop checked!")
            self.parent.SetWindowStyle(self.parent.defaultstyle | wx.STAY_ON_TOP)
            self._aotMenu.Check(True)
            _always_on_top = 1
        else:
            log("ToggleAlwaysOnTop unchecked!")
            self.parent.SetWindowStyle(self.parent.defaultstyle)
            self._aotMenu.Check(False)
            _always_on_top = 0
        # save in config    
        config = load_config()
        config["always_on_top"] = _always_on_top
        save_config(config)            
        
# =============================================================================================
# Run the program
if __name__ == "__main__":
   
    config = load_config()

    if config["log_to_file"] == 1:
        LOG_TO_CONSOLE = False
        logging.basicConfig(filename='myapp.log', level=logging.DEBUG)
        logging.info('Started')
    else:
        logging.basicConfig(level=logging.DEBUG)
        
    app = wx.App(False)
    logging.debug('Main App created')
    frame = MyForm()
    logging.debug('Main Form created')
    align_bottom_right(frame)    
    frame.Show()
    logging.debug('Main Starting MainLoop')
    app.MainLoop()
