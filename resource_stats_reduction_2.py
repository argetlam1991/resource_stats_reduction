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



#RECORD_START_PATTERN = '-------- [a-zA-Z]{3,} [a-zA-Z]{3,} [0-9]{1,2} [0-9]{2,}:[0-9]{2,}:[0-9]{2,} GMT [0-9]{4,} --------'
RECORD_START_PATTERN = 'Fri'
PROCESS_CPU_STAT_PATTERN = '[0-9]+ \(.+\) [A-Z]'

class ResourceUsageStats(object):
    
    def __init__(self):
        self.cpu_stat_bunches = []
        self.mem_stat_bunches = []
    
    def getSummary(self):
        pass
    
class StatBunches(object):
    
    def __init__(self, file_path):
        pass

class StatsIterator(object):
    
    def __init__(self, stats_list, item_name):
        self.stats_list = stats_list
        self.item_name = item_name
        self.pre_stat = None
        self.current_stat = self.stats_list[0]
        self.index = 0
    
    def __iter__(self):
        return self
    
    def next(self):
        if self.index >= len(self.stats_list):
            raise StopIteration()
        if self.item_name == 'overall_cpu_usage_percentages':
            if self.pre_stat is None:
                self.__shiftStatByOne()
                self.next()
            else:
                percentage = self.__calculateCpuUsagePercentage(self.pre_stat.overall_data,
                                                                self.current_stat.overall_data)
                self.__shiftStatByOne()
                return percentage
        else:
            raise StopIteration()
    
    def __shiftStatByOne(self):
        self.pre_stat = self.current_stat
        self.index += 1
        if self.index >= len(self.stats_list): 
            self.current_stat = None
        else:
            self.current_stat = self.stats_list[self.index]
        
    def __calculateCpuUsagePercentage(self, previous, current):
        running_delta = current['running'] - previous['running']
        total_delta = current['total'] - previous['total']
        print (running_delta)
        print (total_delta)
        percentage = float(running_delta) / total_delta
        return percentage
            
        
class CpuStatBunches(StatBunches):

    def __init__(self, file_path):

        self.__file_path = file_path
        self.__start_regexp = re.compile('---- /proc/schedstat')
        self.__end_regexp = re.compile('---- ')

    def parseLogFile(self):
        self.__cpu_stat_bunches = []
        with open(self.__file_path, 'r') as f:
            start = False
            pre_cpu_stat_bunch = None
            current_cpu_stat_bunch = CpuStatBunch()
            for line in f:
                if self.__start_regexp.search(line):
                    start = True
                elif self.__end_regexp.search(line):
                    start = False
                    if pre_cpu_stat_bunch:
                        current_cpu_stat_bunch.calculage_cpu_usage(pre_cpu_stat_bunch)
                        self.cpu_stat_bunches.append(current_cpu_stat_bunch)
                        pre_cpu_stat_bunch = current_cpu_stat_bunch
                elif start is True:
                    current_cpu_stat_bunch.parseText(line)
    
    def getCpuStatBunches(self):
        return self.__cpu_stat_bunches

def parseLogFile(file_path):
    schedstat_start_regexp = re.compile('---- /proc/schedstat')
    meminfo_start_regexp = re.compile('---- /proc/meminfo')
    end_regexp = re.compile('---- ')
    cpu_stats = []
    with open(file_path, 'r') as f:
        schedstat_start = False
        meminfo_start = False
        current_cpu_stat_bunch = CpuStatBunch()
        for line in f:
            if schedstat_start_regexp.search(line):
                schedstat_start = True
            elif meminfo_start_regexp.search(line):
                schedstat_start = False
                cpu_stats.append(current_cpu_stat_bunch)
                current_cpu_stat_bunch = CpuStatBunch()
                meminfo_start = True
                schedstat_start = False
                # TODO: Initialize memStat_bunch
            elif end_regexp.search(line):
                # TODO: Add memStat_bunch to list
                meminfo_start = False
            elif schedstat_start:
                current_cpu_stat_bunch.parseText(line)
    return cpu_stats
    

class MemStatBunches(StatBunches):
    pass


class StatBunch(object):
    pass

class CpuStatBunch(StatBunch):
    
    def __init__(self):
        self.overall_data = {'running':0,
                             'waiting':0,
                             'total':0}
        self.percpu_data = {}

    def parseText(self, text):
        if text.startswith('cpu'):
            items = text.split()
            cpu_id = items[0]
            if cpu_id not in self.percpu_data: self.percpu_data[cpu_id] = {}
            (self.percpu_data[cpu_id])['running'] = int(items[7])
            (self.percpu_data[cpu_id])['waiting'] = int(items[8])
            (self.percpu_data[cpu_id])['total'] = (self.percpu_data[cpu_id])['running'] + \
                                                  (self.percpu_data[cpu_id])['waiting']
            self.overall_data['running'] += (self.percpu_data[cpu_id])['running']
            self.overall_data['waiting'] += (self.percpu_data[cpu_id])['waiting']
            self.overall_data['total'] += (self.percpu_data[cpu_id])['total']
            print (text)
            print (self.overall_data['running'])
            print (self.overall_data['total'])

class MemStatBunch(StatBunch):
    pass

def resourceStatsReduction(input_path):
    resource_usage_stats = ResourceUsageStats()
    resource_usage_stats.parseLogFile(input_path)
    resource_usage_stats.getSummary()
    
if __name__ == '__main__':
    script_description = """
                           This script is for obtaining high-level android phone hardware 
                           resource usage statistics based on raw data collected from 
                           /proc/stat /proc/{pid}/stat and /proc/meminfo
                         """
    parser = argparse.ArgumentParser(description=script_description)
    parser.add_argument('input_file', type=str, help='input log file')
    args = parser.parse_args()
    cpu_stats_list = parseLogFile(args.input_file)
    cpu_percentages = StatsIterator(cpu_stats_list, 'overall_cpu_usage_percentages')
    for percentage in cpu_percentages:
        print (percentage)