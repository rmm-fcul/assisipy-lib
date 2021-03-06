#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
A script to execute behavioural programs for multiple bees (agents) in the
assisi playground.  This script executes one handler for each agent that is
in the agent listing file.  Each agent will have a unique name, and since the
execution file and local config (parameterisation) is also defined for each
agent, it is possible to have heterogeneous agents or agents of multiple types
simulated.

Once the script has connected to all agent handlers, pressing ctrl-c will
propogate to all the handlers, which gives them a chance to close gracefully.

Rob Mills - FCUL, BioISI & ASSISIbf

'''


import os
import signal, subprocess
import time, datetime
import argparse

import specs
from assisipy_utils import tool_version

'''
# The os.setsid() is passed in the argument preexec_fn so
# it's run after the fork() and before  exec() to run the shell.
pro = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            shell=True, preexec_fn=os.setsid)

os.killpg(pro.pid, signal.SIGTERM)  # Send the signal to all the process groups
'''




def main():
    ''' execute the handler for all agents in one or many agent specification listings '''
    parser = argparse.ArgumentParser()
    tool_version.ap_ver(parser)
    # input
    parser.add_argument('-ol', '--obj-listing', type=str, required=True, nargs='+',
            help='files listing all objects spawned in enki simulator (one or more)') # no default
    # output
    parser.add_argument('--logpath', type=str, required=True,
                        help="path to record output in")
    parser.add_argument('-so', '--stdout-logfile', type=str, default='/tmp/bee_output.txt',
            help='capture the standard output from all executed models')
    #parser.add_argument('-lc', '--local-conf', type=str, default=None,
    #        help='local configuration for bee behaviour')
    #parser.add_argument('-e', '--exec-script', type=str, default='./bee_behav.py',
    #        help='name of script to execute for each bee in `bee-file`')
    args = parser.parse_args()


    # extract info from specs
    agent_data = []
    for grp in args.obj_listing:
        _ad = specs.read_agent_handler_data(grp)
        agent_data += _ad
    # check for duplicates (agents managed by their name)
    a_names = [d.get('name') for d in agent_data ]
    _longest = len( max(a_names, key=lambda p: len(p)) )

    # and summarise
    print "[I] {} agents to run:".format(
            len(agent_data), )
    print "\t{:{fwid}} ({:4})  {:20} {:20}".format('agent',  'type', 'behav', 'config', fwid=_longest+1)
    for d in agent_data:
        print "\t{:{fwid}} ({:4}): {:20} {:20}".format(
            d.get('name'),
            d.get('type'),
            d.get('exec_script'),
            d.get('conf'),
            fwid=_longest+1
        )
    if len(a_names) != len(set(a_names)):
        raise IOError, "[E] duplicates found in agent specification. aborting"


    # create/clear the "live output" log file
    if args.stdout_logfile is not None:
        f = open(args.stdout_logfile, 'w')
        f.close() # clear the logfile

    print "Started at:",  datetime.datetime.fromtimestamp(time.time())

    # launch n bee handlers
    p_handles = []
    for d in agent_data:
        print "Launching bee '{}'".format(d.get('name'))
        to_exec = "python {cmd} --logpath={logpath} -bn {agentname} -sa {sub} -pa {pub} -c {lc} #>> {lf}".format(
            agentname=d.get('name'),
            cmd=d.get('exec_script'), lc=d.get('conf'),
            logpath=args.logpath, lf=args.stdout_logfile,
            pub=d.get('pub_addr'), sub=d.get('sub_addr'),
        )

        print "  ", to_exec

        p = subprocess.Popen(to_exec, shell=True)
        #p = subprocess.Popen(to_exec, stdout=subprocess.PIPE, shell=True)
        p_handles.append(p)

    pids = [_p.pid for _p in p_handles]
    print "[I] PIDs are", pids
    #print " type kill -9 ", pids

    # wait for the user to ctrl-c, then kill all the individual scrupts
    try:
        print "[I] wrapper has pid", os.getpid()
        while True:
            time.sleep(0.17) # blocking without any sleep is V costly!
            # and all we are doing is waiting for a keyboard interrupt...
            pass
    except KeyboardInterrupt:
        print "\n"
        time.sleep(0.25)
        print "shutting down..."
        for  p in p_handles:
            print "  killing process ", p.pid
            #os.kill(p.pid, signal.CTRL_BREAK_EVENT)
            os.kill(p.pid, signal.SIGINT)


    time.sleep(0.5)
    print "[] (bee behav wrapper) Finished at:",  datetime.datetime.fromtimestamp(time.time())



if __name__ == '__main__':
    main()
