import os
import re
from scipy.interpolate import UnivariateSpline
from scipy.interpolate import InterpolatedUnivariateSpline
import matplotlib.pyplot as plt
#from matplotlib import animation
import pandas as pd
import numpy as np


def file_name(dir):
    ### find the file_name in the dirs, and return the file_name with root
    L = []
    for root, dirs, files in os.walk(dir):
        for file in files:
            if os.path.splitext(file)[1] == '.pdf':
                file1 = os.path.join(root, file)
                L.append(file1.replace('\\', '/'))
            elif os.path.splitext(file)[1] == '.txt':
                file1 = os.path.join(root, file)
                L.append(file1.replace('\\', '/'))
            elif os.path.splitext(file)[1] == '.csv':
                file1 = os.path.join(root, file)
                L.append(file1.replace('\\', '/'))
            elif os.path.splitext(file)[1] == '.xlsx':
                file1 = os.path.join(root, file)
                L.append(file1.replace('\\', '/'))
            elif os.path.splitext(file)[1] == '.xls':
                file1 = os.path.join(root, file)
                L.append(file1.replace('\\', '/'))
    return L


def serial_number(f):
    SN = []
    for element in f:
        filename = element.split('/')[-1].split('.')[0]
        sn = filename.split('_')[0]
        SN.append(sn)
    return SN


def condition(f):
    COND = []
    for element in f:
        filename = element.split('/')[-1].split('.')[0]
        cond = filename.split('_')[2]
        COND.append(cond)
    return COND

def test_time(f):
    time1 = []
    time2 = []
    for element in f:
        filename = element.split('/')[-1].split('.')[0]
        t1 = filename.split('_')[3]
        t2 = filename.split('_')[4]
        time1.append(t1)
        time2.append(t2)
    return time1, time2


def MT(f, s1, s2):
    pat1 = re.compile(s1 + '(.*?)' + s2, re.S)
    mt = []
    for element in f:
        data = open(element)
        lines = data.read()
        new_data = pat1.findall(lines)
        new_data = '\r\n'.join(new_data)
        MT = new_data.split(' ')[1]
        mt.append(MT)
    return mt


def restart_class(f, s1, s2):
    pat1 = re.compile(s1 + '(.*?)' + s2, re.S)
    res_class = []
    for element in f:
        data = open(element)
        lines = data.read()
        new_data = pat1.findall(lines)
        new_data = '\r\n'.join(new_data)
        rc = new_data.split(' ')[2]
        res_class.append(rc)
    return res_class


def sw_port(f):
    otdr = []
    port = []
    stat = []
    for element in f:
        filename = element.split('/')[-1].split('.')[0]
        cond = filename.split('_')[2]
        if cond == '1' or cond == '2':
            s1 = 'osw 1 pos'
            s2 = '>'
            pat1 = re.compile(s1 + '(.*?)' + s2, re.S)
            data = open(element)
            lines = data.read()
            new_data = pat1.findall(lines)
            new_data = '\r\n'.join(new_data)
            ot = new_data.split(' ')[1]
            nd = new_data.split(' ')[3]
            st = new_data.split(' ')[4]
            st_new = st.strip()
            otdr.append(ot)
            port.append(nd)
            stat.append(st_new)
        elif cond == '3' or cond == '4':
            s1 = 'osw 2 pos'
            s2 = '>'
            pat1 = re.compile(s1 + '(.*?)' + s2, re.S)
            data = open(element)
            lines = data.read()
            new_data = pat1.findall(lines)
            new_data = '\r\n'.join(new_data)
            ot = new_data.split(' ')[1]
            nd = new_data.split(' ')[3]
            st = new_data.split(' ')[4]
            st_new = st.strip()
            otdr.append(ot)
            port.append(nd)
            stat.append(st_new)
    return otdr, port, stat


def dynamic_range(f, s1, s2):
    pat1 = re.compile(s1 + '(.*?)' + s2, re.S)
    final_noise_1 = []
    final_noise_2 = []
    final_mode_1 = []
    final_mode_2 = []
    for element in f:
        data = open(element)
        lines = data.read()
        new_data = pat1.findall(lines)
        for line in new_data:
            pat2 = re.compile('mode = ' + '(.*?)' + '\r\n', re.S)
            pat3 = re.compile('noiseLevelZM = ' + '(.*?)' + '\r\n', re.S)
            mode = pat2.findall(line)
            noise = pat3.findall(line)
            i = len(noise)
            if i == 1:
                final_noise_1.append(noise[0])
                final_noise_2.append(0)
                final_mode_1.append(mode[0])
                final_mode_2.append(0)
            if i == 2:
                final_noise_1.append(noise[0])
                final_noise_2.append(noise[1])
                final_mode_1.append(mode[0])
                final_mode_2.append(mode[1])
    return final_mode_1, final_noise_1, final_mode_2, final_noise_2


