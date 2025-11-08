"""
File system operations manager for Parallax Editor web interface.

Provides secure file reading, writing, and directory tree traversal
within a scoped directory to prevent path traversal attacks.
"""

from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger("parallizer.file_manager")


@dataclass
class FileNode:
    """Represents a file or directory node in the tree"""
    name: str
    path: str
    type: str  # "file" or "directory"
    children: Optional[List['FileNode']] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        result = {
            'name': self.name,
            'path': self.path,
            'type': self.type,
        }
        if self.children is not None:
            result['children'] = [child.to_dict() for child in self.children]
        return result


class PathValidator:
    """Validate paths to prevent directory traversal attacks"""

    @staticmethod
    def validate_path(requested_path: str, scope_root: str) -> Path:
        """
        Validates that requested_path is within scope_root.

        Args:
            requested_path: Path requested by the client
            scope_root: Root directory to constrain operations within

        Returns:
            Resolved absolute Path object if valid

        Raises:
            ValueError: If path escape attempt detected or path invalid
        """
        try:
            scope = Path(scope_root).expanduser().resolve()
            requested = Path(requested_path).expanduser().resolve()

            # Check if requested path is within scope
            requested.relative_to(scope)

            return requested

        except ValueError as e:
            logger.warning(f"Path escape attempt: {requested_path} outside {scope_root}")
            raise ValueError(f"Path must be within scope root: {requested_path}")
        except Exception as e:
            logger.error(f"Path validation error: {e}")
            raise ValueError(f"Invalid path: {requested_path}")


class FileSystemManager:
    """Manage file operations within a scoped directory"""

    # Files and directories to skip in tree traversal
    SKIP_PATTERNS = {
        '__pycache__', 'node_modules', '.git', 'dist', 'build',
        '.next', '.venv', 'venv', '.pytest_cache', '.mypy_cache',
        'coverage', '.coverage', 'htmlcov', '.tox', '.eggs',
        '*.egg-info', '.DS_Store', 'Thumbs.db'
    }

    # File extensions to language mapping
    LANGUAGE_MAP = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.jsx': 'javascript',
        '.json': 'json',
        '.md': 'markdown',
        '.yml': 'yaml',
        '.yaml': 'yaml',
        '.toml': 'toml',
        '.xml': 'xml',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sh': 'shell',
        '.bash': 'shell',
        '.zsh': 'shell',
        '.sql': 'sql',
        '.go': 'go',
        '.rs': 'rust',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
        '.txt': 'plaintext',
        '.log': 'plaintext',
    }

    def __init__(self, scope_root: str):
        """
        Initialize file system manager.

        Args:
            scope_root: Root directory for all file operations

        Raises:
            ValueError: If scope_root doesn't exist
        """
        self.scope_root = Path(scope_root).expanduser().resolve()

        if not self.scope_root.exists():
            raise ValueError(f"Scope root does not exist: {scope_root}")

        if not self.scope_root.is_dir():
            raise ValueError(f"Scope root is not a directory: {scope_root}")

        logger.info(f"FileSystemManager initialized with scope: {self.scope_root}")

    def get_tree(self, max_depth: int = 10) -> FileNode:
        """
        Get directory tree structure.

        Args:
            max_depth: Maximum depth to traverse (prevents deep recursion)

        Returns:
            FileNode representing the tree structure
        """
        logger.info(f"Building file tree for {self.scope_root} (max_depth={max_depth})")
        return self._walk_directory(self.scope_root, 0, max_depth)

    def _should_skip(self, path: Path) -> bool:
        """Check if file/directory should be skipped"""
        # Skip hidden files/directories
        if path.name.startswith('.'):
            return True

        # Skip common build artifacts and dependencies
        if path.name in self.SKIP_PATTERNS:
            return True

        return False

    def _walk_directory(self, path: Path, depth: int, max_depth: int) -> FileNode:
        """
        Recursively walk directory structure.

        Args:
            path: Current path to process
            depth: Current recursion depth
            max_depth: Maximum depth to traverse

        Returns:
            FileNode for this path
        """
        node = FileNode(
            name=path.name or path.as_posix(),
            path=str(path),
            type="directory" if path.is_dir() else "file"
        )

        if path.is_dir() and depth < max_depth:
            try:
                children = []

                # Get all items, sort directories first, then alphabetically
                items = sorted(
                    path.iterdir(),
                    key=lambda p: (not p.is_dir(), p.name.lower())
                )

                for item in items:
                    if self._should_skip(item):
                        continue

                    child = self._walk_directory(item, depth + 1, max_depth)
                    children.append(child)

                node.children = children if children else None

            except PermissionError:
                logger.warning(f"Permission denied accessing {path}")
                node.children = None
            except Exception as e:
                logger.error(f"Error reading directory {path}: {e}")
                node.children = None

        return node

    def read_file(self, file_path: str) -> tuple[str, str]:
        """
        Read file content.

        Args:
            file_path: Path to file (will be validated against scope)

        Returns:
            Tuple of (content, language)

        Raises:
            ValueError: If path is invalid or not a file
        """
        safe_path = PathValidator.validate_path(file_path, str(self.scope_root))

        if not safe_path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        logger.info(f"Reading file: {safe_path}")

        # Try to read content with different encodings
        try:
            content = safe_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            logger.warning(f"UTF-8 decode failed for {safe_path}, trying latin-1")
            try:
                content = safe_path.read_text(encoding='latin-1')
            except Exception as e:
                raise ValueError(f"Cannot decode file: {e}")
        except Exception as e:
            raise ValueError(f"Cannot read file: {e}")

        # Detect language
        language = self._detect_language(safe_path.name)

        logger.info(f"Read {len(content)} bytes from {safe_path} (language: {language})")

        return content, language

    def write_file(self, file_path: str, content: str) -> bool:
        """
        Write content to file.

        Args:
            file_path: Path to file (will be validated against scope)
            content: Content to write

        Returns:
            True if successful

        Raises:
            ValueError: If path is invalid
        """
        safe_path = PathValidator.validate_path(file_path, str(self.scope_root))

        logger.info(f"Writing {len(content)} bytes to {safe_path}")

        try:
            # Create parent directories if they don't exist
            safe_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            safe_path.write_text(content, encoding='utf-8')

            logger.info(f"Successfully wrote to {safe_path}")
            return True

        except PermissionError:
            raise ValueError(f"Permission denied writing to {file_path}")
        except Exception as e:
            logger.error(f"Error writing file {safe_path}: {e}")
            raise ValueError(f"Cannot write file: {e}")

    def _detect_language(self, filename: str) -> str:
        """
        Detect programming language from file extension.

        Args:
            filename: Name of the file

        Returns:
            Language identifier (e.g., 'python', 'javascript')
        """
        ext = Path(filename).suffix.lower()
        return self.LANGUAGE_MAP.get(ext, 'plaintext')
