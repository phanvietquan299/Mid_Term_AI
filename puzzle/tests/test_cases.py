"""
Test cases for 8-puzzle solver
Only test solvable states with A+B=9 rule
"""
from typing import List


class TestCases:
    """Valid test cases - solvable"""
    
    @staticmethod
    def get_easy_cases() -> List[List[List[int]]]:
        """Easy test cases (1-2 steps)"""
        return [
            # Group 1: Blank at (2,2) - to Goal 1
            [[1, 2, 3], [5, 4, 6], [7, 8, 0]],  # Swap 4↔5
            [[1, 2, 6], [4, 5, 3], [7, 8, 0]],  # Swap 3↔6
            [[1, 7, 3], [4, 5, 6], [2, 8, 0]],  # Swap 2↔7
            [[8, 2, 3], [4, 5, 6], [7, 1, 0]],  # Corner swap 1↔8
            
            # Group 2: Blank at (0,0) - to Goal 3
            [[0, 2, 1], [3, 4, 5], [6, 7, 8]],  # Swap 1↔2
            [[0, 1, 2], [6, 4, 5], [3, 7, 8]],  # Swap 3↔6
        ]
    
    @staticmethod
    def get_medium_cases() -> List[List[List[int]]]:
        """Medium test cases (3-5 steps)"""
        return [
            # Blank at (2,2)
            [[1, 2, 6], [5, 4, 3], [7, 8, 0]],  # Swap 3↔6, then 4↔5
            [[1, 7, 3], [5, 4, 6], [2, 8, 0]],  # Swap 2↔7, then 4↔5
            [[2, 1, 3], [4, 5, 6], [7, 8, 0]],  # Corner swap + sum9
            
            # Blank at (0,0)
            [[0, 2, 1], [6, 4, 5], [3, 7, 8]],  # Swap 1↔2, 3↔6
            [[0, 1, 5], [3, 4, 2], [6, 7, 8]],  # Multiple steps
        ]
        
    def get_hard_cases() -> List[List[List[int]]]:
        """Hard test cases (6+ steps)"""
        return [
            # Blank at (2,2)
            [[5, 1, 3], [4, 2, 6], [7, 8, 0]],  # Complex case
            [[1, 2, 3], [6, 4, 5], [7, 8, 0]],  # Multiple swaps
            
            # Blank at (0,0)
            [[0, 5, 1], [3, 2, 4], [6, 7, 8]],  # Complex case
            [[0, 2, 3], [1, 4, 5], [6, 7, 8]],  # Multiple swaps
        
        ]
    
    @staticmethod
    def get_all_cases() -> List[List[List[int]]]:
        """All test cases"""
        return (TestCases.get_easy_cases() + 
                TestCases.get_medium_cases())