resource_stats_reduction is used for measure android device hardware resource usage.

resource_stats_reduction contains Two python scripts:
1. resource_data_collection.py
2. resource_stats_reduction.py

resource_data_collection.py is used to read system file on android device and generate a data file based on android device system file info.
To be able to run it, you need to install adb first and make sure that there is only one android device is connecting to your workstation.

usage:

python resource_data_collection.py <output_data_path>

sample of output_data:
--------------------------------------------------------------
-------- Mon Apr 30 20:09:19 GMT 2018 --------
---- /proc/meminfo
MemTotal:        5876336 kB
MemFree:          257208 kB
MemAvailable:    3492408 kB
Buffers:            7328 kB
Cached:          3083592 kB
SwapCached:        75376 kB
Active:          2201744 kB
Inactive:        1625000 kB
...
...
---- /proc/stat
cpu  25690994 1024226 12934288 736093304 58852 4188 125843 0 0 0
cpu0 5846302 191818 3909207 136754341 17988 1150 105444 0 0 0
cpu1 6389485 193191 3044296 85347348 13623 914 10613 0 0 0
...
...
---- top
User 4%, System 17%, IOW 0%, IRQ 0%
User 2 + Nice 0 + Sys 8 + Idle 37 + IOW 0 + IRQ 0 + SIRQ 0 = 47

  PID USER     PR  NI CPU% S  #THR     VSS     RSS PCY Name
14962 shell    20   0   6% R     1   9136K   1928K  fg top
   68 root     20   0   6% S     1      0K      0K  fg kcompactd0
    3 root     20   0   0% S     1      0K      0K  fg ksoftirqd/0
    5 root      0 -20   0% S     1      0K      0K  fg kworker/0:0H
    7 root     20   0   0% S     1      0K      0K  fg rcu_preempt
    8 root     20   0   0% S     1      0K      0K  fg rcu_sched
--------------------------------------------------------------

resource_stats_reduction.py is used to parse data collected by resource_data_collection.py.

usage: python resource_stats_reduction.py <data_file>

sample of output:
--------------------------------------------------------------
Overall CPU - user + sys + irq min: 0.9%
Overall CPU - user + sys + irq avg: 3.5%
Overall CPU - user + sys + irq max: 18.1%
Overall CPU - user + sys + irq Max - Min: 17.1%
Overall CPU - user + sys + irq Last - First: -0.1%
Overall CPU - user min: 0.4%
Overall CPU - user avg: 1.8%
Overall CPU - user max: 9.8%
Overall CPU - sys min: 0.5%
Overall CPU - sys avg: 1.7%
Overall CPU - sys max: 8.2%
Per CPU - user + sys min: 0.0%
Per CPU - user + sys max: 36.0%
Per CPU - user min: 0.0%
Per CPU - user max: 36.0%
Per CPU - sys min: 0.0%
Per CPU - sys max: 36.0%
Memory in use (MiB) min: 2475.3
Memory in use (MiB) avg: 2482.0
Memory in use (MiB) max: 2498.2
Memory in use (MiB) Max - Min : 23.0
Memory in use (MiB) Last - First: -0.9
--------------------------------------------------------------
