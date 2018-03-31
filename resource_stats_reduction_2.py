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

class ResourceStats(object):
    pass




class StatBunch(object):
    pass

class CpuStatBunch(StatBunch):
    pass

class MemStatBunch(StatBunch):
    pass


