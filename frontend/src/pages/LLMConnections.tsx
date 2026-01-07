import React, { useState, useEffect } from 'react';
import {
  Typography,
  Paper,
  Box,
  Button,
  TextField,
  Grid,
  IconButton,
  Tooltip,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
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
  Settings as SettingsIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Cable as CableIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface LLMConnection {
  id: string;
  name: string;
  base_url: string;
  api_key?: string;
  model: string;
  timeout: number;
  max_tokens?: number;
  temperature: number;
  is_local?: boolean;
  status?: {
    connected: boolean;
    message: string;
    latency?: number;
    provider?: string;
    status_code?: number;
  };
}

const LLMConnections: React.FC = () => {
  const [connections, setConnections] = useState<LLMConnection[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [editingConnection, setEditingConnection] = useState<LLMConnection | null>(null);
  const [showApiKey, setShowApiKey] = useState(false);
  const [testingConnection, setTestingConnection] = useState<string | null>(null);

  const [formData, setFormData] = useState<LLMConnection>({
    id: '',
    name: '',
    base_url: '',
    api_key: '',
    model: '',
    timeout: 60,
    max_tokens: 2048,
    temperature: 0.7,
    is_local: false,
  });

  useEffect(() => {
    fetchConnections();
  }, []);

  const fetchConnections = async () => {
    setLoading(true);
    try {
      // Prefer multi-connection endpoint
      const multi = await axios.get('http://localhost:8000/api/config/llm-connections', { timeout: 5000 });
      const conns = (multi.data?.connections || []).map((c: any) => ({
        id: c.id,
        name: c.name || c.id,
        base_url: c.base_url || '',
        api_key: c.api_key || '',
        model: c.model || '',
        timeout: c.timeout || 60,
        max_tokens: c.max_tokens ?? 2048,
        temperature: c.temperature ?? 0.7,
        is_local: (c.base_url || '').includes('localhost') || (c.base_url || '').includes('127.0.0.1') || (c.base_url || '').includes('11434'),
      })) as LLMConnection[];

      if (conns.length > 0) {
        setConnections(conns);
      } else {
        // Fallback to single-config endpoint
        const response = await axios.get('http://localhost:8000/api/llm/config', { timeout: 5000 });
        const singleConfig = response.data;
        const connection = {
          id: 'default',
          name: 'Default LLM',
          base_url: singleConfig.base_url || '',
          api_key: singleConfig.api_key || '',
          model: singleConfig.default_model || '',
          timeout: singleConfig.timeout_seconds || 60,
          max_tokens: singleConfig.max_tokens || 2048,
          temperature: singleConfig.temperature || 0.7,
          is_local: (singleConfig.base_url || '').includes('localhost') || (singleConfig.base_url || '').includes('11434'),
        } as LLMConnection;
        setConnections([connection]);
      }
    } catch (error: any) {
      console.error('Error fetching LLM connections:', error);
      // Show empty state if backend is not configured
      setConnections([]);
      if (error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK') {
        setMessage('Error: Cannot connect to backend. Please ensure the backend server is running on port 8000.');
      } else {
        setMessage('Error: No LLM configuration found. Click "Add Connection" to configure.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (connection?: LLMConnection) => {
    if (connection) {
      setEditingConnection(connection);
      setFormData(connection);
    } else {
      setEditingConnection(null);
      setFormData({
        id: `llm_${Date.now()}`,
        name: '',
        base_url: '',
        api_key: '',
        model: '',
        timeout: 60,
        max_tokens: 2048,
        temperature: 0.7,
        is_local: false,
      });
    }
    setOpenDialog(true);
    setShowApiKey(false);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingConnection(null);
    setShowApiKey(false);
  };

  const handleSaveConnection = async () => {
    // Validate required fields
    if (!formData.name.trim()) {
      setMessage('Connection name is required');
      return;
    }
    if (!formData.base_url.trim()) {
      setMessage('Base URL is required');
      return;
    }
    // Model is optional - will be selected from available models later

    // Normalize base URL: strip trailing slashes and paths (e.g., remove /api/chat)
    const normalizeBaseUrl = (url: string) => {
      let trimmed = url.trim();
      try {
        const parsed = new URL(trimmed);
        return `${parsed.protocol}//${parsed.host}`;
      } catch (e) {
        // Fallback: strip trailing slash and anything after first '/'
        trimmed = trimmed.replace(/\/$/, '');
        const idx = trimmed.indexOf('/', trimmed.indexOf('//') + 2);
        return idx > -1 ? trimmed.slice(0, idx) : trimmed;
      }
    };

    const normalizedBase = normalizeBaseUrl(formData.base_url);
    if (normalizedBase !== formData.base_url.trim()) {
      setMessage(`Base URL normalized to ${normalizedBase} (paths like /api/chat were removed).`);
    }

    setLoading(true);
    setMessage('Testing connection...');
    
    try {
      // Generate unique ID if creating new connection
      const connectionId = editingConnection?.id || `llm-${Date.now()}`;
      
      // Use POST to create/update connection in multi-connection store
      // Backend will automatically test the connection before saving
      const response = await axios.post(`http://localhost:8000/api/config/llm-connections`, {
        id: connectionId,
        name: formData.name,
        base_url: normalizedBase,
        model: formData.model || undefined, // Allow empty model - will be selected from available models
        api_key: formData.api_key || undefined,
        timeout: formData.timeout,
        max_tokens: formData.max_tokens,
        temperature: formData.temperature,
        is_local: normalizedBase.includes('localhost') || normalizedBase.includes('127.0.0.1'),
      }, { timeout: 30000 }); // 30s timeout for connection test

      if (response.data.success && response.data.test_result) {
        const testResult = response.data.test_result;
        const latencyMsg = testResult.latency_ms ? ` (${Math.round(testResult.latency_ms)}ms)` : '';
        setMessage(`✓ Connection successful! ${testResult.message}${latencyMsg}`);
        await fetchConnections();
        handleCloseDialog();
        setTimeout(() => setMessage(''), 5000);
      } else if (response.data.success) {
        setMessage('LLM connection saved successfully! ✓');
        await fetchConnections();
        handleCloseDialog();
        setTimeout(() => setMessage(''), 3000);
      } else {
        setMessage('Configuration saved but may need verification');
        await fetchConnections();
        handleCloseDialog();
      }
    } catch (error: any) {
      console.error('Error saving connection:', error);
      if (error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK') {
        setMessage('Cannot connect to backend. Please ensure the backend server is running on port 8000.');
      } else if (error.response?.status === 400) {
        // Connection test failed
        setMessage(`⚠️ Connection test failed: ${error.response?.data?.detail || 'Server unreachable'}`);
      } else {
        setMessage(`Error: ${error.response?.data?.detail || error.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteConnection = async (id: string, name: string) => {
    if (!window.confirm(`Are you sure you want to delete connection "${name}"?`)) return;
    
    try {
      await axios.delete(`http://localhost:8000/api/config/llm-connections/${id}`);
      setMessage('LLM connection deleted successfully!');
      fetchConnections();
      setTimeout(() => setMessage(''), 3000);
    } catch (error: any) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleTestConnection = async (connection: LLMConnection) => {
    setTestingConnection(connection.id);
    try {
      // Call backend test endpoint for specific connection id
      const resp = await axios.post(`http://localhost:8000/api/config/llm-connections/${connection.id}/test`);

      const data = resp.data || {};
      if (data.connected) {
        setMessage(`Connection "${connection.name}" is reachable (${Math.round(data.latency_ms)}ms)`);
      } else {
        setMessage(`Error: Connection "${connection.name}" unreachable: ${data.message || 'Test failed'}`);
      }
      const updatedConnections = connections.map(c => {
        if (c.id !== connection.id) return c;
        const newBase = typeof data.base_url === 'string' && data.base_url.length > 0 ? data.base_url : c.base_url;
        return {
          ...c,
          base_url: newBase,
          status: {
            connected: !!data.connected,
            message: data.message || (data.connected ? 'Connected' : 'Disconnected'),
            latency: data.latency_ms || 0,
            provider: data.provider,
            status_code: data.status_code,
          },
        } as LLMConnection;
      });
      setConnections(updatedConnections);
      setTimeout(() => setMessage(''), 3000);
    } catch (error: any) {
      setMessage(`Error testing connection: ${error.message}`);
    } finally {
      setTestingConnection(null);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '—';
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
            LLM Connections
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage Large Language Model server connections and configurations
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Tooltip title="Refresh Connections">
            <IconButton
              onClick={fetchConnections}
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
            Add Connection
          </Button>
        </Box>
      </Box>

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

      {/* Connections Table */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : connections.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <SettingsIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No LLM connections configured
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Add your first LLM connection to get started
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
            sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
          >
            Add Connection
          </Button>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell><strong>Name</strong></TableCell>
                <TableCell><strong>Base URL</strong></TableCell>
                <TableCell><strong>Model</strong></TableCell>
                <TableCell><strong>Timeout</strong></TableCell>
                <TableCell><strong>Temperature</strong></TableCell>
                <TableCell><strong>Status</strong></TableCell>
                <TableCell><strong>Actions</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {connections.map((connection) => (
                <TableRow key={connection.id} hover>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <SettingsIcon sx={{ color: '#667eea', fontSize: 20 }} />
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {connection.name}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                      {connection.base_url}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={connection.model}
                      size="small"
                      sx={{ background: 'rgba(102, 126, 234, 0.2)', color: '#667eea' }}
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{connection.timeout}s</Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{connection.temperature}</Typography>
                  </TableCell>
                  <TableCell>
                    {connection.status ? (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Tooltip
                          title={`$${''}{connection.status.message}${connection.status.provider ? ` • ${connection.status.provider}` : ''}${connection.status.status_code ? ` • HTTP ${connection.status.status_code}` : ''}`}
                        >
                          <Chip
                            icon={connection.status.connected ? <CheckCircleIcon /> : <ErrorIcon />}
                            label={connection.status.connected ? 'Connected' : 'Disconnected'}
                            size="small"
                            color={connection.status.connected ? 'success' : 'error'}
                          />
                        </Tooltip>
                        {connection.status.latency !== undefined && (
                          <Chip
                            icon={<SpeedIcon />}
                            label={`${Math.round(connection.status.latency)}ms`}
                            size="small"
                            sx={{ background: 'rgba(102, 126, 234, 0.2)', color: '#667eea' }}
                          />
                        )}
                      </Box>
                    ) : (
                      <Chip label="Not tested" size="small" />
                    )}
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Tooltip title="Test Connection">
                        <IconButton
                          size="small"
                          onClick={() => handleTestConnection(connection)}
                          disabled={testingConnection === connection.id}
                        >
                          {testingConnection === connection.id ? (
                            <CircularProgress size={20} />
                          ) : (
                            <CableIcon fontSize="small" />
                          )}
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit">
                        <IconButton
                          size="small"
                          onClick={() => handleOpenDialog(connection)}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDeleteConnection(connection.id, connection.name)}
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
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingConnection ? 'Edit LLM Connection' : 'Add New LLM Connection'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                label="Connection Name"
                fullWidth
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Local Ollama"
                helperText="A descriptive name for this connection"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Base URL"
                fullWidth
                value={formData.base_url}
                onChange={(e) => {
                  const url = e.target.value;
                  const isLocal = url.includes('localhost') || 
                                 url.includes('127.0.0.1') || 
                                 url.includes('11434') || 
                                 url.toLowerCase().includes('ollama');
                  setFormData({ ...formData, base_url: url, is_local: isLocal });
                }}
                placeholder="http://localhost:11434"
                helperText="Server URL only (e.g., http://localhost:11434) - do NOT include /api/chat or other paths"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Default Model (Optional)"
                fullWidth
                value={formData.model}
                onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                placeholder="Leave empty to select from available models later"
                helperText="You can specify a default model or leave empty - models will be auto-detected from the server"
              />
            </Grid>
            {formData.is_local ? (
              <Grid item xs={12}>
                <Alert severity="info" icon={<CableIcon />}>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    Local server (no token required)
                  </Typography>
                  <Typography variant="caption">
                    API key field is hidden for local LLM connections like Ollama running on localhost
                  </Typography>
                </Alert>
              </Grid>
            ) : (
              <Grid item xs={12}>
                <TextField
                  label="API Key / Token"
                  fullWidth
                  type={showApiKey ? 'text' : 'password'}
                  value={formData.api_key}
                  onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                  placeholder="Required for most LLM services"
                  required
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowApiKey(!showApiKey)}
                          edge="end"
                        >
                          {showApiKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                  helperText="API key required for most cloud LLM services"
                />
              </Grid>
            )}
            <Grid item xs={12} md={4}>
              <TextField
                label="Timeout (seconds)"
                fullWidth
                type="number"
                value={formData.timeout}
                onChange={(e) => setFormData({ ...formData, timeout: parseInt(e.target.value) })}
                inputProps={{ min: 1, max: 300 }}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                label="Max Tokens"
                fullWidth
                type="number"
                value={formData.max_tokens}
                onChange={(e) => setFormData({ ...formData, max_tokens: parseInt(e.target.value) })}
                inputProps={{ min: 1, max: 32000 }}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                label="Temperature"
                fullWidth
                type="number"
                value={formData.temperature}
                onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
                inputProps={{ min: 0, max: 2, step: 0.1 }}
                helperText="0 = deterministic, 2 = creative"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSaveConnection}
            variant="contained"
            disabled={!formData.name || !formData.base_url || (!formData.is_local && !formData.api_key)}
            sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
          >
            {editingConnection ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Statistics */}
      <Grid container spacing={3} sx={{ mt: 3 }}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <SettingsIcon sx={{ fontSize: 40, color: '#667eea' }} />
              <Box>
                <Typography variant="h4" sx={{ fontWeight: 700, color: '#667eea' }}>
                  {connections.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Connections
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <CheckCircleIcon sx={{ fontSize: 40, color: '#10b981' }} />
              <Box>
                <Typography variant="h4" sx={{ fontWeight: 700, color: '#10b981' }}>
                  {connections.filter(c => c.status?.connected).length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Active Connections
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <SpeedIcon sx={{ fontSize: 40, color: '#764ba2' }} />
              <Box>
                <Typography variant="h4" sx={{ fontWeight: 700, color: '#764ba2' }}>
                  {connections.filter(c => c.status?.latency).length > 0
                    ? Math.round(connections.filter(c => c.status?.latency).reduce((sum, c) => sum + (c.status?.latency || 0), 0) / connections.filter(c => c.status?.latency).length)
                    : 0}ms
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Avg Response Time
                </Typography>
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default LLMConnections;
