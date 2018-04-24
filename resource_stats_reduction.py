#! /usr/bin/env python

"""
This script is for obtaining high-level android phone hardware resource usage statistics based on
raw data collected from /proc/stat and /proc/meminfo

Use output from the following command:
    ../tools/resource_stats_reduction resource_stats_~~~~ | tee reduced_stats_~~~~
to obtain high-level resource usage statistics.

Example:
$ ./resource_stats_reduction.py resource_stats_01.txt | tee reduced_stats_output


Command to collect raw data from system file:

adb shell "while :; do echo -------- \`date -u\` --------; \
echo ---- /proc/schedstat; cat /proc/schedstat; \
echo ---- /proc/meminfo; cat /proc/meminfo; \
echo ---- /proc/stat; \
cat /proc/stat; echo ---- top; \
top -n 1; sleep 3; done" > resource_stats_~~~~

"""
from __future__ import print_function
from __future__ import division


import re
import argparse
from datetime import datetime


class ResourceUsageStats(object):


    def __init__(self, cpu_stats_list, mem_stats_list):
        self.cpu_stats_list = cpu_stats_list
        self.mem_stats_list = mem_stats_list

    def getSummary(self):

        res = 'Overall CPU - user + sys + irq min: {0:.1f}%\n'.format(min(CpuOverallUserSysStats(CpuStats(self.cpu_stats_list))))
        
        res += 'Overall CPU - user + sys + irq avg: {0:.1f}%\n'.format(sum(CpuOverallUserSysStats(CpuStats(self.cpu_stats_list))) / \
                                                                       (CpuStats(self.cpu_stats_list).getStatsCount()))
        res += 'Overall CPU - user + sys + irq max: {0:.1f}%\n'.format(max(CpuOverallUserSysStats(CpuStats(self.cpu_stats_list))))
        res += 'Overall CPU - user + sys + irq Max - Min: {0:.1f}%\n'.format(max(CpuOverallUserSysStats(CpuStats(self.cpu_stats_list))) -  \
                                                                             min(CpuOverallUserSysStats(CpuStats(self.cpu_stats_list))))
        res += 'Overall CPU - user + sys + irq Last - First: {0:.1f}%\n'.format((CpuOverallUserSysStats(CpuStats(self.cpu_stats_list)))[-1] - \
                                                                                (CpuOverallUserSysStats(CpuStats(self.cpu_stats_list)))[0])

        res += 'Overall CPU - user min: {0:.1f}%\n'.format(min(CpuOverallUserStats(CpuStats(self.cpu_stats_list))))
        res += 'Overall CPU - user avg: {0:.1f}%\n'.format(sum(CpuOverallUserStats(CpuStats(self.cpu_stats_list))) / \
                                                          (CpuStats(self.cpu_stats_list).getStatsCount()))
        res += 'Overall CPU - user max: {0:.1f}%\n'.format(max(CpuOverallUserStats(CpuStats(self.cpu_stats_list))))

        res += 'Overall CPU - sys min: {0:.1f}%\n'.format(min(CpuOverallSysStats(CpuStats(self.cpu_stats_list))))
        res += 'Overall CPU - sys avg: {0:.1f}%\n'.format(sum(CpuOverallSysStats(CpuStats(self.cpu_stats_list))) / \
                                                          (CpuStats(self.cpu_stats_list).getStatsCount()))
        res += 'Overall CPU - sys max: {0:.1f}%\n'.format(max(CpuOverallSysStats(CpuStats(self.cpu_stats_list))))

        res += 'Per CPU - user + sys min: {0:.1f}%\n'.format(min([min(x) for x in CpuPerCoreUserSysStats(CpuStats(self.cpu_stats_list))]))
        res += 'Per CPU - user + sys max: {0:.1f}%\n'.format(max([max(x) for x in CpuPerCoreUserSysStats(CpuStats(self.cpu_stats_list))]))

        res += 'Per CPU - user min: {0:.1f}%\n'.format(min([min(x) for x in CpuPerCoreUserStats(CpuStats(self.cpu_stats_list))]))
        res += 'Per CPU - user max: {0:.1f}%\n'.format(max([max(x) for x in CpuPerCoreUserStats(CpuStats(self.cpu_stats_list))]))

        res += 'Per CPU - sys min: {0:.1f}%\n'.format(min([min(x) for x in CpuPerCoreSysStats(CpuStats(self.cpu_stats_list))]))
        res += 'Per CPU - sys max: {0:.1f}%\n'.format(max([max(x) for x in CpuPerCoreSysStats(CpuStats(self.cpu_stats_list))]))

        res += 'Memory in use (MiB) min: {0:.1f}\n'.format(min(MemUsedStats(MemStats(self.mem_stats_list))) / 1024)
        res += 'Memory in use (MiB) avg: {0:.1f}\n'.format((sum(MemUsedStats(MemStats(self.mem_stats_list))) / 1024) /
                                                     len(self.mem_stats_list))
        res += 'Memory in use (MiB) max: {0:.1f}\n'.format(max(MemUsedStats(MemStats(self.mem_stats_list))) / 1024)

        res += 'Memory in use (MiB) Max - Min : {0:.1f}\n'.format((max(MemUsedStats(MemStats(self.mem_stats_list))) - \
                                                         min(MemUsedStats(MemStats(self.mem_stats_list))))  / 1024)
        res += 'Memory in use (MiB) Last - First: {0:.1f}'.format(((MemUsedStats(MemStats(self.mem_stats_list)))[-1] - \
                                                                   (MemUsedStats(MemStats(self.mem_stats_list)))[0]) / 1024)
        return res


