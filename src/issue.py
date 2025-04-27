from dataclasses import dataclass
from typing import Dict, List, Optional, Any

@dataclass
class Issue:
    """Represents an IEEE TVLSI issue"""
    volume: int
    issue: int
    month: str
    numerical_month: int
    year: int
    isnumber: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Issue':
        """Create an Issue instance from a dictionary"""
        return cls(
            volume=int(data['volume']),
            issue=int(data['issue']),
            month=data['month'],
            numerical_month=int(data['numerical_month']),
            year=int(data['year']),
            isnumber=data['isnumber']
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'volume': self.volume,
            'issue': self.issue,
            'month': self.month,
            'numerical_month': self.numerical_month,
            'year': self.year,
            'isnumber': self.isnumber
        }
    
    def __eq__(self, other):
        """Compare two issues for equality"""
        if not isinstance(other, Issue):
            return False
        return (self.volume == other.volume and 
                self.issue == other.issue and 
                self.year == other.year)
    
    def __lt__(self, other):
        """Compare issues chronologically"""
        if not isinstance(other, Issue):
            return NotImplemented
        return (self.year, self.volume, self.numerical_month, self.issue) < \
               (other.year, other.volume, other.numerical_month, other.issue)