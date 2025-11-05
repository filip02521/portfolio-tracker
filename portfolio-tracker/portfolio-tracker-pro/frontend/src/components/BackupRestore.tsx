import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  Chip,
} from '@mui/material';
import {
  Backup,
  Restore,
  Delete,
  Refresh,
  CloudDownload,
  CloudUpload,
  Info,
} from '@mui/icons-material';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

interface Backup {
  backup_id: string;
  backup_filename: string;
  timestamp: string;
  description?: string;
  files_count: number;
  backup_size_mb: number;
  backup_size_bytes: number;
}

interface BackupRestoreProps {
  onBackupCreated?: () => void;
  onRestoreComplete?: () => void;
}

const BackupRestore: React.FC<BackupRestoreProps> = ({ onBackupCreated, onRestoreComplete }) => {
  const [backups, setBackups] = useState<Backup[]>([]);
  const [loading, setLoading] = useState(false);
  const [creatingBackup, setCreatingBackup] = useState(false);
  const [restoreDialog, setRestoreDialog] = useState<{ open: boolean; backupId: string | null }>({
    open: false,
    backupId: null,
  });
  const [deleteDialog, setDeleteDialog] = useState<{ open: boolean; backupId: string | null }>({
    open: false,
    backupId: null,
  });
  const [alert, setAlert] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [restoring, setRestoring] = useState(false);
  const [description, setDescription] = useState('');

  const getAuthToken = () => {
    return localStorage.getItem('authToken');
  };

  const fetchBackups = async () => {
    try {
      setLoading(true);
      const token = getAuthToken();
      const response = await axios.get(`${API_BASE_URL}/backup/list`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      setBackups(response.data);
    } catch (error: any) {
      console.error('Error fetching backups:', error);
      setAlert({
        type: 'error',
        message: error.response?.data?.detail || 'Failed to fetch backups',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBackups();
  }, []);

  const handleCreateBackup = async () => {
    try {
      setCreatingBackup(true);
      setAlert(null);
      const token = getAuthToken();
      const response = await axios.post(
        `${API_BASE_URL}/backup/create`,
        {
          description: description || undefined,
          include_sensitive: false,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setAlert({
        type: 'success',
        message: `Backup created successfully: ${response.data.backup_id}`,
      });
      setDescription('');
      await fetchBackups();
      if (onBackupCreated) {
        onBackupCreated();
      }
    } catch (error: any) {
      console.error('Error creating backup:', error);
      setAlert({
        type: 'error',
        message: error.response?.data?.detail || 'Failed to create backup',
      });
    } finally {
      setCreatingBackup(false);
    }
  };

  const handleRestore = async (backupId: string, overwrite: boolean = false) => {
    try {
      setRestoring(true);
      setAlert(null);
      const token = getAuthToken();
      const response = await axios.post(
        `${API_BASE_URL}/backup/restore`,
        {
          backup_id: backupId,
          overwrite,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setAlert({
        type: 'success',
        message: `Backup restored successfully. ${response.data.restored_count} file(s) restored.`,
      });
      setRestoreDialog({ open: false, backupId: null });
      if (onRestoreComplete) {
        onRestoreComplete();
      }
    } catch (error: any) {
      console.error('Error restoring backup:', error);
      setAlert({
        type: 'error',
        message: error.response?.data?.detail || 'Failed to restore backup',
      });
    } finally {
      setRestoring(false);
    }
  };

  const handleDelete = async (backupId: string) => {
    try {
      setLoading(true);
      setAlert(null);
      const token = getAuthToken();
      await axios.delete(`${API_BASE_URL}/backup/delete/${backupId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      setAlert({
        type: 'success',
        message: 'Backup deleted successfully',
      });
      setDeleteDialog({ open: false, backupId: null });
      await fetchBackups();
    } catch (error: any) {
      console.error('Error deleting backup:', error);
      setAlert({
        type: 'error',
        message: error.response?.data?.detail || 'Failed to delete backup',
      });
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString();
    } catch {
      return timestamp;
    }
  };

  const formatSize = (mb: number) => {
    if (mb < 1) {
      return `${(mb * 1024).toFixed(2)} KB`;
    }
    return `${mb.toFixed(2)} MB`;
  };

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h5" component="h2">
            Backup & Restore
          </Typography>
          <Box>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={fetchBackups}
              disabled={loading}
              sx={{ mr: 1 }}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<Backup />}
              onClick={handleCreateBackup}
              disabled={creatingBackup}
            >
              {creatingBackup ? <CircularProgress size={20} /> : 'Create Backup'}
            </Button>
          </Box>
        </Box>

        {alert && (
          <Alert
            severity={alert.type}
            onClose={() => setAlert(null)}
            sx={{ mb: 2 }}
          >
            {alert.message}
          </Alert>
        )}

        <Box mb={2}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Create a backup of your portfolio data, transactions, goals, and settings.
            Backups are automatically created daily at 2:00 AM.
          </Typography>
        </Box>

        {loading && backups.length === 0 ? (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        ) : backups.length === 0 ? (
          <Box textAlign="center" p={3}>
            <Typography variant="body2" color="text.secondary">
              No backups available. Create your first backup to get started.
            </Typography>
          </Box>
        ) : (
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Backup ID</TableCell>
                  <TableCell>Date</TableCell>
                  <TableCell>Description</TableCell>
                  <TableCell>Files</TableCell>
                  <TableCell>Size</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {backups.map((backup) => (
                  <TableRow key={backup.backup_id}>
                    <TableCell>
                      <Typography variant="body2" fontFamily="monospace">
                        {backup.backup_id}
                      </Typography>
                    </TableCell>
                    <TableCell>{formatDate(backup.timestamp)}</TableCell>
                    <TableCell>
                      {backup.description || (
                        <Typography variant="body2" color="text.secondary" fontStyle="italic">
                          No description
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip label={backup.files_count} size="small" />
                    </TableCell>
                    <TableCell>{formatSize(backup.backup_size_mb)}</TableCell>
                    <TableCell align="right">
                      <Tooltip title="Restore from this backup">
                        <IconButton
                          size="small"
                          onClick={() => setRestoreDialog({ open: true, backupId: backup.backup_id })}
                          color="primary"
                        >
                          <Restore />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete backup">
                        <IconButton
                          size="small"
                          onClick={() => setDeleteDialog({ open: true, backupId: backup.backup_id })}
                          color="error"
                        >
                          <Delete />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </CardContent>

      {/* Restore Dialog */}
      <Dialog
        open={restoreDialog.open}
        onClose={() => setRestoreDialog({ open: false, backupId: null })}
      >
        <DialogTitle>Restore Backup</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to restore from backup {restoreDialog.backupId}?
            This will overwrite your current data. This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRestoreDialog({ open: false, backupId: null })}>
            Cancel
          </Button>
          <Button
            onClick={() => restoreDialog.backupId && handleRestore(restoreDialog.backupId, true)}
            color="primary"
            variant="contained"
            disabled={restoring}
          >
            {restoring ? <CircularProgress size={20} /> : 'Restore'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Dialog */}
      <Dialog
        open={deleteDialog.open}
        onClose={() => setDeleteDialog({ open: false, backupId: null })}
      >
        <DialogTitle>Delete Backup</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete backup {deleteDialog.backupId}?
            This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialog({ open: false, backupId: null })}>
            Cancel
          </Button>
          <Button
            onClick={() => deleteDialog.backupId && handleDelete(deleteDialog.backupId)}
            color="error"
            variant="contained"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Card>
  );
};

export default BackupRestore;

