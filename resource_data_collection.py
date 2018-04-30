from __future__ import print_function
from __future__ import division

import subprocess
import os.path
import time
import argparse


class AndroidDeviceFactory(object):

    def createDevice(self):
        os_version = self.__identifyOSVersion()
        if os_version.startswith('7'):
            return Android7Deivce()
        elif os_version.startswith('8'):
            return Andoroid8Device()
        elif os_version.startswith('6'):
            return Android6Deivce()

    def __identifyOSVersion(self):
        os_version = subprocess.check_output(['adb', 'shell', 'getprop', 'ro.build.version.release'])
        return os_version


class AndroidDeivce(object):
    
    def sendCommand(self, cmd):
        return subprocess.check_output(['adb', 'shell', cmd])
    
    def getDate(self):
        return self.sendCommand('date -u')


class Android6Deivce(AndroidDeivce):
    
    def getTopOutput(self):
        return self.sendCommand('top -n 1')


class Android7Deivce(AndroidDeivce):
    
    def getTopOutput(self):
        return self.sendCommand('top -n 1')
    
    
class Andoroid8Device(AndroidDeivce):
    
    def getTopOutput(self):
        return self.sendCommand('top -n 1 -b')
    
    
class StatsCollector(object):
    
    def __init__(self, device, data_file_path):
        self.device = device
        if os.path.exists(data_file_path):
            raise Exception(data_file_path + ' already exists')
        self.data_file_path = data_file_path
    
    def collectStat(self):
        res = '-------- {0} --------\n'.format(self.device.getDate().rstrip())
        res += '---- /proc/meminfo\n'
        res += self.device.sendCommand('cat /proc/meminfo')
        res += '---- /proc/stat\n'
        res += self.device.sendCommand('cat /proc/stat')
        res += '---- top\n'
        res += self.device.getTopOutput()
        return res
    
    def runCollection(self):
        while True:
            output = self.collectStat()
            with open(self.data_file_path, 'a+') as f:
                f.write(output)
            print (output)
            time.sleep(3)


if __name__ == '__main__':
    script_description = """
                           This script is for collecting android phone hardware 
                           resource usage data
                         """
    args_parser = argparse.ArgumentParser(description=script_description)
    args_parser.add_argument('data_file_path', type=str, help='output data file path')
    args = args_parser.parse_args()    
    
    deviceFactory = AndroidDeviceFactory() 
    device = deviceFactory.createDevice()
    collector = StatsCollector(device, args.data_file_path)
    collector.runCollection()
    