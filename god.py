# -*- coding: utf8 -*-
__author__    = "Yaroslav Berezhinskiy"
__copyright__ = "Copyright (C) 2011 Yaroslav Berezhinskiy"
 
import os
import atexit
import sys
import time
from signal import SIGTERM 
import logging
 
#===========================================================================
# "Итерация свойственна человеку, рекурсия божественна." 
# Видно, у Б-га стек длинный. А мы останемся людьми.
#===========================================================================
 
class Daemon():
    pidfile = 'pidfile.pid'
    stdin='/dev/null'
    stdout='/dev/null'
 
    def daemonize(self):
        pid = os.fork()
        if pid == 0:
            os.setsid()
            pid = os.fork()
            if pid == 0:
                os.chdir(".")
                os.umask(0) 
            else:
                sys.exit(0)
        else:
            sys.exit(0)
 
        atexit.register(self.delpid)
         
        pid = str(os.getpid())
        file(self.pidfile,'w+').write("%s\n" % pid)
        return pid
 
    def descriptors(self):
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
  
    def delpid(self):
        os.remove(self.pidfile)
  
    def start(self,interactive=False):
        if interactive:
            print "Starting program in interactive mode"
            self.run()
            return
         
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
  
        if pid:
            message = "Daemon already running? (pid=%s)\n"
            sys.stderr.write(message % pid)
            sys.exit(1)
 
        pid = self.daemonize()
        print "Starting daemon."
        self.descriptors()
        self.run()
  
    def stop(self):
        try:
            pf = file(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
  
        if not pid:
            message = "Daemon not running? (check %s)\n"
            sys.stderr.write(message % self.pidfile)
            return
 
        print "Stopping daemon.\nWaiting for PID: %s" % pid
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print str(err)
                sys.exit(1)
  
    def restart(self):
        self.stop()
        self.start()
         
    def run(self):
        print >> sys.stderr, "ERROR: Daemon not started\nYou need to override run() method in your subclass!"
        sys.exit(1)


class SanctaDaemon(Daemon):

    def __init__(self, *args, **kwargs):
        self.pidfile = self.pidfile_path

        self.logger = logging.getLogger("DaemonLog")
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler = logging.FileHandler(self.logfile_path)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def ritual(self):
        if len(sys.argv) >= 2:
            if 'start' == sys.argv[1]:
                self.start()
            elif 'stop' == sys.argv[1]:
                self.stop()
            elif 'restart' == sys.argv[1]:
                self.restart()
            else:
                print "Unknown command"
        else:
            print "ritual das't exists"
        sys.exit(2)