class Stats(object):


    def __getitem__(self, index):
        raise NotImplementedError("Subclasses should implement this!")

    def __iter__(self):
        return self

    def next(self):
        raise NotImplementedError("Subclasses should implement this!")


class CpuStats(Stats):


    def __init__(self, stats_list):
        self.stats_list = stats_list
        self.pre_stat = self.stats_list[0]
        self.current_stat = self.stats_list[1]
        self.index = 0

    def __getitem__(self, index):
        pre_index = index
        cur_index = index + 1
        if index <  0:
            pre_index = index - 1
            cur_index = index
        previous = self.stats_list[pre_index]
        current = self.stats_list[cur_index]
        return (previous, current)

    def next(self):
        if self.index >= len(self.stats_list) - 1:
            raise StopIteration()
        res = self.__getitem__(self.index)
        self.__shiftOneStat()
        return res

    def __shiftOneStat(self):
        self.pre_stat = self.current_stat
        self.index += 1
        if self.index >= len(self.stats_list): 
            self.current_stat = None
        else:
            self.current_stat = self.stats_list[self.index]

    def getTotalDelta(self, previous, current, cpu_id):
        time_delta = (current.date - previous.date).total_seconds() * 100
        if cpu_id == 'cpu':
            time_delta *= self.getCpuCoreCount()
        return time_delta
    
    def getUserPercentage(self, previous, current, cpu_id):
        total_delta = self.getTotalDelta(previous, current, cpu_id)
        if cpu_id not in current.data or cpu_id not in previous.data: return 0.0
        current_user_time = (current.data[cpu_id])['user'] + (current.data[cpu_id])['nice']
        previous_user_time = (previous.data[cpu_id])['user'] + (previous.data[cpu_id])['nice']
        user_delta = current_user_time - previous_user_time
        percentage = float(user_delta) / total_delta * 100
        return percentage

    def getSysPercentage(self, previous, current, cpu_id):
        total_delta = self.getTotalDelta(previous, current, cpu_id)
        if cpu_id not in current.data or cpu_id not in previous.data: return 0.0
        current_sys_time = (current.data[cpu_id])['system'] + (current.data[cpu_id])['irq'] + (current.data[cpu_id])['softirq']
        previous_sys_time = (previous.data[cpu_id])['system'] + (previous.data[cpu_id])['irq'] + (previous.data[cpu_id])['softirq']
        sys_delta = current_sys_time - previous_sys_time
        percentage = float(sys_delta) / total_delta * 100
        return percentage

    def getCpuCoreCount(self):
        if len(self.stats_list) == 0: return 0
        return len(self.stats_list[0].data) - 1
    
    def getStatsCount(self):
        return len(self.stats_list) - 1

            
class CpuOverallUserSysStats(Stats):


    def __init__(self, cpu_stats):
        self.cpu_stats = cpu_stats
        
    def __getitem__(self, index):
        previous, current = self.cpu_stats[index]
        return self.__getPercentage(previous, current)
    
    def __getPercentage(self, previous, current):
        res = self.cpu_stats.getUserPercentage(previous, current, 'cpu') + \
              self.cpu_stats.getSysPercentage(previous, current, 'cpu')
        return res
    
    def next(self):
        previous, current = self.cpu_stats.next()
        return self.__getPercentage(previous, current)


class CpuOverallUserStats(Stats):


    def __init__(self, cpu_stats):
        self.cpu_stats = cpu_stats
        
    def __getitem__(self, index):
        previous, current = self.cpu_stats[index]
        return self.__getPercentage(previous, current)
    
    def __getPercentage(self, previous, current):
        return self.cpu_stats.getUserPercentage(previous, current, 'cpu')
    
    def next(self):
        previous, current = self.cpu_stats.next()
        return self.__getPercentage(previous, current)


