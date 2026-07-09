import os
import shutil
from typing import List, Optional
from utils.logger import logger

class FileManager:
    @staticmethod
    def ensure_dir(path: str) -> str:
        """Ensures that a directory exists; creates it if it doesn't."""
        os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def exists(path: str) -> bool:
        """Checks if a file or directory exists."""
        return os.path.exists(path)

    @staticmethod
    def list_files(directory: str, extensions: Optional[List[str]] = None, recursive: bool = False) -> List[str]:
        """
        Lists files in a directory, optionally filtering by extensions (e.g. ['.jpg', '.png']).
        """
        if not os.path.exists(directory):
            logger.warning(f"Directory not found for listing: {directory}")
            return []

        matched_files = []
        
        # Lowercase extensions for robust matching
        exts = [e.lower() for e in extensions] if extensions else None

        if recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if exts is None or ext in exts:
                        matched_files.append(os.path.normpath(os.path.join(root, file)))
        else:
            for item in os.listdir(directory):
                full_path = os.path.join(directory, item)
                if os.path.isfile(full_path):
                    ext = os.path.splitext(item)[1].lower()
                    if exts is None or ext in exts:
                        matched_files.append(os.path.normpath(full_path))
                        
        return matched_files

    @staticmethod
    def get_file_size_formatted(path: str) -> str:
        """Returns file size as a human-readable string (e.g. 1.25 MB)."""
        if not os.path.isfile(path):
            return "0 Bytes"
        size_bytes = os.path.getsize(path)
        for unit in ["Bytes", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    @staticmethod
    def delete_file(path: str) -> bool:
        """Safely deletes a file."""
        try:
            if os.path.isfile(path):
                os.remove(path)
                logger.debug(f"Deleted file: {path}")
                return True
        except Exception as e:
            logger.error(f"Error deleting file {path}: {e}")
        return False

    @staticmethod
    def clean_dir(directory: str):
        """Cleans all files and subdirectories from the given directory without removing the directory itself."""
        if not os.path.exists(directory):
            return
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logger.error(f"Failed to delete {file_path}. Reason: {e}")
