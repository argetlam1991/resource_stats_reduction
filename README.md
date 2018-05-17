resource_stats_reduction is used for measure android device hardware resource usage.

resource_stats_reduction contains Two python scripts:
1. resource_data_collection.py
2. resource_stats_reduction.py



resource_data_collection.py is used to read system file on android device and generate a data file based on android device system file info.
To be able to run it, you need to install adb first and make sure that there is only one android device is connecting to your workstation.

usage: usage: resource_stats_reduction.py [-h] [--input_file INPUT_FILE]
                                   [--start START] [--end END] [--export_csv]




resource_stats_reduction.py is used to parse data collected by resource_data_collection.py.

usage: python resource_stats_reduction.py <data_file>

sample of output:

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

