
class Calculator:
    @staticmethod
    def multiply(a: int, b: int) -> int:
        """
        Multiply two integers.

        Args:
            a (int): The first integer.
            b (int): The second integer.

        Returns:
            int: The product of a and b.
        """
        return a * b
    
    @staticmethod
    def calculate_total(x: dict) -> float:
        """
        Calculate the sum of the given values.
        
        Args:
        x (dict): Dictionary containing numeric values.
        
        Returns:
        float: The sum of all numeric values in the dictionary.
        """
        return sum(float(value) for value in x.values())
    
    @staticmethod
    def calculate_daily_budget(total: float, days: int) -> float:
        """
        Calculate daily budget

        Args:
            total (float): Total cost.
            days (int): Total number of days

        Returns:
            float: Expense for a single day
        """
        return total / days if days > 0 else 0
    
    
