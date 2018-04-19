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
        res = 'Overall CPU - user + sys + irq min: {0:.1f}%\n'.format(min(StatsFactory.CreateIterableStats(self.cpu_stats_list, 'overall user + system')))
        res += 'Overall CPU - user + sys + irq avg: {0:.1f}%\n'.format(sum(StatsFactory.CreateIterableStats(self.cpu_stats_list, 'overall user + system')) / \
                                                          (len(self.cpu_stats_list) - 1))
        res += 'Overall CPU - user + sys + irq max: {0:.1f}%\n'.format(max(StatsFactory.CreateIterableStats(self.cpu_stats_list, 'overall user + system')))
        res += 'Overall CPU - user + sys + irq Max - Min: {0:.1f}%\n'.format(max(StatsFactory.CreateIterableStats(self.cpu_stats_list, 'overall user + system')) -  \
                                                                             min(StatsFactory.CreateIterableStats(self.cpu_stats_list, 'overall user + system')))
        res += 'Overall CPU - user + sys + irq Last - First: {0:.1f}%\n'.format((StatsFactory.CreateIterableStats(self.cpu_stats_list, 'overall user + system'))[-1] - \
                                                                                (StatsFactory.CreateIterableStats(self.cpu_stats_list, 'overall user + system'))[0])

        res += 'Overall CPU - user min: {0:.1f}%\n'.format(min(StatsFactory.CreateIterableStats(self.cpu_stats_list, 'overall user')))
        res += 'Overall CPU - user avg: {0:.1f}%\n'.format(sum(StatsFactory.CreateIterableStats(self.cpu_stats_list, 'overall user')) / \
                                                          (len(self.cpu_stats_list) - 1))
        res += 'Overall CPU - user max: {0:.1f}%\n'.format(max(StatsFactory.CreateIterableStats(self.cpu_stats_list, 'overall user')))

        res += 'Overall CPU - sys min: {0:.1f}%\n'.format(min(StatsFactory.CreateIterableStats(self.cpu_stats_list, 'overall system')))
        res += 'Overall CPU - sys avg: {0:.1f}%\n'.format(sum(StatsFactory.CreateIterableStats(self.cpu_stats_list, 'overall system')) / \
                                                          (len(self.cpu_stats_list) - 1))
        res += 'Overall CPU - sys max: {0:.1f}%\n'.format(max(StatsFactory.CreateIterableStats(self.cpu_stats_list, 'overall system')))

        res += 'Per CPU - user + sys min: {0:.1f}%\n'.format(min([min(x) for x in StatsFactory.CreateIterableStats(self.cpu_stats_list, 'per CPU user + system')]))
        res += 'Per CPU - user + sys max: {0:.1f}%\n'.format(max([max(x) for x in StatsFactory.CreateIterableStats(self.cpu_stats_list, 'per CPU user + system')]))

        res += 'Per CPU - user min: {0:.1f}%\n'.format(min([min(x) for x in StatsFactory.CreateIterableStats(self.cpu_stats_list, 'per CPU user')]))
        res += 'Per CPU - user max: {0:.1f}%\n'.format(max([max(x) for x in StatsFactory.CreateIterableStats(self.cpu_stats_list, 'per CPU user')]))

        res += 'Per CPU - sys min: {0:.1f}%\n'.format(min([min(x) for x in StatsFactory.CreateIterableStats(self.cpu_stats_list, 'per CPU system')]))
        res += 'Per CPU - sys max: {0:.1f}%\n'.format(max([max(x) for x in StatsFactory.CreateIterableStats(self.cpu_stats_list, 'per CPU system')]))

        res += 'Memory in use (MiB) min: {0:.1f}\n'.format(min(StatsFactory.CreateIterableStats(self.mem_stats_list, 'MemUsed')) / 1024)
        res += 'Memory in use (MiB) avg: {0:.1f}\n'.format((sum(StatsFactory.CreateIterableStats(self.mem_stats_list, 'MemUsed')) / 1024) /
                                                     len(self.mem_stats_list))
        res += 'Memory in use (MiB) max: {0:.1f}\n'.format(max(StatsFactory.CreateIterableStats(self.mem_stats_list, 'MemUsed')) / 1024)

        res += 'Memory in use (MiB) Max - Min : {0:.1f}\n'.format((max(StatsFactory.CreateIterableStats(self.mem_stats_list, 'MemUsed')) - \
                                                         min(StatsFactory.CreateIterableStats(self.mem_stats_list, 'MemUsed')))  / 1024)
        res += 'Memory in use (MiB) Last - First: {0:.1f}'.format(((StatsFactory.CreateIterableStats(self.mem_stats_list, 'MemUsed'))[-1] - \
                                                                   (StatsFactory.CreateIterableStats(self.mem_stats_list, 'MemUsed'))[0]) / 1024)
        return res


