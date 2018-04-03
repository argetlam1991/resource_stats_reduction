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

class CpuStatBunches(StatBunches):

    def __init__(self, file_path):
        self.__cpu_stat_bunches = []
        self.__file_path = file_path
        self.__start_regexp = re.compile('---- /proc/schedstat')
        self.__end_regexp = re.compile('---- ')

    def parseLogFile(self):
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
    
    def getOverallCpuUsagePercentages(self):
        for i in xrange(1, len(self.__cpu_stat_bunches)):
            current = self.__cpu_stat_bunches[i]
            previous = self.__cpu_stat_bunches[i-1]
            running_delta = current.overall_data['running'] - \
                            previous.overall_data['running']
            total_delta = current.overall_data['total'] - \
                          previous.overall_data['total']
            percentage = float(running_delta) / total_delta
            yield percentage
    
    

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
            if cpu_id not in self.data: self.data[cpu_id] = {}
            (self.percpu_data[cpu_id])['running'] = int(items[7])
            (self.percpu_data[cpu_id])['waiting'] = int(items[8])
            (self.percpu_data[cpu_id])['total'] = (self.percpu_data[cpu_id])['running'] + \
                                                  (self.percpu_data[cpu_id])['waiting']
            self.overall_data['running'] += (self.percpu_data[cpu_id])['running']
            self.overall_data['waiting'] += (self.percpu_data[cpu_id])['waiting']
            self.overall_data['total'] += (self.percpu_data[cpu_id])['total']

    def calculage_cpu_usage(self, pre_cpu_stat_bunch):
        self.overall_data['total_delta'] = self.overall_data['total'] - pre_cpu_stat_bunch['total']
        self.overall_data
        for cpu_id in self.percpu_data:
            (self.percpu_data[cpu_id])['total_delta'] = (self.percpu_data[cpu_id])['total'] - \
                                                  (pre_cpu_stat_bunch[cpu_id])['total']

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
    resource_usage_stats = ResourceUsageStats()
    resource_usage_stats.parseLogFile(args.input_file)
    resource_usage_stats.getSummary()