class CpuOverallSysStats(Stats):


    def __init__(self, cpu_stats):
        self.cpu_stats = cpu_stats

    def __getitem__(self, index):
        previous, current = self.cpu_stats[index]
        return self.__getPercentage(previous, current)

    def __getPercentage(self, previous, current):
        res = self.cpu_stats.getSysPercentage(previous, current, 'cpu')
        return res

    def next(self):
        previous, current = self.cpu_stats.next()
        return self.__getPercentage(previous, current)


class CpuPerCoreUserSysStats(Stats):


    def __init__(self, cpu_stats):
        self.cpu_stats = cpu_stats

    def __getitem__(self, index):
        previous, current = self.cpu_stats[index]
        return self.getPercentage(previous, current)

    def getPercentage(self, previous, current):
        res = []
        for cpu_id in xrange(self.cpu_stats.getCpuCoreCount()):
                res.append(self.cpu_stats.getUserPercentage(previous, current, 'cpu'+ str(cpu_id)) + \
                           self.cpu_stats.getSysPercentage(previous, current, 'cpu'+ str(cpu_id)))
        return res

    def next(self):
        previous, current = self.cpu_stats.next()
        return self.getPercentage(previous, current)


class CpuPerCoreUserStats(Stats):


    def __init__(self, cpu_stats):
        self.cpu_stats = cpu_stats

    def __getitem__(self, index):
        previous, current = self.cpu_stats[index]
        return self.getPercentage(previous, current)

    def getPercentage(self, previous, current):
        res = []
        for cpu_id in xrange(self.cpu_stats.getCpuCoreCount()):
                res.append(self.cpu_stats.getUserPercentage(previous, current, 'cpu'+ str(cpu_id)))
        return res

    def next(self):
        previous, current = self.cpu_stats.next()
        return self.getPercentage(previous, current)


class CpuPerCoreSysStats(Stats):


    def __init__(self, cpu_stats):
        self.cpu_stats = cpu_stats

    def __getitem__(self, index):
        previous, current = self.cpu_stats[index]
        return self.getPercentage(previous, current)

    def getPercentage(self, previous, current):
        res = []
        for cpu_id in xrange(self.cpu_stats.getCpuCoreCount()):
                res.append(self.cpu_stats.getSysPercentage(previous, current, 'cpu'+ str(cpu_id)))
        return res

    def next(self):
        previous, current = self.cpu_stats.next()
        return self.getPercentage(previous, current)


class MemStats(Stats):


    def __init__(self, mem_stats_list):
        self.stats_list = mem_stats_list
        self.current_stat = self.stats_list[0]
        self.index = 0

    def __iter__(self):
        return self
    
    def __getitem__(self, index):
        return self.stats_list[index]

    def next(self):
        if self.index >= len(self.stats_list):
            raise StopIteration()
        res = self.__getitem__(self.index)
        self.__shiftOneStat()
        return res 

    def __shiftOneStat(self):
        self.index += 1
        if self.index >= len(self.stats_list): 
            self.current_stat = None
        else:
            self.current_stat = self.stats_list[self.index]


class MemUsedStats(Stats):


    def __init__(self, mem_stats):
        self.mem_stats = mem_stats
    
    def __getitem__(self, index):
        stat = self.mem_stats[index]
        return self.getUsed(stat)
    
    def next(self):
        stat = self.mem_stats.next()
        return self.getUsed(stat)
    
    def getUsed(self, stat):
        used = stat.data['MemTotal'] - \
               stat.data['MemFree'] - \
               stat.data['Cached']
        return used


class Data(object):


    def parseText(self, text):
        raise NotImplementedError("Subclasses should implement this!")


