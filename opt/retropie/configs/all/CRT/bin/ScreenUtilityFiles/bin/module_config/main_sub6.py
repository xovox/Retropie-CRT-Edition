#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Configuration Utility

https://github.com/krahsdevil/crt-for-retropie/

Copyright (C)  2018/2020 -krahs- - https://github.com/krahsdevil/

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU Lesser General Public License as published by the Free
Software Foundation, either version 2 of the License, or (at your option) any
later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License along
with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import sys, os, threading, time, commands, re
import logging

#sys.dont_write_bytecode = True

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(SCRIPT_DIR + "/../"))
from main_paths import MODULES_PATH
sys.path.append(MODULES_PATH)

from config_utils import explore_list, find_submenus, load_submenu, \
                         check_es_restart, run, check_sys_reboot
from launcher_module.core_paths import *
from launcher_module.file_helpers import *
from launcher_module.core_controls import CRT_UP, CRT_DOWN, \
                                          CRT_LEFT, CRT_RIGHT, CRT_OK, \
                                          CRT_CANCEL

LOG_PATH = os.path.join(TMP_LAUNCHER_PATH, "utility.log")
EXCEPTION_LOG = os.path.join(TMP_LAUNCHER_PATH, "backtrace.log")

FILE_NAME = os.path.splitext(os.path.basename(__file__))[0]
OPT_MASK = FILE_NAME + "_sub"

ROM_FILE = os.path.join(CRT_ADDN_PATH, "addon_credits/flappybird.gba")
RA_GBA_CFG_FILE1 = os.path.join(RETROPIE_CFG_PATH, "gba/retroarch.cfg")
RA_GBA_CFG_FILE2 = os.path.join(CRT_RA_MAIN_CFG_PATH, "credits.cfg")
RA_GBA_CORE_FILE = os.path.join(CRT_ADDN_PATH,
                  "addon_credits/mgba_libretro.so")

