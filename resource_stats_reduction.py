#! /usr/bin/env python

""" 
This script is for obtaining high-level android phone hardware resource usage statistics based on
raw data collected from /proc/stat /proc/{pid}/stat and /proc/meminfo

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
        res = '-------- Cpu statistics --------\n'

        res += 'Overall CPU - user + sys min: {0:.1f}%\n'.format(min(CpuStats(self.cpu_stats_list, 'overall user + system')))
        res += 'Overall CPU - user + sys avg: {0:.1f}%\n'.format(sum(CpuStats(self.cpu_stats_list, 'overall user + system')) / \
                                                          (len(self.cpu_stats_list) - 1))
        res += 'Overall CPU - user + sys max: {0:.1f}%\n'.format(max(CpuStats(self.cpu_stats_list, 'overall user + system')))
        res += 'Peak Valley Delta: {0:.1f}%\n'.format(max(CpuStats(self.cpu_stats_list, 'overall user + system')) -  \
                                                      min(CpuStats(self.cpu_stats_list, 'overall user + system')))

        res += 'Overall CPU - user min: {0:.1f}%\n'.format(min(CpuStats(self.cpu_stats_list, 'overall user')))
        res += 'Overall CPU - user avg: {0:.1f}%\n'.format(sum(CpuStats(self.cpu_stats_list, 'overall user')) / \
                                                          (len(self.cpu_stats_list) - 1))
        res += 'Overall CPU - user max: {0:.1f}%\n'.format(max(CpuStats(self.cpu_stats_list, 'overall user')))

        res += 'Overall CPU - sys min: {0:.1f}%\n'.format(min(CpuStats(self.cpu_stats_list, 'overall system')))
        res += 'Overall CPU - sys avg: {0:.1f}%\n'.format(sum(CpuStats(self.cpu_stats_list, 'overall system')) / \
                                                          (len(self.cpu_stats_list) - 1))
        res += 'Overall CPU - sys max: {0:.1f}%\n'.format(max(CpuStats(self.cpu_stats_list, 'overall system')))

        res += 'Per CPU - user + sys min: {0:.1f}%\n'.format(min(CpuStats(self.cpu_stats_list, 'per CPU user + system')))
        res += 'Per CPU - user + sys avg: {0:.1f}%\n'.format(sum(CpuStats(self.cpu_stats_list, 'per CPU user + system')) / \
                                                             ((len(self.cpu_stats_list) - 1) * self.cpu_stats_list[0].getCoreCount()))
        res += 'Per CPU - user + sys max: {0:.1f}%\n'.format(max(CpuStats(self.cpu_stats_list, 'per CPU user + system')))

        res += 'Per CPU - user min: {0:.1f}%\n'.format(min(CpuStats(self.cpu_stats_list, 'per CPU user')))
        res += 'Per CPU - user avg: {0:.1f}%\n'.format(sum(CpuStats(self.cpu_stats_list, 'per CPU user')) / \
                                                       ((len(self.cpu_stats_list) - 1) * self.cpu_stats_list[0].getCoreCount()))
        res += 'Per CPU - user max: {0:.1f}%\n'.format(max(CpuStats(self.cpu_stats_list, 'per CPU user')))

        res += 'Per CPU - sys min: {0:.1f}%\n'.format(min(CpuStats(self.cpu_stats_list, 'per CPU system')))
        res += 'Per CPU - sys avg: {0:.1f}%\n'.format(sum(CpuStats(self.cpu_stats_list, 'per CPU system')) / \
                                                      ((len(self.cpu_stats_list) - 1) * self.cpu_stats_list[0].getCoreCount()))
        res += 'Per CPU - sys max: {0:.1f}%\n'.format(max(CpuStats(self.cpu_stats_list, 'per CPU system')))

        res += 'IO min: {0:.1f}%\n'.format(min(CpuStats(self.cpu_stats_list, 'io')))
        res += 'IO avg: {0:.1f}%\n'.format(sum(CpuStats(self.cpu_stats_list, 'io')) / \
                                          (len(self.cpu_stats_list) - 1))
        res += 'IO max: {0:.1f}%\n'.format(max(CpuStats(self.cpu_stats_list, 'io')))
        
        res += '-------- Memory statistics --------\n'

        res += 'Memory in use (MiB) min: {0:.1f}\n'.format(min(MemStats(self.mem_stats_list, 'MemUsed')) / 1024)
        res += 'Memory in use (MiB) avg: {0:.1f}\n'.format((sum(MemStats(self.mem_stats_list, 'MemUsed')) / 1024) /
                                                     len(self.mem_stats_list))
        res += 'Memory in use (MiB) max: {0:.1f}\n'.format(max(MemStats(self.mem_stats_list, 'MemUsed')) / 1024)

        res += 'Peak Valley Delta (MiB): {0:.1f}\n'.format((max(MemStats(self.mem_stats_list, 'MemUsed')) - \
                                                         min(MemStats(self.mem_stats_list, 'MemUsed')))  / 1024)
        res += 'After Before Delta (MiB): {0:.1f}'.format((self.mem_stats_list[0].getMemUsed() - \
                                                          self.mem_stats_list[-1].getMemUsed()) / 1024)
        return res


class CpuStats(object):

    def __init__(self, cpu_stats_list, query):
        self.stats_list = cpu_stats_list
        self.query = query
        self.pre_stat = None
        self.current_stat = self.stats_list[0]
        self.current_stat_current_id = 0
        self.index = 0
        self.__shiftOneStat()

    def __iter__(self):
        return self

    def next(self):
        if self.index >= len(self.stats_list):
            raise StopIteration()
        if self.query == 'overall user + system':
            res = self.__getUserPercentage(self.pre_stat, self.current_stat, 'cpu') + \
                  self.__getSysPercentage(self.pre_stat, self.current_stat, 'cpu')
            self.__shiftOneStat()
        elif self.query == 'overall user':
            res = self.__getUserPercentage(self.pre_stat, self.current_stat, 'cpu')
            self.__shiftOneStat()
        elif self.query == 'overall system':
            res = self.__getSysPercentage(self.pre_stat, self.current_stat, 'cpu')
            self.__shiftOneStat()
        elif self.query == 'per CPU user + system':
            res = self.__getUserPercentage(self.pre_stat, self.current_stat, 'cpu'+ str(self.current_stat_current_id)) + \
            self.__getSysPercentage(self.pre_stat, self.current_stat, 'cpu'+ str(self.current_stat_current_id))
            self.__shiftOneCore()
        elif self.query == 'per CPU user':
            res = self.__getUserPercentage(self.pre_stat, self.current_stat, 'cpu'+ str(self.current_stat_current_id))
            self.__shiftOneCore()
        elif self.query == 'per CPU system':
            res = self.__getSysPercentage(self.pre_stat, self.current_stat, 'cpu'+ str(self.current_stat_current_id))
            self.__shiftOneCore()
        elif self.query == 'io':
            res = self.__getIOPercentage(self.pre_stat, self.current_stat, 'cpu')
            self.__shiftOneStat()
        else:
            raise Exception('unsupported query')
        return res

    def __shiftOneStat(self):
        self.pre_stat = self.current_stat
        self.index += 1
        if self.index >= len(self.stats_list): 
            self.current_stat = None
        else:
            self.current_stat = self.stats_list[self.index]

    def __shiftOneCore(self):
        self.current_stat_current_id += 1
        if self.current_stat_current_id >= self.getCpuCoreCount():
            self.current_stat_current_id = 0
            self.__shiftOneStat()

    def __getUserPercentage(self, previous, current, cpu_id):
        total_delta = self._getTotalCpuTime(current.data, cpu_id) - \
                      self._getTotalCpuTime(previous.data, cpu_id)
        user_delta = (current.data[cpu_id])['user'] - (previous.data[cpu_id])['user']
        percentage = float(user_delta) / total_delta * 100
        return percentage

    def __getSysPercentage(self, previous, current, cpu_id):
        total_delta = self._getTotalCpuTime(current.data, cpu_id) - \
                      self._getTotalCpuTime(previous.data, cpu_id)
        sys_delta = (current.data[cpu_id])['system'] - (previous.data[cpu_id])['system']
        percentage = float(sys_delta) / total_delta * 100
        return percentage

    def __getIOPercentage(self, previous, current, cpu_id):
        total_delta = self._getTotalCpuTime(current.data, cpu_id) - \
                      self._getTotalCpuTime(previous.data, cpu_id)
        io_delta = (current.data[cpu_id])['iowait'] - (previous.data[cpu_id])['iowait']
        percentage = float(io_delta) / total_delta * 100
        return percentage

    def _getTotalCpuTime(self, data, cpu_id):
        total = 0
        for value_name in data[cpu_id]:
            total += (data[cpu_id])[value_name]
        return total

    def getCpuCoreCount(self):
        if len(self.stats_list) == 0: return 0
        return len(self.stats_list[0].data) - 1

class MemStats(object):

    def __init__(self, mem_stats_list, query):
        self.stats_list = mem_stats_list
        self.query = query
        self.current_stat = self.stats_list[0]
        self.index = 0

    def __iter__(self):
        return self

    def next(self):
        if self.index >= len(self.stats_list):
            raise StopIteration()
        if self.query == 'Total_Free_Cached_Used':
            res = [self.current_stat.data['MemTotal'],
                   self.current_stat.data['MemFree'],
                   self.current_stat.data['Cached'],
                   self.current_stat.getMemUsed()]
            self.__shiftOneStat()
            return res
        elif self.query == 'MemUsed':
            used = self.current_stat.getMemUsed()
            self.__shiftOneStat()
            return used
        else:
            raise Exception('unsupported query')

    def __shiftOneStat(self):
        self.index += 1
        if self.index >= len(self.stats_list): 
            self.current_stat = None
        else:
            self.current_stat = self.stats_list[self.index]

class Data(object):

    def parseText(self, text):
        raise NotImplementedError("Subclasses should implement this!")

class ProcStatData(Data):

    def __init__(self, date):
        self.data = {}
        self.date = date

    def parseText(self, log_file):
        end_regexp = re.compile('---- ')
        line = log_file.readline()
        while line and not end_regexp.search(line):
            if line.startswith('cpu'):
                items = line.split()
                cpu_id = items[0]
                if cpu_id not in self.data: self.data[cpu_id] = {}
                self.__fillData(self.data[cpu_id], items)
            line = log_file.readline()
        return line

    def getCoreCount(self):
        return len(self.data) - 1

    def __fillData(self, data, items):
        """ Example
                 user  nice system idle    iowait irq  softirq steal guest guest_nice  
             cpu 74608 2520 24433  1117073 6176   4054 0       0     0     0 
        """
        data['user'] = int(items[1])
        data['nice'] = int(items[2])
        data['system'] = int(items[3])
        data['idle'] = int(items[4])
        data['iowait'] = int(items[5])
        data['irq'] = int(items[6])
        data['softirq'] = int(items[7])

    def __str__(self):
        res = ''
        res += str(self.date) + ': '
        res += 'Cpu Data: {0}\n'.format(self.data)
        return res

    def __repr__(self):
        return self.__str__()

class ProcMeminfoData(Data):

    def __init__(self, date):
        self.data = {}
        self.date = date

    def parseText(self, log_file):
        end_regexp = re.compile('---- ')
        line = log_file.readline()
        while line and not end_regexp.search(line):
            items = line.split()
            value_name = (items[0])[:-1]
            self.data[value_name] = int(items[1])
            line = log_file.readline()
        return line

    def getMemUsed(self):
        used = self.data['MemTotal'] - \
               self.data['MemFree'] - \
               self.data['Cached']
        return used

    def __str__(self):
        res = ''
        res += str(self.date) + ': '
        res += 'Mem Data: {0}\n'.format(self.data)
        return res

    def __repr__(self):
        return self.__str__()

class TopData(Data):

    def __init__(self, date):
        self.data = {}
        self.date = date

    def parseText(self, log_file):
        end_regexp = re.compile('---- ')
        process_regexp = re.compile('\s+([0-9]+)\s+(.*)\s+(.*)\s+(-*[0-9]+)\s+(\d+%)\s+([A-Z])\s+(\d+)\s+(\d+K)\s+(\d+K)\s+([a-z]+)\s+(.*)' )
        line = log_file.readline()
        rss = 0
        while line and not end_regexp.search(line):
            if process_regexp.match(line):
                match_res = process_regexp.match(line)
                rss += int((match_res.group(9))[:-1])
            line = log_file.readline()
        self.data['rss'] = rss
        return line

    def __str__(self):
        res = ''
        res += str(self.date) + ': '
        res += 'Top Rss: {0}\n'.format(self.data)
        return res

    def __repr__(self):
        return self.__str__()

  
def parseDateText(text):
    text = re.match('(.*)-------- (.*) --------', text).group(2)
    date = datetime.strptime(text, '%a %b %d %H:%M:%S %Z %Y')
    return date

def parseLogFile(file_path):
    date_regexp = re.compile('^-------- [a-zA-Z]{3,} [a-zA-Z]{3,} [0-9]{1,2} [0-9]{2,}:[0-9]{2,}:[0-9]{2,} GMT [0-9]{4,} --------')
    proc_stat_start_regexp = re.compile('^---- /proc/stat')
    proc_meminfo_start_regexp = re.compile('^---- /proc/meminfo')
    proc_top_start_regexp = re.compile('^---- top')
    current_date = None
    cpu_stats = []
    mem_stats = []
    top_stats = []
    f = open(file_path, 'r')
    line = f.readline()
    while line:
        if date_regexp.search(line):
            current_date = parseDateText(line)
            line = f.readline()
        elif proc_stat_start_regexp.search(line):
            proc_stat_data = ProcStatData(current_date)
            line = proc_stat_data.parseText(f)
            cpu_stats.append(proc_stat_data)
        elif proc_meminfo_start_regexp.search(line):
            proc_meminfo_data = ProcMeminfoData(current_date)
            line = proc_meminfo_data.parseText(f)
            mem_stats.append(proc_meminfo_data)
        elif proc_top_start_regexp.search(line):
            top_data = TopData(current_date)
            line = top_data.parseText(f)
            top_stats.append(top_data)
        else:
            line = f.readline()
    return cpu_stats, mem_stats, top_stats

def getMemData(mem_stats_list):
    index = 0
    res = '# Index,MemTotal,MemFree,Cached,MemUsed\n'
    mem_stats = MemStats(mem_stats_list, 'Total_Free_Cached_Used')
    for mem_stat in mem_stats:
        total, free, cached, used = mem_stat
        res += '{0},{1},{2},{3},{4}\n'.format(index, total, free, cached, used)
        index += 1
    return res

if __name__ == '__main__':
    script_description = """
                           This script is for obtaining high-level android phone hardware 
                           resource usage statistics based on raw data collected from 
                           /proc/stat /proc/{pid}/stat and /proc/meminfo
                         """
    parser = argparse.ArgumentParser(description=script_description)
    parser.add_argument('input_file', type=str, help='input log file')
    args = parser.parse_args()
    cpu_stats_list, mem_stats_list, top_stats_list = parseLogFile(args.input_file)
    resource_usage_stats = ResourceUsageStats(cpu_stats_list, mem_stats_list)
    res = resource_usage_stats.getSummary()
    print (res)
