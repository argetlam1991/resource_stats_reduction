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

adb shell 'getprop ro.build.version.release; \
while :; do echo -------- $(date -u) --------; \
echo ---- /pid/stat; \
cat /proc/$(ps | grep com.usens | tr -s " " | cut -d " " -f 2)/stat; echo ---- top; top -d 3 -n 1 -m 10; \
echo ---- /proc/meminfo; cat /proc/meminfo; \
echo ---- /proc/stat; cat /proc/stat; \
sleep 3; done' | tee resource_stats_01.txt

"""
from __future__ import print_function
from __future__ import division


import re
import argparse



#RECORD_START_PATTERN = '-------- [a-zA-Z]{3,} [a-zA-Z]{3,} [0-9]{1,2} [0-9]{2,}:[0-9]{2,}:[0-9]{2,} GMT [0-9]{4,} --------'
RECORD_START_PATTERN = 'Fri'
PROCESS_CPU_STAT_PATTERN = '[0-9]+ \(.+\) [A-Z]'


class CpuInfo(object):
    """
      Calculate cpu usage depends on CpuData collected
    """

    def __init__(self):
        self.cpu_data_list = []

    def recevieNewData(self, cpu_data):
        if cpu_data.cpu_raw_values:
            self.cpu_data_list.append(cpu_data)

    def getSummary(self):
        res = ''

        res += 'Overall CPU - user + sys + IRQ min: {0:.1f}%\n'.format(self.overallCpuUsageUserSysIrqMin() * 100)
        res += 'Overall CPU - user + sys + IRQ avg: {0:.1f}%\n'.format(self.overallCpuUsageUserSysIrqAvg() * 100)
        res += 'Overall CPU - user + sys + IRQ max: {0:.1f}%\n'.format(self.overallCpuUsageUserSysIrqMax() * 100)
        
        res += 'Overall CPU - user min: {0:.1f}%\n'.format(self.overallCpuUsageUserMin() * 100)
        res += 'Overall CPU - user avg: {0:.1f}%\n'.format(self.overallCpuUsageUserAvg() * 100)
        res += 'Overall CPU - user max: {0:.1f}%\n'.format(self.overallCpuUsageUserMax() * 100)
    
        res += 'Overall CPU - sys + IRQ min: {0:.1f}%\n'.format(self.overallCpuUsageSysIrqMin() * 100)
        res += 'Overall CPU - sys + IRQ avg: {0:.1f}%\n'.format(self.overallCpuUsageSysIrqAvg() * 100)
        res += 'Overall CPU - sys + IRQ max: {0:.1f}%\n'.format(self.overallCpuUsageSysIrqMax() * 100)
    
        res += 'Per CPU - user + sys + IRQ min: {0:.1f}%\n'.format(self.perCoreCpuUsageUserSysIrqMin() * 100)
        res += 'Per CPU - user + sys + IRQ max: {0:.1f}%\n'.format(self.perCoreCpuUsageUserSysIrqMax() * 100)
    
        res += 'Per CPU - user min: {0:.1f}%\n'.format(self.perCoreCpuUsageUserMin() * 100)
        res += 'Per CPU - user max: {0:.1f}%\n'.format(self.perCoreCpuUsageUserMax() * 100)
    
        res += 'Per CPU - sys + IRQ min: {0:.1f}%\n'.format(self.perCoreCpuUsageSysIrqMin() * 100)
        res += 'Per CPU - sys + IRQ max: {0:.1f}%\n'.format(self.perCoreCpuUsageSysIrqMax() * 100)
        
        res += 'I/O min: {0:.1f}%\n'.format(self.ioMax() * 100)
        res += 'I/O avg: {0:.1f}%\n'.format(self.ioMax() * 100)
        res += 'I/O max: {0:.1f}%\n'.format(self.ioMax() * 100)
        
        res += 'APP process cpu usage min: {0:.1f}%\n'.format(self.appProcessUsageMin() * 100)
        res += 'APP process cpu usage avg: {0:.1f}%\n'.format(self.appProcessUsageAvg() * 100)
        res += 'APP process cpu usage max: {0:.1f}%\n'.format(self.appProcessUsageMax() * 100)
    
        return res

    def appProcessUsageMax(self):
        if len(self.__calculateAppProcessUsage()) <= 0: return -1
        return max(self.__calculateAppProcessUsage())
    
    def appProcessUsageMin(self):
        if len(self.__calculateAppProcessUsage()) <= 0: return -1
        return min(self.__calculateAppProcessUsage())
    
    def appProcessUsageAvg(self):
        if len(self.__calculateAppProcessUsage()) <= 0: return -1
        return sum(self.__calculateAppProcessUsage()) / (len(self.__calculateAppProcessUsage()))

    def overallCpuUsageUserSysIrqMax(self):
        if (len(self.cpu_data_list) - 1) <= 0: return -1
        return max(self.__calculateOverallCpuUsageUserSysIrq())
    
    def overallCpuUsageUserSysIrqMin(self):
        if (len(self.cpu_data_list) - 1) <= 0: return -1
        return min(self.__calculateOverallCpuUsageUserSysIrq())
    
    def overallCpuUsageUserSysIrqAvg(self):
        if (len(self.cpu_data_list) - 1) <= 0: return -1
        return sum(self.__calculateOverallCpuUsageUserSysIrq()) / (len(self.cpu_data_list) - 1)
    
    def overallCpuUsageUserMax(self):
        if (len(self.cpu_data_list) - 1) <= 0: return -1
        return max(self.__calculateOverallCpuUsageUser())
    
    def overallCpuUsageUserMin(self):
        if (len(self.cpu_data_list) - 1) <= 0: return -1
        return min(self.__calculateOverallCpuUsageUser())
    
    def overallCpuUsageUserAvg(self):
        if (len(self.cpu_data_list) - 1) <= 0: return -1
        return sum(self.__calculateOverallCpuUsageUser()) / (len(self.cpu_data_list) - 1)
    
    def overallCpuUsageSysIrqMax(self):
        if (len(self.cpu_data_list) - 1) <= 0: return -1
        return max(self.__calculateOverallCpuUsageSysIrq())
    
    def overallCpuUsageSysIrqMin(self):
        if (len(self.cpu_data_list) - 1) <= 0: return -1
        return min(self.__calculateOverallCpuUsageSysIrq())
    
    def overallCpuUsageSysIrqAvg(self):
        if (len(self.cpu_data_list) - 1) <= 0: return -1
        return sum(self.__calculateOverallCpuUsageSysIrq()) / (len(self.cpu_data_list) - 1)
    
    def perCoreCpuUsageUserSysIrqMax(self):
        if (len(self.cpu_data_list) - 1) <= 0: return -1
        return max(self.__calculatePerCoreUsageUserSysIrq())
    
    def perCoreCpuUsageUserSysIrqMin(self):
        if (len(self.cpu_data_list) - 1) <= 0: return -1
        return min(self.__calculatePerCoreUsageUserSysIrq())
    
    def perCoreCpuUsageUserSysIrqAvg(self):
        if (len(self.cpu_data_list) - 1) <= 0: return -1
        return sum(self.__calculatePerCoreUsageUserSysIrq()) / (len(self.cpu_data_list) - 1)
    
    def perCoreCpuUsageUserMax(self):
        if (len(self.cpu_data_list) - 1) <= 0: return -1
        return max(self.__calculatePerCoreUsageUser())
    
    def perCoreCpuUsageUserMin(self):
        if (len(self.cpu_data_list) - 1) <= 0: return -1
        return min(self.__calculatePerCoreUsageUser())
    
    def perCoreCpuUsageUserAvg(self):
        if (len(self.cpu_data_list) - 1) <= 0: return -1
        return sum(self.__calculatePerCoreUsageUser()) / (len(self.cpu_data_list) - 1)
    
    def perCoreCpuUsageSysIrqMax(self):
        if (len(self.cpu_data_list) - 1) <= 0: return -1
        return max(self.__calculatePerCoreUsageSysIrq())
    
    def perCoreCpuUsageSysIrqMin(self):
        if (len(self.cpu_data_list) - 1) <= 0: return -1
        return min(self.__calculatePerCoreUsageSysIrq())
    
    def perCoreCpuUsageSysIrqAvg(self):
        if (len(self.cpu_data_list) - 1) <= 0: return -1
        return sum(self.__calculatePerCoreUsageSysIrq()) / (len(self.cpu_data_list) - 1)
    
    def ioMax(self):
        if (len(self.cpu_data_list) - 1) <= 0: return -1
        return max(self.__calculateIO())
    
    def ioMin(self):
        if (len(self.cpu_data_list) - 1) <= 0: return -1
        return min(self.__calculateIO()) 
    
    def ioAvg(self):
        if (len(self.cpu_data_list) - 1) <= 0: return -1
        return sum(self.__calculateIO()) / (len(self.cpu_data_list) - 1)

    def __calculateOverallCpuUsageUserSysIrq(self):
        usages = []
        for i in xrange(1, len(self.cpu_data_list)):
            pre_cpu_data = self.cpu_data_list[i-1]
            cpu_data = self.cpu_data_list[i]
            cpu_precentage = cpu_data.calculateCpuUsageUserSysIrq(pre_cpu_data, 'cpu')
            usages.append(cpu_precentage)
        return usages

    def __calculateOverallCpuUsageUser(self):
        usages = []
        for i in xrange(1, len(self.cpu_data_list)):
            pre_cpu_data = self.cpu_data_list[i-1]
            cpu_data = self.cpu_data_list[i]
            cpu_precentage = cpu_data.calculateCpuUsageUser(pre_cpu_data, 'cpu')
            usages.append(cpu_precentage)
        return usages

    def __calculateOverallCpuUsageSysIrq(self):
        usages = []
        for i in xrange(1, len(self.cpu_data_list)):
            pre_cpu_data = self.cpu_data_list[i-1]
            cpu_data = self.cpu_data_list[i]
            cpu_precentage = cpu_data.calculateCpuUsageSysIrq(pre_cpu_data, 'cpu')
            usages.append(cpu_precentage)
        return usages
    
    def __calculateIO(self):
        usages = []
        for i in xrange(1, len(self.cpu_data_list)):
            pre_cpu_data = self.cpu_data_list[i-1]
            cpu_data = self.cpu_data_list[i]
            cpu_precentage = cpu_data.calculateIOUsage(pre_cpu_data)
            usages.append(cpu_precentage)
        return usages
    
    def __calculatePerCoreUsageUserSysIrq(self):
        usages = []
        for i in xrange(1, len(self.cpu_data_list)):
            pre_cpu_data = self.cpu_data_list[i-1]
            cpu_data = self.cpu_data_list[i]
            for cpu_id in cpu_data.cpu_raw_values:
                if re.match('cpu[0-9]+', cpu_id):
                    cpu_precentage = cpu_data.calculateCpuUsageUserSysIrq(pre_cpu_data, cpu_id)
                    usages.append(cpu_precentage)
        return usages
    
    def __calculatePerCoreUsageUser(self):
        usages = []
        for i in xrange(1, len(self.cpu_data_list)):
            pre_cpu_data = self.cpu_data_list[i-1]
            cpu_data = self.cpu_data_list[i]
            for cpu_id in cpu_data.cpu_raw_values:
                if re.match('cpu[0-9]+', cpu_id):
                    cpu_precentage = cpu_data.calculateCpuUsageUser(pre_cpu_data, cpu_id)
                    usages.append(cpu_precentage)
        return usages
    
    def __calculatePerCoreUsageSysIrq(self):
        usages = []
        for i in xrange(1, len(self.cpu_data_list)):
            pre_cpu_data = self.cpu_data_list[i-1]
            cpu_data = self.cpu_data_list[i]
            for cpu_id in cpu_data.cpu_raw_values:
                if re.match('cpu[0-9]+', cpu_id):
                    cpu_precentage = cpu_data.calculateCpuUsageSysIrq(pre_cpu_data, cpu_id)
                    usages.append(cpu_precentage)
        return usages
    
    def __calculateAppProcessUsage(self):
        usages = []
        for i in xrange(1, len(self.cpu_data_list)):
            pre_cpu_data = self.cpu_data_list[i-1]
            cpu_data = self.cpu_data_list[i]
            if 'process' in pre_cpu_data.cpu_raw_values and 'process' in cpu_data.cpu_raw_values:
                usage = cpu_data.calculateAppProcessUsage(pre_cpu_data)
                usages.append(usage)
        return usages


class CpuData(object):
    """
      Collect data from /proc/stat and /proc/{pid}/stat text
    """
    
    def __init__(self):
        self.cpu_raw_values = {}
        
    def isEmpty(self):
        return not self.cpu_raw_values
    
    def isValid(self):
        return not self.isEmpty()
    
    def captureCpuValues(self, text):
        """ Example
                 user  nice system idle    iowait irq  softirq steal guest guest_nice  
             cpu 74608 2520 24433  1117073 6176   4054 0       0     0     0 
        """
        values = {}
        if re.match(PROCESS_CPU_STAT_PATTERN, text):
            items = text.split()
            values['process_utime'] = int((items[13]))
            values['process_stime'] = int((items[14]))
            values['process_cutime'] = int((items[15]))
            values['process_cstime'] = int((items[16]))
            self.cpu_raw_values['process'] = values
        elif text.startswith('cpu'):
            items = text.split()
            values['cpu_idel'] = int(items[4])
            values['cpu_iowait'] = int(items[5])
            values['cpu_user'] = int(items[1])
            values['cpu_nice'] = int(items[2])
            values['cpu_system'] = int(items[3])
            values['cpu_irq'] = int(items[6])
            values['cpu_softirq'] = int(items[7])
            values['cpu_steal'] = int(items[8])
            cpu_id = items[0]
            self.cpu_raw_values[cpu_id] = values
    
    def calculateAppProcessUsage(self, pre_cpu_data):
        if 'process' not in pre_cpu_data.cpu_raw_values: return 0
        pre_value = pre_cpu_data.cpu_raw_values['process']
        value = self.cpu_raw_values['process']
        process_d = value['process_utime'] + value['process_stime'] + value['process_cutime'] + value['process_cstime'] - \
                    pre_value['process_utime'] - pre_value['process_stime'] - pre_value['process_cutime'] - pre_value['process_cstime']
        total_d = self.__calculatTotalDelta(pre_cpu_data, 'cpu')
        return float(process_d) / total_d
        
    def calculateCpuUsageUserSysIrq(self, pre_cpu_data, cpu_id):
        total_d = self.__calculatTotalDelta(pre_cpu_data, cpu_id)
        non_idle_d = self.__calculateNonIdleDelta(pre_cpu_data, cpu_id)
        cpu_percentage = float(non_idle_d) / float(total_d)
        return cpu_percentage
    
    def calculateCpuUsageUser(self, pre_cpu_data, cpu_id):
        total_d = self.__calculatTotalDelta(pre_cpu_data, cpu_id)
        user_d = self.__calculateUserDelta(pre_cpu_data, cpu_id)
        user_percentage = float(user_d) / float(total_d)
        return user_percentage
    
    def calculateCpuUsageSysIrq(self, pre_cpu_data, cpu_id):
        total_d = self.__calculatTotalDelta(pre_cpu_data, cpu_id)
        sys_irq_d = self.__calculateSysIrqDelta(pre_cpu_data, cpu_id)
        sys_irq_percentage = float(sys_irq_d) / float(total_d)
        return sys_irq_percentage
    
    def calculateIOUsage(self, pre_cpu_data):
        total_d = self.__calculatTotalDelta(pre_cpu_data, 'cpu')
        io_d = self.__calculateIODelta(pre_cpu_data)
        io_percentage = float(io_d) / float(total_d)
        return io_percentage
    
    def __calculatTotalDelta(self, pre_cpu_data, cpu_id):
        pre_values= pre_cpu_data.cpu_raw_values[cpu_id]
        values = self.cpu_raw_values[cpu_id]
        pre_idle = pre_values['cpu_idel'] + pre_values['cpu_iowait']
        idle = values['cpu_idel'] + values['cpu_iowait']
        pre_non_idle = pre_values['cpu_user'] + pre_values['cpu_nice'] + pre_values['cpu_system'] + \
                       pre_values['cpu_irq'] + pre_values['cpu_softirq'] + pre_values['cpu_steal']
        non_idle = values['cpu_user'] + values['cpu_nice'] + values['cpu_system'] + \
                   values['cpu_irq'] + values['cpu_softirq'] + values['cpu_steal']
        pre_total = pre_idle + pre_non_idle
        total = idle + non_idle
        total_d = total - pre_total
        return total_d
    
    def __calculateNonIdleDelta(self, pre_cpu_data, cpu_id):
        pre_values= pre_cpu_data.cpu_raw_values[cpu_id]
        values = self.cpu_raw_values[cpu_id]
        pre_non_idle = pre_values['cpu_user'] + pre_values['cpu_nice'] + pre_values['cpu_system'] + \
                       pre_values['cpu_irq'] + pre_values['cpu_softirq'] + pre_values['cpu_steal']
        non_idle = values['cpu_user'] + values['cpu_nice'] + values['cpu_system'] + \
                   values['cpu_irq'] + values['cpu_softirq'] + values['cpu_steal']
        non_idle_delta = non_idle - pre_non_idle
        return non_idle_delta
    
    def __calculateUserDelta(self, pre_cpu_data, cpu_id):
        pre_values= pre_cpu_data.cpu_raw_values[cpu_id]
        values = self.cpu_raw_values[cpu_id]
        user_delta = values['cpu_user'] - pre_values['cpu_user']
        return user_delta
    
    def __calculateSysIrqDelta(self, pre_cpu_data, cpu_id):
        pre_values= pre_cpu_data.cpu_raw_values[cpu_id]
        values = self.cpu_raw_values[cpu_id]
        pre_sys_irq = pre_values['cpu_system'] + pre_values['cpu_irq']
        sys_irq = values['cpu_system'] + pre_values['cpu_irq']
        sys_irq_delta = sys_irq - pre_sys_irq
        return sys_irq_delta
    
    def __calculateIODelta(self, pre_cpu_data):
        pre_values= pre_cpu_data.cpu_raw_values['cpu']
        values = self.cpu_raw_values['cpu']
        pre_io = pre_values['cpu_iowait']
        io = values['cpu_iowait']
        io_delta = io - pre_io
        return io_delta


class MemInfo(object):
    """
      calculate memory usage based on collected MemData
    """
    def __init__(self):
        self.mem_data_list = []
    
    def receiveMemData(self, mem_data):
        if not mem_data.isEmpty():
            self.mem_data_list.append(mem_data)
    
    def getSummary(self):
        res = ''
        res += 'Physical Memory (MB) min: {0}\n'.format(self.memMin() / 1024)
        res += 'Physical Memory (MB) avg: {0}\n'.format(self.memAvg() / 1024)
        res += 'Physical Memory (MB) max: {0}\n'.format(self.memMax() / 1024)
        res += 'Process Physical Memory (MB) min: {0}\n'.format(self.processMin() / 1024)
        res += 'Process Physical Memory (MB) avg: {0}\n'.format(self.processAvg() / 1024)
        res += 'Process Physical Memory (MB) max: {0}\n'.format(self.processMax() / 1024)
        return res

    def memMin(self):
        if len(self.mem_data_list) <= 0: return -1
        return min(self.__calculateMemUsages())
    
    def memMax(self):
        if len(self.mem_data_list) <= 0: return -1
        return max(self.__calculateMemUsages())
    
    def memAvg(self):
        if len(self.mem_data_list) <= 0: return -1
        return sum(self.__calculateMemUsages()) / len(self.mem_data_list)
    
    def virtMin(self):
        if len(self.mem_data_list) <= 0: return -1
        return min(self.__calculateVirtUsages())
    
    def virtMax(self):
        if len(self.mem_data_list) <= 0: return -1
        return max(self.__calculateVirtUsages())

    def virtAvg(self):
        if len(self.mem_data_list) <= 0: return -1
        return sum(self.__calculateVirtUsages()) / len(self.mem_data_list)
    
    def processMax(self):
        usages = self.__calculateProcessMemUsages()
        if len(usages) <= 0: return -1
        return max(usages)
    
    def processMin(self):
        usages = self.__calculateProcessMemUsages()
        if len(usages) <= 0: return -1
        return min(usages)
    
    def processAvg(self):
        usages = self.__calculateProcessMemUsages()
        if len(usages) <= 0: return -1
        return sum(usages) / len(usages)

    def __calculateMemUsages(self):
        usages = []
        for mem_data in self.mem_data_list:
            usages.append(mem_data.calculateMemUsage())
        return usages
    
    def __calculateVirtUsages(self):
        usages = []
        for mem_data in self.mem_data_list:
            usages.append(mem_data.calculateVmUsage())
        return usages
    
    def __calculateProcessMemUsages(self):
        usages = []
        for mem_data in self.mem_data_list:
            if mem_data.calculateProcessMemUsage() >= 0:
                usages.append(mem_data.calculateProcessMemUsage())
        return usages


class MemData(object):
    """
      Collect data from /proc/meminfo
    """
    
    def __init__(self):
        self.mem_raw_values = {}
    
    def isEmpty(self):
        return not self.mem_raw_values
    
    def isValid(self):
        if 'MemFree' not in self.mem_raw_values: return False
        if 'MemTotal' not in self.mem_raw_values: return False
        if 'Buffers' not in self.mem_raw_values: return False
        if 'Cached' not in self.mem_raw_values: return False
        if 'SReclaimable' not in self.mem_raw_values: return False
        if 'Shmem' not in self.mem_raw_values: return False
        return True
        
    def captureMemValues(self, text):
        items = text.split()
        if len(items) <= 0: return
        if items[0] == 'MemTotal:':
            self.mem_raw_values['MemTotal'] = int(items[1])
        elif items[0] == 'MemFree:':
            self.mem_raw_values['MemFree'] = int(items[1])
        elif items[0] == 'Buffers:':
            self.mem_raw_values['Buffers'] = int(items[1])
        elif items[0] == 'Cached:':
            self.mem_raw_values['Cached'] = int(items[1])
        elif items[0] == 'SReclaimable:':
            self.mem_raw_values['SReclaimable'] = int(items[1])
        elif items[0] == 'Shmem:':
            self.mem_raw_values['Shmem'] = int(items[1])
        elif items[0] == 'VmallocTotal:':
            self.mem_raw_values['VmallocTotal'] = int(items[1])
        elif items[0] == 'VmRSS:':
            self.mem_raw_values['process_VmRss'] = int(items[1])
            
    def calculateMemUsage(self):
        total_used_memory = self.mem_raw_values['MemTotal'] - self.mem_raw_values['MemFree'] -\
                            (self.mem_raw_values['Buffers'] + \
                             (self.mem_raw_values['Cached'] + self.mem_raw_values['SReclaimable'] - self.mem_raw_values['Shmem']))
        return total_used_memory
    
    def calculateVmUsage(self):
        return self.mem_raw_values['VmallocTotal']
    
    def calculateProcessMemUsage(self):
        if 'process_VmRss' in self.mem_raw_values:
            return self.mem_raw_values['process_VmRss']
        else:
            return -1

def resourceStatsReduction(input_path):
    cpu_info = CpuInfo()
    mem_info = MemInfo()
    regexp = re.compile(RECORD_START_PATTERN)
    with open(input_path, 'r') as f:
        cpu_usage_record = CpuData()
        mem_usage_record = MemData()
        for line in f:
            if regexp.search(line):
                print (line)
                cpu_info.recevieNewData(cpu_usage_record)
                mem_info.receiveMemData(mem_usage_record)
                cpu_usage_record = CpuData()
                mem_usage_record = MemData()
            cpu_usage_record.captureCpuValues(line)
            mem_usage_record.captureMemValues(line)
        if not cpu_usage_record.isValid(): cpu_info.recevieNewData(cpu_usage_record)
        if not mem_usage_record.isValid(): mem_info.receiveMemData(mem_usage_record)
    print (cpu_info.getSummary())
    print (mem_info.getSummary())


if __name__ == '__main__':
    script_description = """
                           This script is for obtaining high-level android phone hardware 
                           resource usage statistics based on raw data collected from 
                           /proc/stat /proc/{pid}/stat and /proc/meminfo
                         """
    parser = argparse.ArgumentParser(description=script_description)
    parser.add_argument('input_file', type=str, help='input log file')
    args = parser.parse_args()
    resourceStatsReduction(args.input_file)