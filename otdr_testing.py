import string
import re
import os
from module import Module
import pandas as pd
import matplotlib.pyplot as plt
import time
import datetime

if __name__=='__main__':
    dut = Module('COM64')
    dut.ask('key 1')
    ver = dut.ask('ver')
    sn = ver.split()[-2]
    #reflector = Module('COM8')
    file_dir = 'condition/spec for Galactus.xlsx'
    result_dir = 'results'
    spec = pd.read_excel(file_dir)
    n = len(spec)
    m = len(spec.keys())
    for i in range(n):
        condition = 'condition_%s' % spec.iloc[i, 0]
        otdr = spec.iloc[i, 1]
        voa1 = spec.iloc[i, 2]
        voa2 = spec.iloc[i, 3]
        voa3 = spec.iloc[i, 4]
        pos = spec.iloc[i, 5]
        print pos
        dut.ask('osw %s pos %s' % (otdr, pos))
        print dut.ask('osw %s pos' % otdr)
     #   reflector.ask('key 1')
     #   reflector.ask('voa 1 man setpos %f' % voa1)
     #   reflector.ask('voa 2 man setpos %f' % voa2)
     #   reflector.ask('voa 3 man setpos %f' % voa3)
        for j in range(6, m, 1):
            dut.ask('otdr %s %s %f' % (otdr, spec.keys()[j], spec.iloc[i, j]))
            time.sleep(1)
        print '8888888888888888888888888888888888888888888888888888888881212121212121212121212121212'
        print '*************************************************************************************'

      #  print reflector.ask('voa 1 all')
      #  print reflector.ask('voa 2 all')
      #  print reflector.ask('voa 3 all')
        mode = dut.ask('osc %s mode' % otdr)
        mode = mode.split(':')
        mode1 = mode[1].strip()
        if mode1 == 'OSC\r\n>':
            dut.ask('key 1')
            dut.ask('osc %s mode otdr' % otdr)
            dut.ask('power txen1 on')
            dut.ask('power txen2 on')
            dut.ask('otdr %s run' % otdr)
            while True:
                stat = dut.ask('otdr %s status' % otdr)
                stat_new = stat.split()[-2]
                if stat_new == 'IDLE':
                    t = datetime.datetime.now()
                    t_new = t.strftime('%Y-%m-%d_%H-%M-%S')
                    f = open('%s\%s_%s_%s.csv' % (result_dir, sn, condition, t_new), 'w')
                    cmds = ['ver full', 'MT', 'restart', 'otdr %s' % otdr, 'osw %s pos' % otdr,
                            'otdr %s x' % otdr, 'otdr %s dump trace' % otdr, 'otdr %s dump event' % otdr]
                    for cmd in cmds:
                        log = dut.ask('%s' % cmd)
                        # print log
                        time.sleep(3)
                        f.write(log + '\n')
                    f.close()
                    break
                else:
                    print '&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&_________________________'
                    print dut.ask('otdr %s status' % otdr)
                    time.sleep(2)
                    continue
        else:
            dut.ask('otdr %s run' % otdr)
            while True:
                stat = dut.ask('otdr %s status' % otdr)
                stat_new = stat.split()[-2]
                if stat_new == 'IDLE':
                    t = datetime.datetime.now()
                    t_new = t.strftime('%Y-%m-%d_%H-%M-%S')
                    f = open('%s\%s_%s_%s.csv' % (result_dir, sn, condition, t_new), 'w')
                    cmds = ['ver full', 'MT', 'restart', 'otdr %s' % otdr, 'osw %s pos' % otdr,
                            'otdr %s x' % otdr, 'otdr %s dump trace' % otdr, 'otdr %s dump event' % otdr]
                    for cmd in cmds:
                        log = dut.ask('%s' % cmd)
                        # print log
                        time.sleep(3)
                        f.write(log + '\n')
                    f.close()
                    break
                else:
                    print '&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&____****____****'
                    print dut.ask('otdr %s status' % otdr)
                    time.sleep(2)
                    continue