class main_sub6(object):
    m_bPause = [False, False]
    m_oThreads = []
    m_bThreadsStop = True

    m_lLines = []
    m_lMainOpts = []
    m_lSubMenus = []
    m_lOptFn = []
    
    m_lCtrl = []
    m_lRestart = [__name__, False]
    m_lReboot = [__name__, False]

    m_lIcon = {'icon': 'icon_folder'}
    m_sSection = "06 Information"

    m_lLayer40 = [None, None] # text & icon label
    
    def __init__(self):
        self._load_options()
        self._load_sub_menus()

    def load(self):
        self.m_bThreadsStop = False
        self._create_threads()

    def info(self, p_sText = False, p_sIcon = False):
        self.m_lLayer40[0] = None
        self.m_lLayer40[1] = None
        if p_sText:
            self.m_lLayer40[0] = p_sText
            self.m_lLayer40[1] = p_sIcon

    def _create_threads(self):
        p_oDmns = [self._auto_load_datas]
        self.m_oThreads = []
        for dmn in p_oDmns:    
            t = threading.Thread(target=dmn)
            t.start()
            self.m_oThreads.append(t)

    def _auto_load_datas(self):
        p_lAutoL = [self.opt4, self.opt5]
        timer = 0.5 # look for datas timer
        if p_lAutoL:
            while not self.m_bThreadsStop:
                for opt in p_lAutoL:
                    self._reload_opt_datas(opt)
                time.sleep(timer)
                
    def _load_options(self):
        p_lOptFn = [self.opt1, self.opt2, self.opt3,
                    self.opt4, self.opt5, self.opt6,
                    self.opt7, self.opt8, self.opt10]
        self.m_lOptFn = p_lOptFn
        for opt in self.m_lOptFn:
            self.m_lMainOpts.append(opt)
            self.m_lLines.append(opt())
            self.m_lCtrl.append(opt())

    def _reload_opt_datas(self, opt = None):
        pos = self.m_lMainOpts.index(opt)
        if opt: self.m_lLines[pos].update(opt())

    def _launch_app(self, p_sCommand, p_sDBSys = None):
        self.m_bPause[0] = True
        self.m_bThreadsStop = True
        run(p_sCommand, p_sDBSys)
        self.m_bPause[0] = False
        self.m_bThreadsStop = False

    def _load_sub_menus(self):
        submenus = []
        try:
            for sbm in find_submenus(SCRIPT_DIR, OPT_MASK):
                logging.info("Loading main menu option: %s " % sbm["name"])
                sub = load_submenu(sbm)
                submenus.append(sub())

            if len(self.m_lLines) != 0:
                for i in range (0, len(self.m_lLines)):
                    self.m_lSubMenus.append(None)
            for sub in submenus:
                self.m_lSubMenus.append(sub)                
            
            for sbm in self.m_lSubMenus:
                if sbm:
                    temp = {}
                    temp.update({'text': sbm.m_sSection})
                    temp.update({'icon': sbm.m_lIcon['icon']})
                    temp.update({'color_txt': "type_color_2"})
                    self.m_lLines.append(temp)
        except:
            raise

    def opt1(self, p_iJoy = None, p_iLine = None):
        p_lLines = {}
        if p_iJoy == None:
            return self.opt1_datas()

    def opt1_datas(self):
        p_lLines = {'text': "System", 
                    'value': "CRT Edition",
                    'color_val': "type_color_1"}
        return p_lLines

    def opt2(self, p_iJoy = None, p_iLine = None):
        p_lLines = {}
        if p_iJoy == None:
            return self.opt2_datas()

    def opt2_datas(self):
        p_lLines = {'text': "Version",
                    'color_val': "type_color_1"}
        value = (" ".join(ini_getlist(CRT_UTILITY_FILE, "version"))).strip()
        value = re.sub(r' +', " ", value).replace('"', '')
        p_lLines.update({'value': value})
        return p_lLines

    def opt3(self, p_iJoy = None, p_iLine = None):
        p_lLines = {}
        if p_iJoy == None:
            return self.opt3_datas()

    def opt3_datas(self):
        p_lLines = {'color_val': "type_color_1"}
        value = commands.getoutput('cat /proc/device-tree/model')
        value = value.replace('Raspberry Pi', '')
        value = value.replace(' Model ', '')
        value = value.replace(' Plus', '+')
        value = value.replace('Rev ', 'Rev')
        value = value.replace('\00', '').strip()
        value = re.sub(r' +', " ", value)
        p_lLines.update({'text': "Raspberry Pi"})
        p_lLines.update({'value': value})
        return p_lLines

    def opt4(self, p_iJoy = None, p_iLine = None):
        p_lLines = {}
        if p_iJoy == None:
            return self.opt4_datas()

    def opt4_datas(self):
        p_lLines = {'text': "Storage",
                    'color_val': "type_color_1"}
        disk = "/dev/root"
        if os.path.exists (CRT_EXTSTRG_TRIG_MNT_PATH):
            with open(CRT_EXTSTRG_TRIG_MNT_PATH, "r+") as f:
                new_file = f.readlines()
                line = new_file[0]
                disk = line.strip().split(" ")[0]

        tmp = commands.getoutput('df -h | grep %s' % disk)
        tmp = re.sub(r' +', " ", tmp).strip().split(" ")
        try: space = tmp[3] + '/' + tmp[1] + '(' + tmp[4] + ')'
        except: space = "CALCULATING..."
        p_lLines.update({'value': space})
        return p_lLines

    def opt5(self, p_iJoy = None, p_iLine = None):
        p_lLines = {}
        if p_iJoy == None:
            return self.opt5_datas()

    def opt5_datas(self):
        p_lLines = {'color_val': "type_color_1"}
        temp = commands.getoutput('vcgencmd measure_temp')
        temp = temp.strip().split("=")[1]
        p_lLines.update({'text': "Temperature"})
        p_lLines.update({'value': temp})
        return p_lLines

    def opt6(self, p_iJoy = None, p_iLine = None):
        p_lLines = {}
        if p_iJoy == None:
            return self.opt6_datas()

    def opt6_datas(self):
        p_lLines = {'color_val': "type_color_1"}
        p_lLines.update({'text': "Games Played"})
        value = 0
        if os.path.exists(CRT_STATS_FILE):
            with open(CRT_STATS_FILE, 'r') as f:
                for line in f:
                    if "played_" in line:
                        system = line.replace(' ', '').replace('"', '').strip()
                        system = system.split("=")[1]
                        value += int(system)
        p_lLines.update({'value': value})
        return p_lLines

    def opt7(self, p_iJoy = None, p_iLine = None):
        p_lLines = {}
        if p_iJoy == None:
            return self.opt7_datas()

    def opt7_datas(self):
        p_lLines = {'color_val': "type_color_1"}
        p_lLines.update({'text': "Time Played"})
        value = 0
        if os.path.exists(CRT_STATS_FILE):
            value = int(ini_get(CRT_STATS_FILE, 'timer'))
        m, s = divmod(value, 60)
        h, m = divmod(m, 60)
        
        value = "%sh %sm" % (h, m)        
        p_lLines.update({'value': value})
        return p_lLines

    def opt8(self, p_iJoy = None, p_iLine = None):
        p_lLines = {}
        if p_iJoy == None:
            return self.opt8_datas()

    def opt8_datas(self):
        p_lLines = {'color_val': "type_color_1"}
        p_lLines.update({'text': "TOP System"})
        value = "Not Played"
        counter = 0
        if os.path.exists(CRT_STATS_FILE):
            with open(CRT_STATS_FILE, 'r') as f:
                for line in f:
                    if "timer_" in line:
                        system = line.replace(' ', '').replace('"', '').strip()
                        play = int(system.split("=")[1])
                        if play > counter: 
                            counter = play
                            value = system.split("=")[0].replace("timer_", '')
                            value = value.upper()
        p_lLines.update({'value': value})
        return p_lLines

    def opt10(self, p_iJoy = None, p_iLine = None):
        p_lLines = {}
        if p_iJoy == None:
            return self.opt10_datas()
        if p_iJoy & CRT_OK:
            commandline = "%s -L %s " % (RA_BIN_FILE, RA_GBA_CORE_FILE)
            commandline += "--config %s " % RA_GBA_CFG_FILE1
            commandline += "--appendconfig %s " % RA_GBA_CFG_FILE2
            commandline += "\"%s\" " % ROM_FILE
            commandline += "> /dev/null 2>&1"
            self._launch_app(commandline, "gba")

    def opt10_datas(self):
        p_lLines = {'text': "Credits",
                    'color_txt': "type_color_2",
                    'icon': "icon_bin"}
        return p_lLines
        
    def input(self, p_iLine, p_iJoy):
        if p_iJoy & CRT_CANCEL:
            self.quit()
            return CRT_CANCEL # False: back to previous menu
        else:
            if p_iLine > (len(self.m_lOptFn) - 1):
                if p_iJoy & CRT_OK: return self.m_lSubMenus[p_iLine]
            else:
                self.m_lMainOpts[p_iLine](p_iJoy, p_iLine)
                self.m_lRestart[1] = check_es_restart(self.m_lLines, self.m_lCtrl)
                self.m_lReboot[1] = check_sys_reboot(self.m_lLines, self.m_lCtrl)

    def quit(self):
        self.m_bThreadsStop = True
        self.info()