def loss(f, s1, s2):
    pat1 = re.compile(s1 + '(.*?)' + s2, re.S)
    final_pos = []
    final_loss = []
    for element in f:
        filename = element.split('/')[-1].split('.')[0]
        cond = filename.split('_')[2]
        data = open(element)
        lines = data.read()
        new_data = pat1.findall(lines)
        for line in new_data:
            line = line.split('\r\n')
            n = len(line)
            min_point = []
            for i in range(2, n-1, 1):
                loss = float(line[i].split(',')[4])
                pos = float(line[i].split(',')[1])
                if pos - 0.4 < 0:
                    if float(cond) == 1 or float(cond) == 4 or float(cond) == 5 or float(cond) == 6 or float(cond) == 7 or float(cond) == 8:
                        loss_delta = abs(loss - 1.0)
                        min_point.append(loss_delta)
                    if float(cond) == 2:
                        loss_delta = abs(loss - 2.0)
                        min_point.append(loss_delta)
                    if float(cond) == 3:
                        loss_delta = abs(loss - 3.0)
                        min_point.append(loss_delta)
            if min_point != []:
                min_loss = min(min_point)
                index = min_point.index(min_loss) + 2
                pos = line[index].split(',')[1]
                loss = line[index].split(',')[4]
                final_pos.append(pos)
                final_loss.append(loss)
    return final_pos, final_loss                                       


def reflection(f, s1, s2):
    pat1 = re.compile(s1 + '(.*?)' + s2, re.S)
    final_pos = []
    final_ref = []
    for element in f:
        filename = element.split('/')[-1].split('.')[0]
        cond = filename.split('_')[2]
        data = open(element)
        lines = data.read()
        new_data = pat1.findall(lines)
        for line in new_data:
            line = line.split('\r\n')
            n = len(line)
            min_point = []
            for i in range(2, n-1, 1):
                new_line = line[i].replace('NaN', '-100')
                ref = float(new_line.split(',')[5])  
                pos = float(new_line.split(',')[1])
                if pos - 1.0 < 0:
                    if float(cond) == 1:
                        ref_delta = abs(ref + 45)
                        min_point.append(ref_delta)
                    if float(cond) == 2:
                        ref_delta = abs(ref + 45)
                        min_point.append(ref_delta)
                    if float(cond) == 3:
                        ref_delta = abs(ref + 45)
                        min_point.append(ref_delta)
                    if float(cond) == 4:
                        ref_delta = abs(ref + 40)
                        min_point.append(ref_delta)
                    if float(cond) == 5:
                        ref_delta = abs(ref + 30)
                        min_point.append(ref_delta)
                    if float(cond) == 6:
                        ref_delta = abs(ref + 20)
                        min_point.append(ref_delta)
                    if float(cond) == 7:
                        ref_delta = abs(ref + 15)
                        min_point.append(ref_delta)
                    if float(cond) == 8:
                        ref_delta = abs(ref + 45)
                        min_point.append(ref_delta)
            if min_point != []:
                min_ref = min(min_point)
                index = min_point.index(min_ref) + 2
                pos = line[index].split(',')[1]
                ref = line[index].split(',')[5]
                final_pos.append(pos)
                final_ref.append(ref)
    return final_pos, final_ref


def figure(f, s1, s2):
    pat1 = re.compile(s1 + '(.*?)' + s2, re.S)  ### used for otdr 1
    for element in f:
        filename = element.split('/')[-1].split('.')[0]
        data = open(element)
        lines = data.read()
        new_data = pat1.findall(lines)
        x = []
        y = []
        for line in new_data:
            line = line.split()
            n = len(line)
            start = int(n*0.1)
            end = int(n*1.0)
            for i in range(start, end, 1):
                newline = line[i].split(',')
                x.append(float(newline[0]))
                y.append(float(newline[1]))
        spl = InterpolatedUnivariateSpline(x, y)
        #print spl.get_residual()
        x_new  = np.linspace(x[0], x[-1], 1000)
        y_new = spl(x_new)
        plt.plot(x, y, '*', x_new, y_new, '-')
        plt.legend(('raw_data', 'interpolatdUnivariateSpline'), loc='upper right')
        plt.xlabel('span length(km)')
        plt.ylabel('loss(dB)')
        plt.title('trace_%s' % filename)
        fname = 'traces/%s.png' % (filename)
        plt.savefig(fname, format='png')
        plt.clf()


def refl_dead_zone(f, s1, s2):
    DZ = []
    pat1 = re.compile(s1 + '(.*?)' + s2, re.S)  ### used for otdr 1
    for element in f:
        filename = element.split('/')[-1].split('.')[0]
        cond = filename.split('_')[2]
        if float(cond) != 8:
            data = open(element)
            lines = data.read()
            new_data = pat1.findall(lines)
            x = []
            y = []
            for line in new_data:
                line = line.split()
                n = len(line)
                for i in range(1, n, 1):
                    newline = line[i].split(',')
                    x.append(float(newline[0]))
                    y.append(float(newline[1]))
            refl_peak = max(y)
            refl_under_peak_1 = refl_peak - 1.5
            index = y.index(refl_peak)
            index_low = index - 50
            index_high = index + 20
            x_new = []
            y_new = []
            for i in range(index_low, index_high, 1):
                x_new.append(float(x[i]))
                y_new.append(float(y[i]) - refl_under_peak_1)
            spl = InterpolatedUnivariateSpline(x_new, y_new)
            root = InterpolatedUnivariateSpline.roots(spl)
            pos_gap = (abs(root[0] - root[1]))*1000
            DZ.append(pos_gap)
        else:
            DZ.append(0)
    return DZ