class StatsFactory(object):

    @classmethod
    def CreateIterableStats(cls, stats_list, query):
        if query == 'overall user + system':
            return CpuStats(stats_list, query)
        elif query == 'overall user':
            return CpuStats(stats_list, query)
        elif query == 'overall system':
            return CpuStats(stats_list, query)
        elif query == 'per CPU user + system':
            return CpuStats(stats_list, query)
        elif query == 'per CPU user':
            return CpuStats(stats_list, query)
        elif query == 'per CPU system':
            return CpuStats(stats_list, query)
        elif query == 'MemUsed':
            return MemStats(stats_list, query)
        else:
            return None


class CpuStats(object):

    def __init__(self, cpu_stats_list, query):
        self.stats_list = cpu_stats_list
        self.query = query
        self.pre_stat = None
        self.current_stat = self.stats_list[0]
        self.index = 0
        self.__shiftOneStat()

    def __getitem__(self, index):
        pre_index = index
        cur_index = index + 1
        if index <  0:
            pre_index = index - 1
            cur_index = index
        previous = self.stats_list[pre_index]
        current = self.stats_list[cur_index]
        return self.__getPercentage(previous, current)

    def __iter__(self):
        return self

    def next(self):
        if self.index >= len(self.stats_list):
            raise StopIteration()
        res = self.__getPercentage(self.pre_stat, self.current_stat)
        self.__shiftOneStat()
        return res

    def __getPercentage(self, previous, current):
        if self.query == 'overall user + system':
            res = self.__getUserPercentage(previous, current, 'cpu') + \
                  self.__getSysPercentage(previous, current, 'cpu')
        elif self.query == 'overall user':
            res = self.__getUserPercentage(previous, current, 'cpu')
        elif self.query == 'overall system':
            res = self.__getSysPercentage(previous, current, 'cpu')
        elif self.query == 'per CPU user + system':
            res = []
            for cpu_id in xrange(self.getCpuCoreCount()):
                res.append(self.__getUserPercentage(previous, current, 'cpu'+ str(cpu_id)) + \
                           self.__getSysPercentage(previous, current, 'cpu'+ str(cpu_id)))
        elif self.query == 'per CPU user':
            res = []
            for cpu_id in xrange(self.getCpuCoreCount()):
                res.append(self.__getUserPercentage(previous, current, 'cpu'+ str(cpu_id)))
        elif self.query == 'per CPU system':
            res = []
            for cpu_id in xrange(self.getCpuCoreCount()):
                res.append(self.__getSysPercentage(previous, current, 'cpu'+ str(cpu_id)))
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

    def __getUserPercentage(self, previous, current, cpu_id):
        total_delta = self.__getTotalDelta(previous, current, cpu_id)
        current_user_time = (current.data[cpu_id])['user'] + (current.data[cpu_id])['nice']
        previous_user_time = (previous.data[cpu_id])['user'] + (previous.data[cpu_id])['nice']
        user_delta = current_user_time - previous_user_time
        percentage = float(user_delta) / total_delta * 100
        return percentage

    def __getSysPercentage(self, previous, current, cpu_id):
        total_delta = self.__getTotalDelta(previous, current, cpu_id)
        current_sys_time = (current.data[cpu_id])['system'] + (current.data[cpu_id])['irq'] + (current.data[cpu_id])['softirq']
        previous_sys_time = (previous.data[cpu_id])['system'] + (previous.data[cpu_id])['irq'] + (previous.data[cpu_id])['softirq']
        sys_delta = current_sys_time - previous_sys_time
        percentage = float(sys_delta) / total_delta * 100
        return percentage
    
    def __getTotalDelta(self, previous, current, cpu_id):
        time_delta = (current.date - previous.date).total_seconds() * 100
        if cpu_id == 'cpu':
            time_delta *= self.getCpuCoreCount()
        return time_delta
        
        

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
    
    def __getitem__(self, index):
        return self.__getUsage(self.stats_list[index])

    def next(self):
        if self.index >= len(self.stats_list):
            raise StopIteration()
        res = self.__getUsage(self.current_stat)
        self.__shiftOneStat()
        return res
        
    def __getUsage(self, stat):
        if self.query == 'Total_Free_Cached_Used':
            res = [stat.data['MemTotal'],
                   stat.data['MemFree'],
                   stat.data['Cached'],
                   self.__getMemUsed(stat)]
            return res
        elif self.query == 'MemUsed':
            used = self.__getMemUsed(stat)
            return used
        else:
            raise Exception('unsupported query')
        
    def __getMemUsed(self, stat):
        used = stat.data['MemTotal'] - \
               stat.data['MemFree'] - \
               stat.data['Cached']
        return used
        

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
        text = re.match('(.*)-------- (.*) --------', text).group(2)
        date = datetime.strptime(text, '%a %b %d %H:%M:%S %Z %Y')
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
