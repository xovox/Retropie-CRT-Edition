#!/usr/bin/python
# -*- coding: utf-8 -*-


"""
launcher core.py.

launcher library for retropie, based on original idea - Ironic
  and the retropie integration work by -krahs-

https://github.com/krahsdevil/crt-for-retropie/

Copyright (C)  2018/2019 -krahs- - https://github.com/krahsdevil/
Copyright (C)  2019 dskywalk - http://david.dantoine.org

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


import os, sys
import subprocess, commands
import logging

from .screen_helpers import crt_open_screen_from_timings_cfg, es_restore_screen
from .utils import something_is_bad, splash_info
from .file_helpers import *

__VERSION__ = '0.1'
__DEBUG__ = logging.INFO # logging.ERROR
CLEAN_LOG_ONSTART = True

TMP_LAUNCHER_PATH = "/dev/shm"
TMP_SPEEPER_NAME = "lchtmp"
TMP_SLEEPER_FILE = os.path.join(TMP_LAUNCHER_PATH, TMP_SPEEPER_NAME)
LEGACY_SLEEPER_FILE = "/tmp/lchtmp"

LOG_PATH = os.path.join(TMP_LAUNCHER_PATH, "CRT_Launcher.log")

# retropie path setup
__RETROPIE_PATH = "/opt/retropie"
RETROPIECFG_PATH = os.path.join(__RETROPIE_PATH, "configs")
RETROPIEEMU_PATH = os.path.join(__RETROPIE_PATH, "emulators")
CRTROOT_PATH = os.path.join(RETROPIECFG_PATH, "all/CRT")
__CRTBIN_PATH = os.path.join(CRTROOT_PATH, "bin")

CRT_RUNCOMMAND_FORMAT = "touch %s && sleep 1 && "
RUNCOMMAND_FILE = os.path.join(__RETROPIE_PATH, "supplementary/runcommand/runcommand.sh")

CFG_VIDEOMODES_FILE = os.path.join(RETROPIECFG_PATH, "all/videomodes.cfg")

CFG_FIXMODES_FILE = os.path.join(__CRTBIN_PATH, "ScreenUtilityFiles/modes.cfg")
CFG_VIDEOUTILITY_FILE = os.path.join(__CRTBIN_PATH,"ScreenUtilityFiles/utility.cfg")
CFG_NETPLAY_FILE = os.path.join(CRTROOT_PATH, "netplay.cfg")
CFG_TIMINGS_FILE = os.path.join(CRTROOT_PATH, "Resolutions/base_systems.cfg")


# FIXME: arcade
RC_ADVANCEDMAME_FILE = os.path.join(__RETROPIE_PATH, "mame-advmame/advmame.rc")
__ARCADE_PATH = TMP_LAUNCHER_PATH
__ARCADE_FILE = "retroarcharcade"
CFG_ARCADE_FILE = "%s%s.cfg" % (__ARCADE_PATH, __ARCADE_FILE)


class launcher(object):
    """ virtual class for crt launcher """
    m_sFileName = ""
    m_sCfgSystemPath = ""
    m_sSystemFreq = ""
    m_sBinarySelected = ""
    m_lBinaryMasks = []
    m_lBinaries = []
    m_lProcesses = []

    m_oRunProcess = None

    def __init__(self, p_sFilePath, p_sSystem, p_sCustom):
        self.m_sSystem = p_sSystem
        self.m_sCustom = p_sCustom
        self.m_sFilePath = p_sFilePath
        self.m_sFileName = os.path.basename(self.m_sFilePath)
        self.m_sGameName = os.path.splitext(self.m_sFileName)[0]

        self.__temp()
        self.__clean()
        logging.info("INFO: arg 1 (rom_path) = %s, (system) = %s, (sin uso) = %s"
            % (self.m_sFilePath, self.m_sSystem, self.m_sCustom))

        self.init() # user virtual method get init values
        self.setup() # rom name work
        self.configure() # user virtual method for post configure
        self.check() # check runcommand string
        self.run() # launch, wait and cleanup

    def check(self):
        self.netplay_setup()
        self.runcommand_check()

    def run(self):
        self.start()
        self.wait()
        self.cleanup()

    def start(self):
        self.runcommand_start()
        self.screen_set()

    def wait(self):
        self.m_oRunProcess.wait()
        logging.info("process end")

    # setup paths - called by __init__()
    def setup(self):
        self.video_setup()
        self.system_setup()

    # TODO: Read data from EasyNetplay
    def netplay_setup(self):
        self.m_sNetIP = ""

    def system_setup(self):
        self.m_sSystemFreq = self.m_sSystemVideoName
        self.m_sCfgSystemPath = os.path.join(RETROPIECFG_PATH, self.m_sSystem, "emulators.cfg")

    def video_setup(self):
        self.m_sSystemVideoName = self.m_sSystem

    # called children init at start, called by __init__()
    def configure(self):
        pass

    def init(self):
        pass

    # generate command string
    # just called if need rebuild the CMD
    def runcommand_generate(self, p_sCMD):
        p_sCMD = p_sCMD.replace('"','').strip()
        new_cmd = self.m_sBinarySelected + " = \""
        new_cmd += CRT_RUNCOMMAND_FORMAT % TMP_SLEEPER_FILE
        new_cmd += p_sCMD + "\""
        return new_cmd

    def runcommand_clean(self, p_sCMD):
        # first remove quotes
        p_sCMD = p_sCMD.replace('"', '')
        # "touch /path/lchtmp && sleep 1 && /path/retroarch ...
        # "/path/retroarch ...
        if "&&" in p_sCMD:
            p_sCMD = p_sCMD.split("&&")[-1]
        # ... --appendconfig /path/system.cfg %ROM%"'
        # ... %ROM%"'
        if "--appendconfig" in p_sCMD:
            p_sCMD = p_sCMD.split("--appendconfig")[0]
        # add at the end
        if "%ROM%" not in p_sCMD:
            p_sCMD += "%ROM%"
        # finally add quotes
        p_sCMD = '"' + p_sCMD.strip() + '"'
        return p_sCMD

    # check if runcommand has correct behaivor:
    #   FROM emulator-binary-name = "command-to-launch-the-game"
    #   TO   emulator-binary-name = "crt-command && command-to-launch-the-game"
    def runcommand_check(self):
        f = open(self.m_sCfgSystemPath, "r")
        new_file = f.readlines()
        f.close()
        # only change file if is need it
        for line in new_file:
            lValues = line.strip().split('=')
            lValues = map(lambda s: s.strip(), lValues)
            if lValues[0] == self.m_sBinarySelected:
                cmd_cleaned = self.runcommand_clean(lValues[1])
                cmd_current = self.runcommand_generate(cmd_cleaned)
                if cmd_current != line.strip(): # atm just force our cmd
                    logging.info("changed command (%s)" % cmd_current)
                    modify_line(self.m_sCfgSystemPath, line, cmd_current)


    # wait_runcommand: wait for user launcher menu
    #   @full_checks: off, just check current process.
    #   return: True, if user wants close emulation directly.
    def runcommand_wait(self, full_checks = True):
        if not self.m_lProcesses:
            self.panic("processes not available")

        logging.info("wait runcommand ends and start: %s (full_checks: %s)" % (str(self.m_lProcesses), str(full_checks)) )
        # TODO: better use a symple socket daemon
        while True:
            if full_checks:
                if os.path.exists(TMP_SLEEPER_FILE):
                    logging.info("detected trigger file %s, wait finished..." % TMP_SLEEPER_FILE)
                    return False
                # try to detect if user exits from runcommand
                poll = self.m_oRunProcess.poll()
                if poll != None:
                    logging.info("runcommand closed by user (poll = %s)" % poll)
                    RuncommandClosed = True
                    return True
            output = commands.getoutput('ps -A')
            for proc in self.m_lProcesses:
                if proc in output:
                    logging.info("detected %s in active process, wait finished...", proc)
                    return False

    def runcommand_start(self):
        """ launch_core: run emulator!"""
        commandline = "%s 0 _SYS_ %s \"%s\"" % (RUNCOMMAND_FILE, self.m_sSystem, self.m_sFilePath)
        self.m_oRunProcess = subprocess.Popen(commandline, shell=True)
        logging.info("Subprocess running: %s", commandline)
        self.runcommand_wait()

    def screen_set(self):
        crt_open_screen_from_timings_cfg(self.m_sSystemFreq, CFG_TIMINGS_FILE)
        try:
            splash_info("black") # clean screen
        except Exception as e:
            logging.error("splash failed: %s" % e)
        logging.info("clean: %s", TMP_SLEEPER_FILE)
        remove_file(TMP_SLEEPER_FILE)

    def panic(self, p_sErrorLine1, p_sErrorLine2 = "-", p_bForceQuit = True):
        """ stop the program and show error to the user """
        logging.error("PANIC: %s" % p_sErrorLine1)
        something_is_bad(p_sErrorLine1, p_sErrorLine2)
        if p_bForceQuit:
            logging.error("EXIT: crt_launcher forced")
            self.__clean()
            sys.exit(1)

    # cleanup code

    def cleanup(self):
        es_restore_screen()
        logging.info("ES mode recover")
        os.system('clear')
        self.__clean()
        sys.exit()

    # clean system
    def __clean(self):
        self.clean_videomodes()
        remove_file(TMP_SLEEPER_FILE)

    def clean_videomodes(self):
        try:
            os.remove(CFG_VIDEOMODES_FILE)
        except OSError:
            return False
        return True

    def __temp(self):
        if CLEAN_LOG_ONSTART:
            remove_file(LOG_PATH)
        logging.basicConfig(filename=LOG_PATH, level=__DEBUG__, format='[%(asctime)s] %(levelname)s - %(filename)s:%(funcName)s - %(message)s')
