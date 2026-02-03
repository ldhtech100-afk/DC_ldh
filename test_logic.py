
import unittest
import pandas as pd
import numpy as np
from utils import calculate_top_3, calculate_least_3, get_missing_forms_count

class TestDashboardLogic(unittest.TestCase):
    
    def setUp(self):
        # Create a mock dataframe
        data = {
            'VLE Name': ['A', 'B', 'C', 'D', 'E'],
            'Cards Issued': [10, 20, 30, 5, np.nan],
            'Date': pd.to_datetime(['2025-01-01'] * 5)
        }
        self.df = pd.DataFrame(data)
        
    def test_top_3(self):
        # Top 3 should be C (30), B (20), A (10)
        top = calculate_top_3(self.df, 'VLE Name')
        expected_names = ['C', 'B', 'A']
        self.assertListEqual(top['VLE Name'].tolist(), expected_names)
        self.assertListEqual(top['Cards Issued'].tolist(), [30, 20, 10])

    def test_least_3(self):
        # Least 3: D (5), A (10), B (20). 
        # Note: calculate_least_3 includes those with values. 
        # Depending on implementation, NaN might be excluded or treated as 0.
        # In my utils, I simply sort ascending. NaN is usually at the end (bottom) in pandas default sort unless na_position='first'.
        # Let's check pandas default: ascending=True puts NaNs at the end.
        # So least should be D, A, B.
        
        least = calculate_least_3(self.df, 'VLE Name')
        expected_names = ['D', 'A', 'B']
        self.assertListEqual(least['VLE Name'].tolist(), expected_names)
        self.assertListEqual(least['Cards Issued'].tolist(), [5, 10, 20])

    def test_missing_forms(self):
        # 1 VLE (E) has NaN
        count = get_missing_forms_count(self.df)
        self.assertEqual(count, 1)

if __name__ == '__main__':
    unittest.main()
