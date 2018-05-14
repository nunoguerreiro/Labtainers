#!/usr/bin/env python
'''
This software was created by United States Government employees at 
The Center for the Information Systems Studies and Research (CISR) 
at the Naval Postgraduate School NPS.  Please note that within the 
United States, copyright protection is not available for any works 
created  by United States Government employees, pursuant to Title 17 
United States Code Section 105.   This software is in the public 
domain and is not subject to copyright. 
'''
import os
import subprocess
import argparse
import time
import shlex
import signal
import sys
'''
Use xdotool to simulate a lab being performed, as driven by
a simthis.txt file
'''
def isProcRunning(proc_string):
    ''' return True if given string in ps -ao args '''
    time.sleep(0.5)
    cmd = 'ps -ao args'
    ps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = ps.communicate()
    for line in output[0].splitlines():
        #print('is %s in %s' % (proc_string, line))
        if proc_string in output[0]:
            return True
    return False

def DockerCmd(cmd):
    ok = False
    count = 0
    while not ok:
        #print("Command to execute is (%s)" % cmd)
        ps = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        output = ps.communicate()
        if len(output[1]) > 0:
            count += 1
            #print("Failed cmd %s %s" % (cmd, output[1]))
            if count > 1:
                return False, ""
            time.sleep(1)
        else:
            if len(output[0]) > 0:
                #print("cmd %s stdout: %s" % (cmd, output[0]))
                return True, output[0]
            else:
                #print("cmd %s stdout: ''" % cmd)
                ok = True
    return True, ""

