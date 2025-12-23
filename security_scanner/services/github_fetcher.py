"""
GitHub Repository Fetcher Service

Safely fetches repository content from GitHub API without cloning.
This approach is more secure and efficient than cloning.
"""
import os
import re
import base64
import logging
import requests
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """Represents a file in the repository."""
    path: str
    name: str
    size: int
    sha: str
    url: str
    type: str  # 'file' or 'dir'
    content: Optional[str] = None
    encoding: Optional[str] = None


@dataclass
class FetchResult:
    """Result of fetching repository files."""
    files: Dict[str, str] = field(default_factory=dict)
    all_files_in_repo: List[str] = field(default_factory=list)
    files_scanned: List[str] = field(default_factory=list)
    files_skipped: List[str] = field(default_factory=list)
    dependency_files: List[str] = field(default_factory=list)
    source_files: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    has_more_files: bool = False
    total_files_in_repo: int = 0
    next_chunk_start: int = 0


class GitHubFetcherError(Exception):
    """Custom exception for GitHub fetcher errors."""
    pass


class GitHubFetcher:
    """
    Fetches repository content from GitHub API in a safe, sandboxed manner.
    
    Uses GitHub REST API to:
    - Validate repository existence and accessibility
    - Fetch repository tree structure
    - Retrieve file contents without cloning
    
    Features:
    - Chunk-based fetching for large repositories
    - Priority fetching for dependency and config files
    - Comprehensive file tracking
    """
    
    BASE_URL = "https://api.github.com"
    MAX_FILE_SIZE = 1024 * 1024  # 1MB max file size
    DEFAULT_CHUNK_SIZE = 100  # Files per chunk
    MAX_FILES_TO_SCAN = 500  # Maximum total files
    
    # PRIORITY 1: Dependency files (ALWAYS scan these first)
    DEPENDENCY_FILE_PATTERNS = [
        r'^requirements\.txt$',
        r'^requirements[-_].*\.txt$',
        r'^dev[-_]?requirements\.txt$',
        r'^test[-_]?requirements\.txt$',
        r'^Pipfile$',
        r'^Pipfile\.lock$',
        r'^pyproject\.toml$',
        r'^poetry\.lock$',
        r'^setup\.py$',
        r'^setup\.cfg$',
        r'^package\.json$',
        r'^package-lock\.json$',
        r'^yarn\.lock$',
        r'^pnpm-lock\.yaml$',
        r'^pom\.xml$',
        r'^build\.gradle$',
        r'^build\.gradle\.kts$',
        r'^go\.mod$',
        r'^go\.sum$',
        r'^Cargo\.toml$',
        r'^Cargo\.lock$',
        r'^Gemfile$',
        r'^Gemfile\.lock$',
        r'^composer\.json$',
        r'^composer\.lock$',
        r'^mix\.exs$',
        r'^pubspec\.yaml$',
        r'^\.csproj$',
        r'^packages\.config$',
    ]
    
    # PRIORITY 2: Configuration files
    CONFIG_FILE_PATTERNS = [
        r'^\.env$',
        r'^\.env\..*$',
        r'^\.env\.local$',
        r'^\.env\.production$',
        r'^\.env\.example$',
        r'^\.gitignore$',
        r'^Dockerfile$',
        r'^Dockerfile\..*$',
        r'^docker-compose\.ya?ml$',
        r'^docker-compose\..*\.ya?ml$',
        r'^\.dockerignore$',
        r'.*kubernetes.*\.ya?ml$',
        r'.*k8s.*\.ya?ml$',
        r'^\.github/workflows/.*\.ya?ml$',
        r'^\.gitlab-ci\.ya?ml$',
        r'^Jenkinsfile$',
        r'^\.travis\.ya?ml$',
        r'^\.circleci/.*$',
        r'^nginx\.conf$',
        r'^apache\.conf$',
        r'^\.htaccess$',
        r'.*settings\.py$',
        r'.*config\.py$',
        r'.*config\.js$',
        r'.*config\.ts$',
        r'^\.eslintrc.*$',
        r'^webpack\.config\..*$',
        r'^vite\.config\..*$',
        r'^next\.config\..*$',
        r'^tsconfig\.json$',
        r'^\.babelrc$',
        r'^jest\.config\..*$',
    ]
    
    # PRIORITY 3: Source code files
    SOURCE_FILE_PATTERNS = [
        r'.*\.py$',
        r'.*\.js$',
        r'.*\.ts$',
        r'.*\.jsx$',
        r'.*\.tsx$',
        r'.*\.java$',
        r'.*\.go$',
        r'.*\.rb$',
        r'.*\.php$',
        r'.*\.cs$',
        r'.*\.rs$',
        r'.*\.c$',
        r'.*\.cpp$',
        r'.*\.h$',
        r'.*\.hpp$',
        r'.*\.swift$',
        r'.*\.kt$',
        r'.*\.scala$',
        r'.*\.vue$',
        r'.*\.svelte$',
        r'.*\.sql$',
        r'.*\.sh$',
        r'.*\.bash$',
        r'.*\.zsh$',
        r'.*\.ps1$',
    ]
    
    # Files/directories to ALWAYS skip
    SKIP_PATTERNS = [
        r'^node_modules/',
        r'^vendor/',
        r'^\.git/',
        r'^dist/',
        r'^build/',
        r'^__pycache__/',
        r'.*\.min\.js$',
        r'.*\.min\.css$',
        r'.*\.map$',
        r'^\.next/',
        r'^\.nuxt/',
        r'^coverage/',
        r'^\.pytest_cache/',
        r'^\.mypy_cache/',
        r'^venv/',
        r'^env/',
        r'^\.venv/',
        r'^virtualenv/',
        r'.*\.pyc$',
        r'.*\.pyo$',
        r'.*\.class$',
        r'.*\.o$',
        r'.*\.so$',
        r'.*\.dll$',
        r'.*\.exe$',
        r'.*\.bin$',
        r'.*\.(png|jpg|jpeg|gif|svg|ico|webp)$',
        r'.*\.(woff|woff2|ttf|eot|otf)$',
        r'.*\.(mp4|mp3|wav|avi|mov|webm)$',
        r'.*\.(pdf|doc|docx|xls|xlsx|ppt)$',
        r'.*\.(zip|tar|gz|rar|7z)$',
        r'^static/',
        r'^public/assets/',
        r'^test_data/',
        r'^fixtures/',
        r'.*\.spec\..*$',
        r'.*\.test\..*$',
        r'.*_test\..*$',
    ]
    
    def __init__(self):
        """Initialize the GitHub fetcher."""
        self.token = os.environ.get('GITHUB_PAT')
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'SecurityScanner/1.0'
        }
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'
            logger.info("GitHub PAT found and configured")
        else:
            logger.warning("No GITHUB_PAT found - API rate limits will apply")
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def parse_repo_url(self, url: str) -> Tuple[str, str]:
        """Parse GitHub repository URL to extract owner and repo name."""
        patterns = [
            r'github\.com[/:]([^/]+)/([^/\.]+?)(?:\.git)?/?$',
            r'github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/.*)?$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2).rstrip('/')
        
        raise GitHubFetcherError(f"Invalid GitHub URL: {url}")
    
    def validate_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """Validate that repository exists and is accessible."""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}",
                timeout=10
            )
            
            if response.status_code == 404:
                raise GitHubFetcherError(
                    f"Repository not found: {owner}/{repo}. "
                    "Make sure the repository exists and is public."
                )
            elif response.status_code == 403:
                error_msg = response.json().get('message', '')
                if 'rate limit' in error_msg.lower():
                    raise GitHubFetcherError(
                        "GitHub API rate limit exceeded. "
                        "Please add a GITHUB_PAT environment variable or try again later."
                    )
                raise GitHubFetcherError(
                    "Repository access denied. Make sure the repository is public."
                )
            elif response.status_code != 200:
                raise GitHubFetcherError(
                    f"Failed to access repository: HTTP {response.status_code}"
                )
            
            return response.json()
            
        except requests.exceptions.Timeout:
            raise GitHubFetcherError("Request timed out. GitHub may be slow or unavailable.")
        except requests.exceptions.RequestException as e:
            raise GitHubFetcherError(f"Network error: {str(e)}")
    
    def get_repository_tree(
        self, 
        owner: str, 
        repo: str, 
        branch: str = "main"
    ) -> List[FileInfo]:
        """Get the complete file tree of a repository."""
        try:
            # Try specified branch first
            response = self.session.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
                timeout=30
            )
            
            if response.status_code == 404:
                # Try 'master' branch
                response = self.session.get(
                    f"{self.BASE_URL}/repos/{owner}/{repo}/git/trees/master?recursive=1",
                    timeout=30
                )
            
            if response.status_code == 404:
                # Try 'develop' branch
                response = self.session.get(
                    f"{self.BASE_URL}/repos/{owner}/{repo}/git/trees/develop?recursive=1",
                    timeout=30
                )
            
            if response.status_code != 200:
                raise GitHubFetcherError(
                    f"Failed to fetch repository tree: HTTP {response.status_code}"
                )
            
            data = response.json()
            files = []
            
            for item in data.get('tree', []):
                if item['type'] == 'blob':  # Only files, not directories
                    files.append(FileInfo(
                        path=item['path'],
                        name=os.path.basename(item['path']),
                        size=item.get('size', 0),
                        sha=item['sha'],
                        url=item['url'],
                        type='file'
                    ))
            
            logger.info(f"Found {len(files)} total files in repository")
            return files
            
        except requests.exceptions.RequestException as e:
            raise GitHubFetcherError(f"Failed to fetch repository tree: {str(e)}")
    
    def _categorize_file(self, file_path: str) -> Optional[str]:
        """
        Categorize a file into dependency, config, source, or None (skip).
        
        Returns: 'dependency', 'config', 'source', or None
        """
        # Check skip patterns first
        for pattern in self.SKIP_PATTERNS:
            if re.search(pattern, file_path, re.IGNORECASE):
                return None
        
        # Check dependency files (highest priority)
        file_name = os.path.basename(file_path)
        for pattern in self.DEPENDENCY_FILE_PATTERNS:
            if re.search(pattern, file_name, re.IGNORECASE):
                return 'dependency'
        
        # Check config files
        for pattern in self.CONFIG_FILE_PATTERNS:
            if re.search(pattern, file_path, re.IGNORECASE):
                return 'config'
        
        # Check source files
        for pattern in self.SOURCE_FILE_PATTERNS:
            if re.search(pattern, file_path, re.IGNORECASE):
                return 'source'
        
        return None
    
    def get_file_content(
        self, 
        owner: str, 
        repo: str, 
        file_path: str
    ) -> Optional[str]:
        """Fetch content of a specific file."""
        try:
            response = self.session.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{file_path}",
                timeout=15
            )
            
            if response.status_code != 200:
                logger.debug(f"Failed to fetch file {file_path}: HTTP {response.status_code}")
                return None
            
            data = response.json()
            
            # Check file size
            if data.get('size', 0) > self.MAX_FILE_SIZE:
                logger.debug(f"File too large, skipping: {file_path}")
                return None
            
            # Decode content
            if data.get('encoding') == 'base64':
                try:
                    content = base64.b64decode(data['content']).decode('utf-8')
                    return content
                except (UnicodeDecodeError, base64.binascii.Error):
                    logger.debug(f"Failed to decode file: {file_path}")
                    return None
            
            return data.get('content')
            
        except requests.exceptions.RequestException as e:
            logger.debug(f"Error fetching file {file_path}: {str(e)}")
            return None
    
    def fetch_repository_files(
        self, 
        repo_url: str,
        max_files: Optional[int] = None,
        chunk_start: int = 0,
        chunk_size: Optional[int] = None
    ) -> FetchResult:
        """
        Fetch files from a repository with prioritization and chunking.
        
        Priority order:
        1. Dependency files (requirements.txt, package.json, etc.)
        2. Configuration files (.env, Dockerfile, etc.)
        3. Source code files (.py, .js, etc.)
        
        Args:
            repo_url: GitHub repository URL
            max_files: Maximum total files to fetch
            chunk_start: Starting index for chunked fetching
            chunk_size: Number of files per chunk
            
        Returns:
            FetchResult with categorized files and metadata
        """
        owner, repo = self.parse_repo_url(repo_url)
        
        # Validate repository
        repo_info = self.validate_repository(owner, repo)
        default_branch = repo_info.get('default_branch', 'main')
        
        # Get file tree
        all_files = self.get_repository_tree(owner, repo, default_branch)
        
        # Categorize all files
        dependency_files = []
        config_files = []
        source_files = []
        skipped_files = []
        
        for f in all_files:
            category = self._categorize_file(f.path)
            if category == 'dependency':
                dependency_files.append(f)
            elif category == 'config':
                config_files.append(f)
            elif category == 'source':
                source_files.append(f)
            else:
                skipped_files.append(f.path)
        
        logger.info(f"Categorized files - Dependency: {len(dependency_files)}, "
                   f"Config: {len(config_files)}, Source: {len(source_files)}, "
                   f"Skipped: {len(skipped_files)}")
        
        # Build prioritized file list:
        # 1. ALL dependency files first
        # 2. ALL config files
        # 3. Source files (up to limit)
        files_to_scan = []
        files_to_scan.extend(dependency_files)
        files_to_scan.extend(config_files)
        files_to_scan.extend(source_files)
        
        # Apply chunking
        total_files = len(files_to_scan)
        limit = max_files or self.MAX_FILES_TO_SCAN
        actual_chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
        
        # Ensure we always include ALL dependency and config files
        min_required = len(dependency_files) + len(config_files)
        actual_limit = max(limit, min_required)
        
        # Apply chunk window
        chunk_end = min(chunk_start + actual_limit, total_files)
        files_in_chunk = files_to_scan[chunk_start:chunk_end]
        
        has_more = chunk_end < total_files
        
        logger.info(f"Fetching {len(files_in_chunk)} files (chunk {chunk_start}-{chunk_end} of {total_files})")
        
        # Fetch file contents in parallel
        file_contents = {}
        
        def fetch_file(file_info: FileInfo) -> Tuple[str, Optional[str]]:
            content = self.get_file_content(owner, repo, file_info.path)
            return file_info.path, content
        
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = {
                executor.submit(fetch_file, f): f 
                for f in files_in_chunk
            }
            
            for future in as_completed(futures):
                try:
                    path, content = future.result()
                    if content:
                        file_contents[path] = content
                except Exception as e:
                    logger.debug(f"Error fetching file: {str(e)}")
        
        # Build result
        result = FetchResult(
            files=file_contents,
            all_files_in_repo=[f.path for f in all_files],
            files_scanned=list(file_contents.keys()),
            files_skipped=skipped_files,
            dependency_files=[f.path for f in dependency_files],
            source_files=[f.path for f in source_files if f.path in file_contents],
            config_files=[f.path for f in config_files if f.path in file_contents],
            has_more_files=has_more,
            total_files_in_repo=len(all_files),
            next_chunk_start=chunk_end if has_more else 0
        )
        
        logger.info(f"Successfully fetched {len(file_contents)} files")
        return result
    
    def get_repository_info(self, repo_url: str) -> Dict[str, Any]:
        """Get repository metadata."""
        owner, repo = self.parse_repo_url(repo_url)
        return self.validate_repository(owner, repo)
