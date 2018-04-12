import unittest
from resource_stats_reduction import ResourceUsageStats
from resource_stats_reduction import StatsFactory
from resource_stats_reduction import CpuStats
from resource_stats_reduction import MemStats
from resource_stats_reduction import ProcStatData
from resource_stats_reduction import ProcMeminfoData

class TestFactorial(unittest.TestCase):
    
    def test_fact(self):
        expect = 'Hello'
        actual = 'Hello'
        self.assertEqual(expect, actual)
        
    

if __name__ == '__main__':
    unittest.main()