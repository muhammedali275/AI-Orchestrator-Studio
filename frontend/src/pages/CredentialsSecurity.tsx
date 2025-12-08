import React, { useState, useEffect } from 'react';
import {
  Typography,
  Paper,
  Box,
  Button,
  TextField,
  Grid,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  InputAdornment,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Security as SecurityIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  VpnKey as VpnKeyIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface Credential {
  id: string;
  name: string;
  type: string;
  username?: string;
  extra: Record<string, any>;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

const CREDENTIAL_TYPES = [
  { value: 'ssh', label: 'SSH Key' },
  { value: 'http_basic', label: 'HTTP Basic Auth' },
  { value: 'bearer_token', label: 'Bearer Token' },
  { value: 'db_dsn', label: 'Database DSN' },
  { value: 'api_key', label: 'API Key' },
  { value: 'https_cert', label: 'HTTPS Certificate' },
  { value: 'ip_allowlist', label: 'IP Allowlist' },
  { value: 'token', label: 'Authentication Token' },
  { value: 'custom', label: 'Custom' },
];

const CredentialsSecurity: React.FC = () => {
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [editingCredential, setEditingCredential] = useState<Credential | null>(null);
  const [showSecret, setShowSecret] = useState(false);
  const [testingCredential, setTestingCredential] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    name: '',
    type: 'api_key',
    username: '',
    secret: '',
    extra: {} as Record<string, any>,
  });

  useEffect(() => {
    fetchCredentials();
  }, []);

  const fetchCredentials = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/api/credentials');
      setCredentials(response.data.credentials || []);
    } catch (error) {
      console.error('Error fetching credentials:', error);
      setMessage('Error loading credentials');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (credential?: Credential) => {
    if (credential) {
      setEditingCredential(credential);
      setFormData({
        name: credential.name,
        type: credential.type,
        username: credential.username || '',
        secret: '', // Never populate secret for security
        extra: credential.extra || {},
      });
    } else {
      setEditingCredential(null);
      setFormData({
        name: '',
        type: 'api_key',
        username: '',
        secret: '',
        extra: {},
      });
    }
    setOpenDialog(true);
    setShowSecret(false);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingCredential(null);
    setShowSecret(false);
  };

  const handleSaveCredential = async () => {
    try {
      if (editingCredential) {
        // Only send secret if it's been changed
        const updateData: any = {
          name: formData.name,
          username: formData.username,
          extra: formData.extra,
        };
        if (formData.secret) {
          updateData.secret = formData.secret;
        }
        await axios.put(`http://localhost:8000/api/credentials/${editingCredential.id}`, updateData);
        setMessage('Credential updated successfully!');
      } else {
        await axios.post('http://localhost:8000/api/credentials', formData);
        setMessage('Credential created successfully!');
      }
      fetchCredentials();
      handleCloseDialog();
      setTimeout(() => setMessage(''), 3000);
    } catch (error: any) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleDeleteCredential = async (id: string, name: string) => {
    if (!window.confirm(`Are you sure you want to delete credential "${name}"?`)) return;
    
    try {
      await axios.delete(`http://localhost:8000/api/credentials/${id}`);
      setMessage('Credential deleted successfully!');
      fetchCredentials();
      setTimeout(() => setMessage(''), 3000);
    } catch (error: any) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleTestCredential = async (id: string, name: string) => {
    setTestingCredential(id);
    try {
      const response = await axios.post(`http://localhost:8000/api/credentials/${id}/test`);
      if (response.data.success) {
        setMessage(`Credential "${name}" is valid and active!`);
      } else {
        setMessage(`Credential "${name}" test failed: ${response.data.message}`);
      }
      setTimeout(() => setMessage(''), 3000);
    } catch (error: any) {
      setMessage(`Error testing credential: ${error.response?.data?.detail || error.message}`);
    } finally {
      setTestingCredential(null);
    }
  };

  const getTypeLabel = (type: string) => {
    const typeObj = CREDENTIAL_TYPES.find(t => t.value === type);
    return typeObj ? typeObj.label : type;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <Box className="fade-in">
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography
            variant="h3"
            sx={{
              fontWeight: 700,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              mb: 1,
            }}
          >
            Credentials & Security
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage secure credentials for tools, databases, and services
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Tooltip title="Refresh Credentials">
            <IconButton
              onClick={fetchCredentials}
              disabled={loading}
              sx={{
                background: 'rgba(102, 126, 234, 0.1)',
                '&:hover': { background: 'rgba(102, 126, 234, 0.2)' },
              }}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
            sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
          >
            Add Credential
          </Button>
        </Box>
      </Box>

      {/* Security Warning */}
      <Alert severity="warning" icon={<WarningIcon />} sx={{ mb: 3 }}>
        <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
          Security Best Practices
        </Typography>
        <Typography variant="caption">
          • Secrets are encrypted before storage and never displayed in full
          <br />
          • Use strong, unique credentials for each service
          <br />
          • Rotate credentials regularly
          <br />
          • Never share credentials or commit them to version control
          <br />
          • Authentication tokens are disabled by default for local LLM connections
        </Typography>
      </Alert>

      {/* Credential Types Explanation */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
          Credential Types
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
              Required for Remote Services
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              These credentials are typically required when connecting to remote services:
            </Typography>
            <Box component="ul" sx={{ pl: 2, m: 0 }}>
              <Typography component="li" variant="body2" color="text.secondary">
                <strong>API Keys</strong> - For authenticating with most cloud services and APIs
              </Typography>
              <Typography component="li" variant="body2" color="text.secondary">
                <strong>Bearer Tokens</strong> - For OAuth and token-based authentication systems
              </Typography>
              <Typography component="li" variant="body2" color="text.secondary">
                <strong>Database DSN</strong> - Connection strings for database access
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
              Optional for Local Services
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              These credentials are optional when using local services (like Ollama):
            </Typography>
            <Box component="ul" sx={{ pl: 2, m: 0 }}>
              <Typography component="li" variant="body2" color="text.secondary">
                <strong>Authentication Tokens</strong> - Disabled by default for local LLMs
              </Typography>
              <Typography component="li" variant="body2" color="text.secondary">
                <strong>HTTPS Certificates</strong> - For secure local connections
              </Typography>
              <Typography component="li" variant="body2" color="text.secondary">
                <strong>IP Allowlists</strong> - For restricting access to specific IP addresses
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Messages */}
      {message && (
        <Alert
          severity={message.includes('Error') ? 'error' : 'success'}
          sx={{ mb: 3 }}
          onClose={() => setMessage('')}
        >
          {message}
        </Alert>
      )}

      {/* Credentials Table */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : credentials.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <VpnKeyIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No credentials configured
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Add your first credential to securely store authentication information
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
            sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
          >
            Add Credential
          </Button>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>Name</strong></TableCell>
                <TableCell><strong>Type</strong></TableCell>
                <TableCell><strong>Username</strong></TableCell>
                <TableCell><strong>Status</strong></TableCell>
                <TableCell><strong>Created</strong></TableCell>
                <TableCell><strong>Actions</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {credentials.map((credential) => (
                <TableRow key={credential.id} hover>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <SecurityIcon sx={{ color: '#667eea', fontSize: 20 }} />
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {credential.name}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={getTypeLabel(credential.type)}
                      size="small"
                      sx={{ background: 'rgba(102, 126, 234, 0.2)', color: '#667eea' }}
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary">
                      {credential.username || '—'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      icon={credential.is_active ? <CheckCircleIcon /> : <WarningIcon />}
                      label={credential.is_active ? 'Active' : 'Inactive'}
                      size="small"
                      color={credential.is_active ? 'success' : 'warning'}
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption" color="text.secondary">
                      {formatDate(credential.created_at)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Tooltip title="Test Credential">
                        <IconButton
                          size="small"
                          onClick={() => handleTestCredential(credential.id, credential.name)}
                          disabled={testingCredential === credential.id}
                        >
                          {testingCredential === credential.id ? (
                            <CircularProgress size={20} />
                          ) : (
                            <CheckCircleIcon fontSize="small" />
                          )}
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit">
                        <IconButton
                          size="small"
                          onClick={() => handleOpenDialog(credential)}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDeleteCredential(credential.id, credential.name)}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingCredential ? 'Edit Credential' : 'Add New Credential'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                label="Credential Name"
                fullWidth
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="my-api-credential"
                helperText="A descriptive name for this credential"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Credential Type</InputLabel>
                <Select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  label="Credential Type"
                >
                  {CREDENTIAL_TYPES.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      {type.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            {(formData.type === 'ssh' || formData.type === 'http_basic' || formData.type === 'db_dsn') && (
              <Grid item xs={12}>
                <TextField
                  label="Username"
                  fullWidth
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  placeholder="username"
                />
              </Grid>
            )}
            <Grid item xs={12}>
              <TextField
                label={editingCredential ? 'New Secret (leave empty to keep current)' : 'Secret'}
                fullWidth
                type={showSecret ? 'text' : 'password'}
                value={formData.secret}
                onChange={(e) => setFormData({ ...formData, secret: e.target.value })}
                placeholder={
                  formData.type === 'api_key' ? 'API Key' :
                  formData.type === 'bearer_token' ? 'Bearer Token' :
                  formData.type === 'ssh' ? 'SSH Private Key' :
                  'Secret Value'
                }
                required={!editingCredential}
                multiline={formData.type === 'ssh'}
                rows={formData.type === 'ssh' ? 4 : 1}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => setShowSecret(!showSecret)}
                        edge="end"
                      >
                        {showSecret ? <VisibilityOffIcon /> : <VisibilityIcon />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
                helperText={editingCredential ? 'Leave empty to keep the current secret' : 'This will be encrypted before storage'}
              />
            </Grid>
            <Grid item xs={12}>
              <Alert severity="info" icon={<SecurityIcon />}>
                <Typography variant="caption">
                  Secrets are encrypted using AES-256 encryption before storage and are never displayed in full after creation.
                </Typography>
              </Alert>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSaveCredential}
            variant="contained"
            disabled={!formData.name || (!editingCredential && !formData.secret)}
            sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
          >
            {editingCredential ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mt: 3 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <SecurityIcon sx={{ fontSize: 40, color: '#667eea' }} />
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#667eea' }}>
                    {credentials.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Credentials
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <CheckCircleIcon sx={{ fontSize: 40, color: '#10b981' }} />
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#10b981' }}>
                    {credentials.filter(c => c.is_active).length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Active Credentials
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <VpnKeyIcon sx={{ fontSize: 40, color: '#764ba2' }} />
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#764ba2' }}>
                    {new Set(credentials.map(c => c.type)).size}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Credential Types
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default CredentialsSecurity;