def attenuation_dead_zone(f, s1, s2):
    DZ = []
    pat1 = re.compile(s1 + '(.*?)' + s2, re.S)  ### used for otdr 1
    for element in f:
        filename = element.split('/')[-1].split('.')[0]
        cond = filename.split('_')[2]
        if float(cond) != 8:
            data = open(element)
            lines = data.read()
            new_data = pat1.findall(lines)
            x = []
            y = []
            for line in new_data:
                line = line.split()
                n = len(line)
                for i in range(1, int(n*0.5), 1):
                    newline = line[i].split(',')
                    x.append(float(newline[0]))
                    y.append(float(newline[1]))
            spl = InterpolatedUnivariateSpline(x, y)
            x_new_1 = np.linspace(0.15, 0.25, 100)
            y_new_1 = spl(x_new_1)
            left = np.average(abs(y_new_1))
            n = len(y)
            y_new = []
            for i in range(n):
                y_new.append(float(y[i])-left)
            spl1 = InterpolatedUnivariateSpline(x, y_new)
            root = InterpolatedUnivariateSpline.roots(spl1)
            error = (abs(root[-1] - root[-2]))*500
            DZ.append(error)
        else:
            DZ.append(0)
    return DZ


def to_excel(f, s1, s2):
    pat1 = re.compile(s1 + '(.*?)' + s2, re.S)  ### used for otdr 1
    for element in f:
        filename = element.split('/')[-1].split('.')[0]
        data = open(element)
        lines = data.read()
        new_data = pat1.findall(lines)
        x = []
        y = []
        for line in new_data:
            line = line.split()
            n = len(line)
            start = 1
            end = int(n * 1.0)
            x_title = line[0].split(',')[0]
            y_title = line[0].split(',')[1]
            for i in range(start, end, 1):
                newline = line[i].split(',')
                x.append(float(newline[0]))
                y.append(float(newline[1]))
        result = pd.DataFrame({'%s' % (x_title):x, '%s' % (y_title):y})
        result.to_excel('D:/OTDR/04.MR_OTDR/trace_data/%s.xlsx' % (filename))


if __name__=='__main__':
    dir = 'E:/19.Cisco Mystique OTDR/81 RMA/results'
    f = file_name(dir)
    sn = serial_number(f)
    cond = condition(f)
    t= test_time(f)
    mt = MT(f, s1='MT', s2='>')
    p = sw_port(f)
    r = restart_class(f, s1='restart', s2='>')
    result = pd.concat([pd.DataFrame({"SN": sn}),
                       pd.DataFrame({"COND": cond}),
                       pd.DataFrame({"day": t[0]}),
                       pd.DataFrame({"time": t[1]}),
                       pd.DataFrame({"MT": mt}),
                       pd.DataFrame({"OTDR":p[0]}),
                       pd.DataFrame({"port":p[1]}),
                       pd.DataFrame({"stat":p[2]}),
                       pd.DataFrame({"Restart_class": r})], axis=1)
    result.to_excel('Cisco Galactus RMA - Stress Test - 20180801.xlsx')
    
    #to_excel(f, s1='otdr 1 x dump y', s2='>')

    """
    adz = attenuation_dead_zone(f, s1='otdr 1 dump trace', s2='>')
    ref = reflection(f, s1='otdr 1 dump event raw', s2='>')
    los = loss(f, s1='otdr 1 dump event raw', s2='>')
    sn = serial_number(f)
    cond = condition(f)
    mt = MT(f, s1='MT', s2='>')
    DR = dynamic_range(f, s1='otdr 1 x dump_mlist', s2='>')
    result = pd.concat([pd.DataFrame({"SN": sn}),
                       pd.DataFrame({"COND": cond}),
                       pd.DataFrame({"MT": mt}),
                       pd.DataFrame({"POSITION": los[0]}),
                       pd.DataFrame({"LOSS": los[1]}),
                       pd.DataFrame({"POSITION": ref[0]}),
                       pd.DataFrame({"Reflection": ref[1]}),
                       pd.DataFrame({"MODE1": DR[0]}),
                       pd.DataFrame({"Noise1": DR[1]}),
                       pd.DataFrame({"MODE2": DR[2]}),
                       pd.DataFrame({"Noise2": DR[3]}),
                       pd.DataFrame({"EDZ": rdz}),
                       pd.DataFrame({"ADZ": adz})], axis=1)
    result.to_excel('MR-OTDR DVT - optical performance for sample 2 at room temperature - 20180710.xlsx')
    """