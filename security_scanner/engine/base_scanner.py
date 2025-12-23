"""
Base Scanner Abstract Class

Defines the interface for all security scanners.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from security_scanner.core.result import VulnerabilityResult, ScanResult


class BaseScanner(ABC):
    """
    Abstract base class for all security scanners.
    
    All scanner implementations must inherit from this class
    and implement the scan() method.
    """
    
    # Scanner identification
    name: str = "base"
    description: str = "Base scanner class"
    
    def __init__(self):
        """Initialize the scanner."""
        self.enabled = True
    
    @abstractmethod
    def scan(
        self, 
        files: Dict[str, str],
        **kwargs
    ) -> List[VulnerabilityResult]:
        """
        Scan files for vulnerabilities.
        
        Args:
            files: Dictionary mapping file paths to file contents
            **kwargs: Additional scanner-specific options
            
        Returns:
            List of vulnerability results found
        """
        pass
    
    def is_applicable(self, file_path: str) -> bool:
        """
        Check if this scanner is applicable to a file.
        
        Override this in subclasses to limit scanning to specific files.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if scanner should process this file
        """
        return True
    
    def pre_scan_hook(self, files: Dict[str, str]) -> None:
        """
        Hook called before scanning starts.
        
        Override to perform any setup or preprocessing.
        """
        pass
    
    def post_scan_hook(self, results: List[VulnerabilityResult]) -> List[VulnerabilityResult]:
        """
        Hook called after scanning completes.
        
        Override to perform any post-processing or filtering.
        
        Args:
            results: List of vulnerability results
            
        Returns:
            Processed list of results
        """
        return results
    
    def filter_false_positives(
        self, 
        results: List[VulnerabilityResult],
        files: Dict[str, str]
    ) -> List[VulnerabilityResult]:
        """
        Filter out likely false positives.
        
        Override to implement scanner-specific false positive detection.
        
        Args:
            results: List of vulnerability results
            files: Original files dict for context
            
        Returns:
            Filtered list of results
        """
        return results