class SimLab():
    def __init__(self, lab, verbose_level=0, logger=None):
        self.sim_path = os.path.abspath(os.path.join('../../../simlab', lab))
        self.labname = lab
        self.current_wid = None
        self.logger = logger
        print('set verbose to %s' % verbose_level)
        self.verbose_level = verbose_level

        # For dconf - HUD setting
        self.dconf_enable = None
        self.dconf_orig_hud_string_set = None
        self.dconf_hud_string = ""

        if not os.path.isdir(self.sim_path):
            return None

    def hasSim(self):
        if os.path.isdir(self.sim_path):
            return True
        else:
            return False

    def getExpectedPath(self):
        return os.path.join(self.sim_path, 'expected')

    def dotool(self, cmd):
        cmd = 'xdotool %s' % cmd
        #print('dotool cmd: %s' % cmd)
        ps = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = ps.communicate()
        if len(output[1]) > 0:
            print output[1]
        return output[0].strip()
    
    
    def searchWindows(self, name):
        ''' find the most recent window whose title matches the given name.
            The title "Terminal" seems to return most windows, so double check
            the name against the getWindowname results.
        '''
        wid = None
        count = 0
        while wid is None or len(wid) == 0:
            count += 1
            if count > 20:
                print('searchWindows failed to find %s after 20 seconds, exit' % name)
                exit(1)
            time.sleep(1)
            cmd = 'search %s' % name
            #print('searchWindows %s' % cmd)
            output=self.dotool(cmd)
            #print('output is %s' % output)
            parts = output.strip().split()
            if len(parts) == 1:
                #print('search out is %s' % output)
                twid = output.rsplit(' ',1)[0].strip()
                cmd = 'getwindowname %s' % twid
                wname = self.dotool(cmd)
                if name.strip('"') in wname:
                    wid = output.rsplit(' ',1)[0].strip()
            elif len(parts)>0:
                for twid in sorted(parts, reverse=True):
                    cmd = 'getwindowname %s' % twid
                    wname = self.dotool(cmd)
                    if name.strip('"') in wname:
                        #print('wid: %s  wname is %s' % (twid, wname))
                        wid = twid
                        break
        return wid
    
    def activate(self, wid):
        self.current_wid = int(wid)
        cmd = 'windowactivate --sync %s' % wid
        self.dotool(cmd)
    
    def typeLine(self, string):
        #cmd = "type --window %d '%s'" % (self.current_wid, string)
        cmd = 'type "%s\n"' % (string)
        self.dotool(cmd)
        #cmd = 'key Return'
        #self.dotool(cmd)
    
    def commandFile(self, fname):
        full = os.path.join(self.sim_path, fname)
        with open(full) as fh:
            for line in fh:
                if len(line.strip()) > 0:
                    self.typeLine(line.strip())
                    while isProcRunning(line.strip()):
                        print('%s running, wait' % line.strip())
                        time.sleep(1)
                # at least one to avoid timestamp collisions
                time.sleep(1)
                    
    def typeFile(self, fname):
        full = os.path.join(self.sim_path, fname)
        with open(full) as fh:
            for line in fh:
                if line.strip().startswith('#'):
                    print('verbose level %d' % self.verbose_level)
                    if self.verbose_level >= 1:
                        print('%s' % line.strip())
                    continue
                if len(line.strip()) > 0:
                    if self.verbose_level == 2:
                        print('cmd: %s' % line.strip())
                    self.typeLine(line.strip())
                    time.sleep(1.1)
                else:
                    #print 'sleep 2'
                    time.sleep(2)

    def keyFile(self, fname):
        full = os.path.join(self.sim_path, fname)
        with open(full) as fh:
            for line in fh:
                if line.strip().startswith('#'):
                    if self.verbose_level >= 1:
                        print('%s' % line.strip())
                    continue
                if len(line.strip()) > 0:
                    if self.verbose_level == 2:
                        print('key: %s' % line.strip())
                    send = "key %s" % line.strip()
                    self.dotool(send)
                    time.sleep(1.1)
                else:
                    #print 'sleep 2'
                    time.sleep(2)

    def addFile(self, params, replace=False):
        from_file, to_file = params.split()
        from_file = os.path.join(self.sim_path, from_file) 
        cmd = 'vi %s' % to_file
        self.typeLine(cmd.strip()) 
        if replace:
            cmd = "type '9999dd'"
            self.dotool(cmd)
        else:
            self.dotool("type 'G'")
        self.dotool("type 'i'")
        with open(from_file) as fh:
            for line in fh:
                self.typeLine(line.strip())
        self.dotool("key Escape")
        self.dotool("type 'ZZ'")
       
    def includeFile(self, fname):
        full = os.path.join(self.sim_path, fname)
        with open(full) as fh:
            for line in fh:
                if line.strip().startswith('#') or len(line.strip()) == 0:
                    if line.strip().startswith('#'):
                        if self.verbose_level >= 1:
                            print('%s' % line.strip())
                    continue
                #print line
                try:
                    cmd, params = line.split(' ', 1)
                except:
                    print('bad SimLab line: %s' % line)
                    exit(1)
                #print('cmd: %s params %s' % (cmd, params))
                self.handleCmd(cmd.strip(), params.strip())
                #print('back from handleCmd')

    def execNetStat_On_Container(self, labname, container_hosturl):
        ''' return True if the container_hosturl is found in netstat output '''
        waitNetURL_string = container_hosturl.split(':')
        if len(waitNetURL_string) != 2:
            print("Invalid wait_net container_hosturl string format!")
            exit(1)
        else:
            container = waitNetURL_string[0]
            full_containername = "%s.%s.student" % (labname, container)
            hosturl = waitNetURL_string[1]

        netstat_cmd = "sudo netstat -put -W | grep %s" % hosturl
        cmd = 'docker exec %s script -q -c "%s" /dev/null' % (full_containername, netstat_cmd)
        #print "cmd is (%s)" % cmd
        result, output_str = DockerCmd(cmd)
        #print('wait_net %r out is %s' % (result, output_str))
        if not result:
            print('failed %s' % cmd)
            exit(1)
        if result and output_str == "":
            #print "After DockerCmd, return False"
            return False
        else:
            for line in output_str.splitlines():
                if container_hosturl in line and "TIME_WAIT" not in line:
                    return True
            return False

    def waitNetURL(self, labname, container_hosturl):
        # wait for connection to establish
        time.sleep(1)
        while self.execNetStat_On_Container(labname, container_hosturl):
            #self.logger.debug('waiting for execNetStat_On_Container')
            time.sleep(1)
        time.sleep(1)
    
    def handleCmd(self, cmd, params):
        if self.logger is not None:
            self.logger.debug('cmd %s  params: %s' % (cmd, params))
        if self.verbose_level == 2:
            print('%s: %s' % (cmd, params))
        if cmd == 'window':
            wid = self.searchWindows(params)
            self.activate(wid)
        elif cmd == 'include':
            self.includeFile(params)
        elif cmd == 'type_file':
            self.typeFile(params)
        elif cmd == 'key_file':
            self.keyFile(params)
        elif cmd == 'type_line':
            self.typeLine(params.strip())
        elif cmd == 'command_file':
            self.commandFile(params)
        elif cmd == 'command':
            self.dotool(params)
        elif cmd == 'add_file':
            self.addFile(params)
        elif cmd == 'replace_file':
            self.addFile(params, True)
        elif cmd == 'key':
            send = "key %s" % params
            self.dotool(send)
            time.sleep(0.2)
        elif cmd == 'rep_key':
            parts = params.split()
            quant = int(parts[0])
            the_key = parts[1]
            send = "key %s" % the_key
            for i in range(quant):
                self.dotool(send)
                time.sleep(0.3)
        elif cmd == 'wait_net':
            self.waitNetURL(self.labname, params)
        elif cmd == 'wait_proc':
            while isProcRunning(params):
                print('%s running, wait' % params)
                time.sleep(1)
        elif cmd == 'sleep':
            time.sleep(int(params))
        else:
            print('Unknown command %s %s' % (cmd, params))

    def signal_handler(self, signum, frame):
        #self.logger.debug("Signal handle called with signal", signum)
        self.reset_dconf_hud_settting()
        # Caught a SIGTERM signal exiting after reset dconf HUD setting
        sys.exit(1)

    def reset_dconf_hud_settting(self):
        result = 0
        if self.dconf_enable:
            if self.dconf_orig_hud_string_set:
                command = "/usr/bin/dconf write /org/compiz/integrated/show-hud %s" % self.dconf_hud_string
            else:
                command = "/usr/bin/dconf write /org/compiz/integrated/show-hud"
            #self.logger.debug("Command is (%s)" % command)
            ps = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = ps.communicate()
            if len(output[1]) > 0:
                result = 1
                #self.logger.debug("Failed to set hud_string to %s" % self.dconf_hud_string)
            #else:
            #    self.logger.debug("Set hud_string to %s is successful" % self.dconf_hud_string)
        return result

    def change_dconf_hud_setting(self):
        result = 0
        if self.dconf_enable:
            command = "/usr/bin/dconf write /org/compiz/integrated/show-hud '[\"\"]'"
            #self.logger.debug("Command is (%s)" % command)
            ps = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = ps.communicate()
            if len(output[1]) > 0:
                result = 1
                #self.logger.debug("Failed to set hud_string to '[\"\"]'")
            #else:
            #    self.logger.debug("Set hud_string to '[\"\"]' is successful")
        return result

    def get_orig_dconf_hud_setting(self):
        result = 0
        if self.dconf_enable:
            command = "/usr/bin/dconf read /org/compiz/integrated/show-hud"
            #self.logger.debug("Command is (%s)" % command)
            ps = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = ps.communicate()
            if len(output[0]) > 0:
                self.dconf_orig_hud_string_set = True
                #print "output[0] is (%s)" % output[0].strip()
                self.dconf_hud_string = output[0].strip()
            else:
                self.dconf_orig_hud_string_set = False
                result = 1
            #if self.dconf_orig_hud_string_set:
            #    print "hud_string is (%s)" % self.dconf_hud_string
            #else:
            #    print "hud_string is not SET!"
        return result

    def test_for_program(self, myprogram):
        command = "which %s > /dev/null" % myprogram
        if os.system(command) == 0:
            #self.logger.debug("program (%s) exists/installed" % myprogram)
            return 0
        else:
            #self.logger.debug("program (%s) does not exists/not installed" % myprogram)
            return 1
    
    def simThis(self):
        fname = os.path.join(self.sim_path, 'simthis.txt')
        if self.logger is not None:
            self.logger.debug('smithThis for %s' % fname)

        # Test for dconf first
        if self.test_for_program("dconf") != 0:
            #self.logger.debug("NO dconf support")
            self.dconf_enable = False
            self.dconf_orig_hud_string_set = False
        else:
            self.dconf_enable = True
            self.get_orig_dconf_hud_setting()
            self.change_dconf_hud_setting()

        # Setup signal handler for SIGINT
        signal.signal(signal.SIGINT, self.signal_handler)

        with open(fname) as fh:
            for line in fh:
                if line.strip().startswith('#') or len(line.strip()) == 0:
                    if line.strip().startswith('#'):
                        if self.verbose_level >= 1:
                            print('%s' % line.strip())
                    continue
                #print line
                try:
                    cmd, params = line.split(' ', 1)
                except:
                    print('bad SimLab line: %s' % line)
                    exit(1)
                #print('cmd: %s params %s' % (cmd, params))
                self.handleCmd(cmd.strip(), params.strip())
                #print('back from handleCmd')

        # Finish processing, reset dconf HUD setting
        self.reset_dconf_hud_settting()

def __main__():
    parser = argparse.ArgumentParser(description='Simulate student performing lab')
    parser.add_argument('labname', help='The lab to simulate')
    parser.add_argument('-v', '--verbose', action='count', default=0, help="Use -v to see comments as they are encountered, -vv to see each line")
    args = parser.parse_args()
    lab = args.labname
    verbose_level = int(args.verbose)
    #print("lab is (%s)" % lab)
    #print("verbose_level is (%d)" % verbose_level)
    if verbose_level > 2:
        print("Verbose level up to 2 only!")
        exit(1)
    simlab = SimLab(lab, verbose_level)
    simlab.simThis() 

if __name__=="__main__":
    __main__()
