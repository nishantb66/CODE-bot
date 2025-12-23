"""
Scan Orchestrator

Coordinates all security scanners and aggregates results.
This is the main entry point for security scanning.
"""
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Type
from concurrent.futures import ThreadPoolExecutor, as_completed

from security_scanner.engine.base_scanner import BaseScanner
from security_scanner.engine.dependency_scanner import DependencyScanner
from security_scanner.engine.code_pattern_scanner import CodePatternScanner
from security_scanner.engine.secret_scanner import SecretScanner
from security_scanner.engine.config_scanner import ConfigScanner
from security_scanner.engine.cicd_scanner import CICDScanner
from security_scanner.core.result import ScanResult, VulnerabilityResult
from security_scanner.core.severity import Severity
from security_scanner.services.github_fetcher import GitHubFetcher, GitHubFetcherError, FetchResult

logger = logging.getLogger(__name__)


class ScanOrchestrator:
    """
    Orchestrates the security scanning process.
    
    Features:
    - Priority-based scanning (dependencies first)
    - Chunk-based analysis for large repositories
    - Detailed tracking of scanned files
    - Transparency about what was analyzed
    """
    
    # Default scanners to run
    DEFAULT_SCANNERS: List[Type[BaseScanner]] = [
        DependencyScanner,
        SecretScanner,
        CodePatternScanner,
        ConfigScanner,
        CICDScanner,
    ]
    
    def __init__(
        self, 
        scanners: Optional[List[Type[BaseScanner]]] = None,
        parallel: bool = True,
        max_workers: int = 5
    ):
        """Initialize the orchestrator."""
        self.scanner_classes = scanners or self.DEFAULT_SCANNERS
        self.parallel = parallel
        self.max_workers = max_workers
        self.github_fetcher = GitHubFetcher()
        
        # Initialize scanner instances
        self.scanners = [cls() for cls in self.scanner_classes]
    
    def scan_repository(
        self, 
        repo_url: str,
        max_files: Optional[int] = None,
        include_low_confidence: bool = False,
        chunk_start: int = 0
    ) -> ScanResult:
        """
        Perform a complete security scan of a GitHub repository.
        
        Args:
            repo_url: GitHub repository URL
            max_files: Maximum number of files to scan
            include_low_confidence: Whether to include low-confidence findings
            chunk_start: Starting offset for chunked scanning
            
        Returns:
            ScanResult containing all findings with detailed metadata
        """
        start_time = time.time()
        result = ScanResult(
            repository_url=repo_url,
            scan_started_at=datetime.utcnow()
        )
        
        try:
            # Validate and get repository info
            logger.info(f"Starting security scan of {repo_url}")
            repo_info = self.github_fetcher.get_repository_info(repo_url)
            result.metadata['repository_name'] = repo_info.get('full_name')
            result.metadata['default_branch'] = repo_info.get('default_branch')
            result.metadata['is_private'] = repo_info.get('private', False)
            
            # Fetch repository files with prioritization
            logger.info("Fetching repository files...")
            fetch_result: FetchResult = self.github_fetcher.fetch_repository_files(
                repo_url, 
                max_files=max_files,
                chunk_start=chunk_start
            )
            
            files = fetch_result.files
            
            if not files:
                logger.warning("No files found to scan")
                result.error = "No scannable files found in repository"
                result.complete_scan()
                return result
            
            result.files_scanned = len(files)
            
            # Store detailed scan information in metadata
            result.metadata['scan_details'] = {
                'total_files_in_repo': fetch_result.total_files_in_repo,
                'files_scanned_count': len(fetch_result.files_scanned),
                'files_skipped_count': len(fetch_result.files_skipped),
                'has_more_files': fetch_result.has_more_files,
                'next_chunk_start': fetch_result.next_chunk_start,
                
                # Categorized file lists
                'dependency_files_found': fetch_result.dependency_files,
                'config_files_found': fetch_result.config_files,
                'source_files_scanned': fetch_result.source_files[:50],  # Limit for response
                
                # Files actually scanned (for transparency)
                'files_analyzed': sorted(fetch_result.files_scanned)[:100],
            }
            
            # Build scan summary message
            result.metadata['scan_summary'] = self._build_scan_summary(fetch_result)
            
            logger.info(f"Fetched {len(files)} files, starting security analysis...")
            
            # Run all scanners
            all_vulnerabilities = self._run_scanners(files)
            
            # Filter low confidence if requested
            if not include_low_confidence:
                all_vulnerabilities = self._filter_low_confidence(all_vulnerabilities)
            
            # Deduplicate across scanners
            all_vulnerabilities = self._deduplicate_vulnerabilities(all_vulnerabilities)
            
            # Add to result
            result.add_vulnerabilities(all_vulnerabilities)
            
            # Add scan summary to metadata
            result.metadata['scanners_used'] = [s.name for s in self.scanners]
            result.metadata['scan_duration_seconds'] = round(time.time() - start_time, 2)
            
            # Add scan coverage information
            result.metadata['coverage'] = {
                'dependency_analysis': len(fetch_result.dependency_files) > 0,
                'dependency_files_count': len(fetch_result.dependency_files),
                'source_code_analysis': len(fetch_result.source_files) > 0,
                'source_files_count': len(fetch_result.source_files),
                'config_analysis': len(fetch_result.config_files) > 0,
                'config_files_count': len(fetch_result.config_files),
            }
            
            by_severity = result.get_by_severity()
            logger.info(
                f"Scan complete. Found {len(all_vulnerabilities)} vulnerabilities "
                f"({len(by_severity['critical'])} critical, "
                f"{len(by_severity['high'])} high, "
                f"{len(by_severity['medium'])} medium, "
                f"{len(by_severity['low'])} low)"
            )
            
        except GitHubFetcherError as e:
            logger.error(f"GitHub fetch error: {str(e)}")
            result.error = str(e)
        except Exception as e:
            logger.exception(f"Scan failed: {str(e)}")
            result.error = f"Scan failed: {str(e)}"
        
        result.complete_scan()
        return result
    
    def _build_scan_summary(self, fetch_result: FetchResult) -> str:
        """Build a human-readable scan summary."""
        parts = []
        
        parts.append(f"Analyzed {len(fetch_result.files_scanned)} of {fetch_result.total_files_in_repo} files in the repository.")
        
        if fetch_result.dependency_files:
            deps = ", ".join(fetch_result.dependency_files[:5])
            if len(fetch_result.dependency_files) > 5:
                deps += f" (+{len(fetch_result.dependency_files) - 5} more)"
            parts.append(f"Dependency files: {deps}")
        else:
            parts.append("No dependency files (requirements.txt, package.json, etc.) found.")
        
        if fetch_result.config_files:
            configs = ", ".join([f.split('/')[-1] for f in fetch_result.config_files[:3]])
            if len(fetch_result.config_files) > 3:
                configs += f" (+{len(fetch_result.config_files) - 3} more)"
            parts.append(f"Config files: {configs}")
        
        parts.append(f"Source files: {len(fetch_result.source_files)} files analyzed")
        
        if fetch_result.has_more_files:
            remaining = fetch_result.total_files_in_repo - len(fetch_result.files_scanned)
            parts.append(f"Note: {remaining} additional files can be analyzed in the next scan.")
        
        return " | ".join(parts)
    
    def _run_scanners(self, files: Dict[str, str]) -> List[VulnerabilityResult]:
        """Run all configured scanners on the files."""
        all_results = []
        
        if self.parallel:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self._run_single_scanner, scanner, files): scanner
                    for scanner in self.scanners
                }
                
                for future in as_completed(futures):
                    scanner = futures[future]
                    try:
                        results = future.result()
                        all_results.extend(results)
                        logger.info(f"Scanner {scanner.name} found {len(results)} issues")
                    except Exception as e:
                        logger.warning(f"Scanner {scanner.name} failed: {str(e)}")
        else:
            for scanner in self.scanners:
                try:
                    results = self._run_single_scanner(scanner, files)
                    all_results.extend(results)
                    logger.info(f"Scanner {scanner.name} found {len(results)} issues")
                except Exception as e:
                    logger.warning(f"Scanner {scanner.name} failed: {str(e)}")
        
        return all_results
    
    def _run_single_scanner(
        self, 
        scanner: BaseScanner, 
        files: Dict[str, str]
    ) -> List[VulnerabilityResult]:
        """Run a single scanner."""
        try:
            scanner.pre_scan_hook(files)
            results = scanner.scan(files)
            results = scanner.post_scan_hook(results)
            return results
        except Exception as e:
            logger.error(f"Scanner {scanner.name} error: {str(e)}")
            return []
    
    def _filter_low_confidence(
        self, 
        vulnerabilities: List[VulnerabilityResult]
    ) -> List[VulnerabilityResult]:
        """Filter out low confidence findings (keep for CRITICAL severity)."""
        from security_scanner.core.severity import Confidence
        
        filtered = []
        for vuln in vulnerabilities:
            confidence = vuln.confidence
            if isinstance(confidence, str):
                confidence = Confidence(confidence)
            
            if confidence in [Confidence.HIGH, Confidence.MEDIUM]:
                filtered.append(vuln)
            elif vuln.severity == Severity.CRITICAL:
                filtered.append(vuln)
        
        return filtered
    
    def _deduplicate_vulnerabilities(
        self, 
        vulnerabilities: List[VulnerabilityResult]
    ) -> List[VulnerabilityResult]:
        """Remove duplicate vulnerabilities across scanners."""
        seen = set()
        unique = []
        
        for vuln in vulnerabilities:
            key = (
                vuln.title,
                vuln.file_path,
                vuln.line or 0,
                vuln.vulnerability_type
            )
            
            if key not in seen:
                seen.add(key)
                unique.append(vuln)
        
        return unique
    
    def scan_files(
        self, 
        files: Dict[str, str],
        repo_url: str = "local"
    ) -> ScanResult:
        """Scan a dictionary of files directly (without fetching from GitHub)."""
        result = ScanResult(
            repository_url=repo_url,
            scan_started_at=datetime.utcnow()
        )
        
        try:
            result.files_scanned = len(files)
            
            all_vulnerabilities = self._run_scanners(files)
            all_vulnerabilities = self._deduplicate_vulnerabilities(all_vulnerabilities)
            result.add_vulnerabilities(all_vulnerabilities)
            
        except Exception as e:
            logger.exception(f"Scan failed: {str(e)}")
            result.error = str(e)
        
        result.complete_scan()
        return result
    
    @classmethod
    def quick_scan(cls, repo_url: str) -> Dict:
        """Perform a quick security scan and return results as dict."""
        orchestrator = cls()
        result = orchestrator.scan_repository(repo_url)
        return result.to_dict()