class ProcStatData(Data):


    def __init__(self, date):
        """Data format:
           <cpu_id>    <user>  <nice> <system> <idle>    <iowait> <irq>  <softirq> <steal> <guest> <guest_nice>
           
           Example:
           cpu       74608 2520 24433  1117073 6176   4054 0       0     0     0 
        """
        self.data = {}
        self.date = date
        self.end_regexp = re.compile('---- ')
        self.data_regexp = re.compile(''.join(('(?P<cpu_id>^cpu[0-9]*) +', 
                                               '(?P<user>[0-9]+) ', 
                                               '(?P<nice>[0-9]+) ', 
                                               '(?P<system>[0-9]+) '
                                               '(?P<idel>[0-9]+) '
                                               '(?P<iowait>[0-9]+) '
                                               '(?P<irq>[0-9]+) '
                                               '(?P<softirq>[0-9]+) '
                                               '(?P<steal>[0-9]+) '
                                               '(?P<guest>[0-9]+) '
                                               '(?P<guest_nice>[0-9]+)')))

    def parseText(self, log_file):
        line = log_file.readline()
        while line and not self.end_regexp.search(line):
            self.__fillData(line)
            line = log_file.readline()
        return line

    def getCoreCount(self):
        return len(self.data) - 1

    def __fillData(self, text):

        m = self.data_regexp.match(text)
        if not m: return
        cpu_id = m.group('cpu_id')
        user = m.group('user')
        nice = m.group('nice')
        system = m.group('system')
        idle = m.group('idel')
        iowait = m.group('iowait')
        irq = m.group('irq')
        softirq = m.group('softirq')
        self.data[cpu_id] = {'user': int(user),
                             'nice': int(nice),
                             'system': int(system),
                             'idle': int(idle),
                             'iowait': int(iowait),
                             'irq': int(irq),
                             'softirq': int(softirq)}

    def __str__(self):
        res = ''
        res += str(self.date) + ': '
        res += 'Cpu Data: {0}\n'.format(self.data)
        return res

    def __repr__(self):
        return self.__str__()


class ProcMeminfoData(Data):


    def __init__(self, date):
        """Meminfo data format:
           <key>:           <value> kB
           .....
           .....
           ---- ****
           Example:
           
           MemTotal:        3809032 kB
           MemFree:          495404 kB
           MemAvailable:    2133700 kB
           Buffers:            8140 kB
           Cached:          1256828 kB
           SwapCached:        86428 kB
           ....
           .....
           ---- /proc/stat
        """
        self.data = {}
        self.date = date
        self.end_regexp = re.compile('---- ')
        self.data_regexp = re.compile('(?P<key>^[a-zA-Z]+):\s+(?P<value>[0-9]+)\s+kB')

    def parseText(self, log_file):
        end_regexp = re.compile('---- ')
        line = log_file.readline()
        while line and not end_regexp.search(line):
            m = self.data_regexp.match(line)
            if m:
                value_name = m.group('key')
                self.data[value_name] = int(m.group('value'))
            line = log_file.readline()
        return line

    def __str__(self):
        res = ''
        res += str(self.date) + ': '
        res += 'Mem Data: {0}\n'.format(self.data)
        return res

    def __repr__(self):
        return self.__str__()


class LogParser(object):


    def __init__(self, file_path):
        self.file_path = file_path
        
    def parseLogFile(self):
        date_regexp = re.compile('^-------- [a-zA-Z]{3,} [a-zA-Z]{3,} [0-9]{1,2} [0-9]{2,}:[0-9]{2,}:[0-9]{2,} GMT [0-9]{4,} --------')
        proc_stat_start_regexp = re.compile('^---- /proc/stat')
        proc_meminfo_start_regexp = re.compile('^---- /proc/meminfo')
        current_date = None
        cpu_stats = []
        mem_stats = []
        f = open(self.file_path, 'r')
        line = f.readline()
        while line:
            if date_regexp.search(line):
                current_date = self.__parseDateText(line)
                line = f.readline()
            elif proc_stat_start_regexp.search(line):
                proc_stat_data = ProcStatData(current_date)
                line = proc_stat_data.parseText(f)
                cpu_stats.append(proc_stat_data)
            elif proc_meminfo_start_regexp.search(line):
                proc_meminfo_data = ProcMeminfoData(current_date)
                line = proc_meminfo_data.parseText(f)
                mem_stats.append(proc_meminfo_data)
            else:
                line = f.readline()
        return cpu_stats, mem_stats
    
    def __parseDateText(self, text):
        date_text = re.match('(.*)-------- (.*) --------', text).group(2)
        date = datetime.strptime(date_text, '%a %b %d %H:%M:%S %Z %Y')
        return date


if __name__ == '__main__':
    script_description = """
                           This script is for obtaining high-level android phone hardware 
                           resource usage statistics based on raw data collected from 
                           /proc/stat and /proc/meminfo
                         """
    args_parser = argparse.ArgumentParser(description=script_description)
    args_parser.add_argument('input_file', type=str, help='input log file')
    args = args_parser.parse_args()
    log_parser = LogParser(args.input_file)
    cpu_stats_list, mem_stats_list = log_parser.parseLogFile()
    resource_usage_stats = ResourceUsageStats(cpu_stats_list, mem_stats_list)
    res = resource_usage_stats.getSummary()
    print (res)