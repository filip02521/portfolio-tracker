"""
Backup Service for Portfolio Tracker Pro
Handles automated backups of user data and settings
"""
import os
import json
import gzip
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Data files to backup
BACKUP_DATA_FILES = [
    'transaction_history.json',
    'portfolio_history.json',
    'goals.json',
    'app_settings.json',
    'watchlist.json',
    'ai_recommendations_history.json'
]

# Sensitive files (user data - optional backup)
SENSITIVE_FILES = [
    'users.json'  # User accounts - may want to exclude for privacy
]

# Backup directory
BACKUP_DIR = "backups"


class BackupService:
    """Service for creating and managing backups"""
    
    def __init__(self, backup_dir: str = BACKUP_DIR, include_sensitive: bool = False):
        """
        Initialize backup service
        
        Args:
            backup_dir: Directory to store backups
            include_sensitive: Whether to include sensitive files (users.json)
        """
        self.backup_dir = Path(backup_dir)
        self.include_sensitive = include_sensitive
        self.backup_dir.mkdir(exist_ok=True)
        logger.info(f"BackupService initialized with backup_dir: {self.backup_dir}")
    
    def create_backup(self, description: str = None) -> Dict[str, Any]:
        """
        Create a backup of all data files
        
        Args:
            description: Optional description for the backup
            
        Returns:
            Dict with backup metadata
        """
        timestamp = datetime.now()
        backup_id = timestamp.strftime('%Y%m%d_%H%M%S')
        backup_filename = f"backup_{backup_id}.json.gz"
        backup_path = self.backup_dir / backup_filename
        
        backup_data = {
            'backup_id': backup_id,
            'timestamp': timestamp.isoformat(),
            'description': description,
            'version': '1.0',
            'files': {}
        }
        
        # Backup each data file
        backed_up_files = 0
        total_size = 0
        
        for filename in BACKUP_DATA_FILES:
            file_path = Path(filename)
            if file_path.exists():
                try:
                    # Try to read as JSON
                    with open(file_path, 'r', encoding='utf-8') as f:
                        try:
                            data = json.load(f)
                        except json.JSONDecodeError as json_err:
                            # If JSON is invalid, read as text and store as string
                            f.seek(0)
                            data = {'_raw_content': f.read(), '_json_error': str(json_err)}
                            logger.warning(f"{filename} has invalid JSON, backing up as raw content")
                    
                    backup_data['files'][filename] = {
                        'size': os.path.getsize(file_path),
                        'data': data
                    }
                    backed_up_files += 1
                    total_size += os.path.getsize(file_path)
                    logger.debug(f"Backed up {filename}")
                except Exception as e:
                    logger.error(f"Error backing up {filename}: {e}")
                    backup_data['files'][filename] = {
                        'error': str(e)
                    }
            else:
                logger.debug(f"File {filename} does not exist, skipping")
        
        # Backup sensitive files if requested
        if self.include_sensitive:
            for filename in SENSITIVE_FILES:
                file_path = Path(filename)
                if file_path.exists():
                    try:
                        with open(file_path, 'r') as f:
                            data = json.load(f)
                        
                        backup_data['files'][filename] = {
                            'size': os.path.getsize(file_path),
                            'data': data,
                            'sensitive': True
                        }
                        backed_up_files += 1
                        total_size += os.path.getsize(file_path)
                        logger.debug(f"Backed up sensitive file {filename}")
                    except Exception as e:
                        logger.error(f"Error backing up sensitive file {filename}: {e}")
        
        # Add metadata
        backup_data['metadata'] = {
            'files_count': backed_up_files,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2)
        }
        
        # Compress and save backup
        try:
            with gzip.open(backup_path, 'wt', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2)
            
            backup_size = os.path.getsize(backup_path)
            backup_data['backup_size_bytes'] = backup_size
            backup_data['backup_size_mb'] = round(backup_size / (1024 * 1024), 2)
            backup_data['compression_ratio'] = round(backup_size / total_size, 2) if total_size > 0 else 0
            
            logger.info(f"Backup created: {backup_filename} ({backup_data['metadata']['files_count']} files, {backup_data['backup_size_mb']} MB)")
            
            return {
                'success': True,
                'backup_id': backup_id,
                'backup_filename': backup_filename,
                'backup_path': str(backup_path),
                'timestamp': timestamp.isoformat(),
                'files_count': backed_up_files,
                'total_size_mb': backup_data['metadata']['total_size_mb'],
                'backup_size_mb': backup_data['backup_size_mb'],
                'compression_ratio': backup_data['compression_ratio']
            }
        except Exception as e:
            logger.error(f"Error creating backup file: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_backups(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        List all available backups
        
        Args:
            limit: Maximum number of backups to return
            
        Returns:
            List of backup metadata
        """
        backups = []
        
        if not self.backup_dir.exists():
            return backups
        
        # Find all backup files
        backup_files = sorted(self.backup_dir.glob('backup_*.json.gz'), reverse=True)
        
        for backup_file in backup_files[:limit]:
            try:
                # Read metadata without decompressing full file
                with gzip.open(backup_file, 'rt', encoding='utf-8') as f:
                    # Read first few lines to get metadata
                    content = f.read(5000)  # Read first 5KB which should contain metadata
                    data = json.loads(content)
                
                backups.append({
                    'backup_id': data.get('backup_id', 'unknown'),
                    'backup_filename': backup_file.name,
                    'backup_path': str(backup_file),
                    'timestamp': data.get('timestamp', ''),
                    'description': data.get('description'),
                    'files_count': data.get('metadata', {}).get('files_count', 0),
                    'backup_size_mb': data.get('backup_size_mb', 0),
                    'backup_size_bytes': data.get('backup_size_bytes', os.path.getsize(backup_file))
                })
            except Exception as e:
                logger.warning(f"Error reading backup metadata from {backup_file.name}: {e}")
                # Fallback: use file stats
                backups.append({
                    'backup_id': backup_file.stem.replace('backup_', ''),
                    'backup_filename': backup_file.name,
                    'backup_path': str(backup_file),
                    'timestamp': datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat(),
                    'description': None,
                    'files_count': 0,
                    'backup_size_mb': round(os.path.getsize(backup_file) / (1024 * 1024), 2),
                    'backup_size_bytes': os.path.getsize(backup_file)
                })
        
        return backups
    
    def restore_backup(self, backup_id: str, overwrite: bool = False) -> Dict[str, Any]:
        """
        Restore data from a backup
        
        Args:
            backup_id: ID of the backup to restore (format: YYYYMMDD_HHMMSS)
            overwrite: Whether to overwrite existing files
            
        Returns:
            Dict with restore status
        """
        backup_filename = f"backup_{backup_id}.json.gz"
        backup_path = self.backup_dir / backup_filename
        
        if not backup_path.exists():
            return {
                'success': False,
                'error': f'Backup {backup_id} not found'
            }
        
        try:
            # Load backup
            with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            restored_files = []
            skipped_files = []
            error_files = []
            
            # Restore each file
            for filename, file_data in backup_data.get('files', {}).items():
                if 'error' in file_data:
                    error_files.append({'filename': filename, 'error': file_data['error']})
                    continue
                
                file_path = Path(filename)
                
                # Check if file exists
                if file_path.exists() and not overwrite:
                    skipped_files.append(filename)
                    continue
                
                try:
                    # Restore file
                    data = file_data['data']
                    
                    # If it was stored as raw content due to JSON error, restore as-is
                    if isinstance(data, dict) and '_raw_content' in data:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(data['_raw_content'])
                    else:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(data, f, indent=2)
                    
                    restored_files.append(filename)
                    logger.info(f"Restored {filename}")
                except Exception as e:
                    logger.error(f"Error restoring {filename}: {e}")
                    error_files.append({'filename': filename, 'error': str(e)})
            
            return {
                'success': True,
                'backup_id': backup_id,
                'restored_files': restored_files,
                'skipped_files': skipped_files,
                'error_files': error_files,
                'restored_count': len(restored_files)
            }
        except Exception as e:
            logger.error(f"Error restoring backup {backup_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_backup(self, backup_id: str) -> Dict[str, Any]:
        """
        Delete a backup
        
        Args:
            backup_id: ID of the backup to delete
            
        Returns:
            Dict with delete status
        """
        backup_filename = f"backup_{backup_id}.json.gz"
        backup_path = self.backup_dir / backup_filename
        
        if not backup_path.exists():
            return {
                'success': False,
                'error': f'Backup {backup_id} not found'
            }
        
        try:
            backup_path.unlink()
            logger.info(f"Deleted backup {backup_id}")
            return {
                'success': True,
                'backup_id': backup_id
            }
        except Exception as e:
            logger.error(f"Error deleting backup {backup_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_old_backups(self, days: int = 30, keep_minimum: int = 5) -> Dict[str, Any]:
        """
        Delete backups older than specified days, but keep at least minimum number
        
        Args:
            days: Number of days to keep backups
            keep_minimum: Minimum number of backups to keep (regardless of age)
            
        Returns:
            Dict with cleanup status
        """
        if not self.backup_dir.exists():
            return {
                'success': True,
                'deleted_count': 0,
                'kept_count': 0
            }
        
        cutoff_date = datetime.now() - timedelta(days=days)
        backup_files = sorted(self.backup_dir.glob('backup_*.json.gz'), reverse=True)
        
        deleted_count = 0
        kept_count = 0
        
        for i, backup_file in enumerate(backup_files):
            file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
            
            # Always keep the most recent N backups
            if i < keep_minimum:
                kept_count += 1
                continue
            
            # Delete if older than cutoff
            if file_time < cutoff_date:
                try:
                    backup_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old backup {backup_file.name}")
                except Exception as e:
                    logger.error(f"Error deleting old backup {backup_file.name}: {e}")
            else:
                kept_count += 1
        
        return {
            'success': True,
            'deleted_count': deleted_count,
            'kept_count': kept_count,
            'cutoff_date': cutoff_date.isoformat()
        }
    
    def get_backup_info(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a backup
        
        Args:
            backup_id: ID of the backup
            
        Returns:
            Dict with backup details or None if not found
        """
        backup_filename = f"backup_{backup_id}.json.gz"
        backup_path = self.backup_dir / backup_filename
        
        if not backup_path.exists():
            return None
        
        try:
            with gzip.open(backup_path, 'rt', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            return {
                'backup_id': backup_data.get('backup_id'),
                'timestamp': backup_data.get('timestamp'),
                'description': backup_data.get('description'),
                'version': backup_data.get('version'),
                'files': list(backup_data.get('files', {}).keys()),
                'metadata': backup_data.get('metadata', {}),
                'backup_size_bytes': backup_data.get('backup_size_bytes', os.path.getsize(backup_path)),
                'backup_size_mb': backup_data.get('backup_size_mb', round(os.path.getsize(backup_path) / (1024 * 1024), 2))
            }
        except Exception as e:
            logger.error(f"Error reading backup info for {backup_id}: {e}")
            return None

