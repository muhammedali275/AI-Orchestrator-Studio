import React, { useState, useEffect } from 'react';
import {
  Typography,
  Paper,
  Box,
  Tabs,
  Tab,
  TextField,
  Button,
  Grid,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  Alert,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Computer as ComputerIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Cable as CableIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface Server {
  id: string;
  name: string;
  host: string;
  port: number;
  type: string;
  status: string;
  credentials?: {
    username?: string;
    password?: string;
    api_key?: string;
  };
}

interface ServerMetrics {
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  network_in: number;
  network_out: number;
  timestamp: string;
}

const Monitoring: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [servers, setServers] = useState<Server[]>([]);
  const [selectedServer, setSelectedServer] = useState<Server | null>(null);
  const [metrics, setMetrics] = useState<ServerMetrics | null>(null);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const [newServer, setNewServer] = useState({
    name: '',
    host: '',
    port: 22,
    type: 'ssh',
    username: '',
    password: '',
    api_key: '',
  });

  const fetchServers = async () => {
    try {
      // Placeholder - will be implemented with backend
      setServers([
        {
          id: '1',
          name: 'Production Server',
          host: '192.168.1.100',
          port: 22,
          type: 'ssh',
          status: 'connected',
        },
      ]);
    } catch (error) {
      console.error('Error fetching servers:', error);
    }
  };

  const fetchMetrics = async (serverId: string) => {
    setLoading(true);
    try {
      // Placeholder - will be implemented with backend
      setMetrics({
        cpu_percent: 45.2,
        memory_percent: 62.8,
        disk_percent: 38.5,
        network_in: 1024,
        network_out: 512,
        timestamp: new Date().toISOString(),
      });
    } catch (error) {
      console.error('Error fetching metrics:', error);
    } finally {
      setLoading(false);
    }
  };

  const addServer = async () => {
    try {
      // Placeholder - will be implemented with backend
      const server: Server = {
        id: Date.now().toString(),
        name: newServer.name,
        host: newServer.host,
        port: newServer.port,
        type: newServer.type,
        status: 'disconnected',
        credentials: {
          username: newServer.username,
          password: newServer.password,
          api_key: newServer.api_key,
        },
      };
      
      setServers([...servers, server]);
      setShowAddDialog(false);
      setMessage('Server added successfully!');
      setTimeout(() => setMessage(''), 3000);
      
      // Reset form
      setNewServer({
        name: '',
        host: '',
        port: 22,
        type: 'ssh',
        username: '',
        password: '',
        api_key: '',
      });
    } catch (error) {
      console.error('Error adding server:', error);
      setMessage('Error adding server');
    }
  };

  const deleteServer = async (serverId: string) => {
    try {
      setServers(servers.filter(s => s.id !== serverId));
      setMessage('Server deleted successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Error deleting server:', error);
    }
  };

  const testConnection = async (server: Server) => {
    try {
      // Placeholder - will be implemented with backend
      setMessage(`Testing connection to ${server.name}...`);
      setTimeout(() => {
        setMessage(`Connection to ${server.name} successful!`);
        setTimeout(() => setMessage(''), 3000);
      }, 1000);
    } catch (error) {
      setMessage(`Connection to ${server.name} failed!`);
    }
  };

  useEffect(() => {
    fetchServers();
  }, []);

  useEffect(() => {
    if (selectedServer) {
      fetchMetrics(selectedServer.id);
      const interval = setInterval(() => fetchMetrics(selectedServer.id), 5000);
      return () => clearInterval(interval);
    }
  }, [selectedServer]);

  const getStatusColor = (percent: number) => {
    if (percent < 60) return '#10b981';
    if (percent < 80) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <Box className="fade-in">
      <Box sx={{ mb: 4 }}>
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
          Server Monitoring
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Real-time monitoring of destination servers
        </Typography>
      </Box>

      {message && (
        <Alert severity={message.includes('Error') || message.includes('failed') ? 'error' : 'success'} 
               sx={{ mb: 3 }} onClose={() => setMessage('')}>
          {message}
        </Alert>
      )}

      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab label="Servers" />
          <Tab label="Credentials" />
          <Tab label="Metrics" />
        </Tabs>
      </Paper>

      {/* Servers Tab */}
      {tabValue === 0 && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Monitored Servers
            </Typography>
            <Button variant="contained" startIcon={<AddIcon />} onClick={() => setShowAddDialog(true)}
              sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
              Add Server
            </Button>
          </Box>

          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell><strong>Name</strong></TableCell>
                  <TableCell><strong>Host</strong></TableCell>
                  <TableCell><strong>Port</strong></TableCell>
                  <TableCell><strong>Type</strong></TableCell>
                  <TableCell><strong>Status</strong></TableCell>
                  <TableCell><strong>Actions</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {servers.map((server) => (
                  <TableRow key={server.id}>
                    <TableCell>{server.name}</TableCell>
                    <TableCell>{server.host}</TableCell>
                    <TableCell>{server.port}</TableCell>
                    <TableCell><Chip label={server.type.toUpperCase()} size="small" /></TableCell>
                    <TableCell>
                      <Chip
                        icon={server.status === 'connected' ? <SuccessIcon /> : <ErrorIcon />}
                        label={server.status}
                        size="small"
                        color={server.status === 'connected' ? 'success' : 'error'}
                      />
                    </TableCell>
                    <TableCell>
                      <Tooltip title="Test Connection">
                        <IconButton size="small" onClick={() => testConnection(server)}>
                          <CableIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="View Metrics">
                        <IconButton size="small" onClick={() => { setSelectedServer(server); setTabValue(2); }}>
                          <ComputerIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton size="small" onClick={() => deleteServer(server.id)} color="error">
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Credentials Tab */}
      {tabValue === 1 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
            Server Credentials
          </Typography>
          <Alert severity="info" sx={{ mb: 3 }}>
            Credentials are encrypted and stored securely. They are used to connect to destination servers for monitoring.
          </Alert>
          <Grid container spacing={3}>
            {servers.map((server) => (
              <Grid item xs={12} md={6} key={server.id}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>{server.name}</Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {server.host}:{server.port}
                    </Typography>
                    <Box sx={{ mt: 2 }}>
                      <Chip label={`Type: ${server.type.toUpperCase()}`} size="small" sx={{ mr: 1 }} />
                      <Chip 
                        label={server.credentials ? 'Credentials Configured' : 'No Credentials'} 
                        size="small"
                        color={server.credentials ? 'success' : 'warning'}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      {/* Metrics Tab */}
      {tabValue === 2 && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              {selectedServer ? `Metrics: ${selectedServer.name}` : 'Select a server'}
            </Typography>
            {selectedServer && (
              <Tooltip title="Refresh Metrics">
                <IconButton onClick={() => fetchMetrics(selectedServer.id)} disabled={loading}>
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
            )}
          </Box>

          {selectedServer && metrics ? (
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="body2" color="text.secondary" gutterBottom>CPU Usage</Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: getStatusColor(metrics.cpu_percent) }}>
                      {metrics.cpu_percent.toFixed(1)}%
                    </Typography>
                    <Box sx={{ width: '100%', height: 8, borderRadius: 4, background: 'rgba(102, 126, 234, 0.1)', mt: 2 }}>
                      <Box sx={{ 
                        width: `${metrics.cpu_percent}%`, height: '100%', borderRadius: 4,
                        background: `linear-gradient(90deg, ${getStatusColor(metrics.cpu_percent)}, ${getStatusColor(metrics.cpu_percent)}dd)` 
                      }} />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="body2" color="text.secondary" gutterBottom>Memory Usage</Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: getStatusColor(metrics.memory_percent) }}>
                      {metrics.memory_percent.toFixed(1)}%
                    </Typography>
                    <Box sx={{ width: '100%', height: 8, borderRadius: 4, background: 'rgba(102, 126, 234, 0.1)', mt: 2 }}>
                      <Box sx={{ 
                        width: `${metrics.memory_percent}%`, height: '100%', borderRadius: 4,
                        background: `linear-gradient(90deg, ${getStatusColor(metrics.memory_percent)}, ${getStatusColor(metrics.memory_percent)}dd)` 
                      }} />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="body2" color="text.secondary" gutterBottom>Disk Usage</Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: getStatusColor(metrics.disk_percent) }}>
                      {metrics.disk_percent.toFixed(1)}%
                    </Typography>
                    <Box sx={{ width: '100%', height: 8, borderRadius: 4, background: 'rgba(102, 126, 234, 0.1)', mt: 2 }}>
                      <Box sx={{ 
                        width: `${metrics.disk_percent}%`, height: '100%', borderRadius: 4,
                        background: `linear-gradient(90deg, ${getStatusColor(metrics.disk_percent)}, ${getStatusColor(metrics.disk_percent)}dd)` 
                      }} />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="body2" color="text.secondary" gutterBottom>Network Traffic</Typography>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">IN</Typography>
                        <Typography variant="h6" sx={{ color: '#10b981' }}>
                          {(metrics.network_in / 1024).toFixed(2)} MB/s
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">OUT</Typography>
                        <Typography variant="h6" sx={{ color: '#3b82f6' }}>
                          {(metrics.network_out / 1024).toFixed(2)} MB/s
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          ) : (
            <Alert severity="info">Select a server from the Servers tab to view metrics</Alert>
          )}
        </Paper>
      )}

      {/* Add Server Dialog */}
      <Dialog open={showAddDialog} onClose={() => setShowAddDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Add Monitoring Server</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                label="Server Name"
                fullWidth
                value={newServer.name}
                onChange={(e) => setNewServer({ ...newServer, name: e.target.value })}
                placeholder="Production Server"
              />
            </Grid>
            <Grid item xs={12} sm={8}>
              <TextField
                label="Host/IP Address"
                fullWidth
                value={newServer.host}
                onChange={(e) => setNewServer({ ...newServer, host: e.target.value })}
                placeholder="192.168.1.100"
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                label="Port"
                fullWidth
                type="number"
                value={newServer.port}
                onChange={(e) => setNewServer({ ...newServer, port: parseInt(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Connection Type</InputLabel>
                <Select
                  value={newServer.type}
                  onChange={(e) => setNewServer({ ...newServer, type: e.target.value })}
                  label="Connection Type"
                >
                  <MenuItem value="ssh">SSH</MenuItem>
                  <MenuItem value="api">API</MenuItem>
                  <MenuItem value="snmp">SNMP</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            {newServer.type === 'ssh' && (
              <>
                <Grid item xs={12}>
                  <TextField
                    label="Username"
                    fullWidth
                    value={newServer.username}
                    onChange={(e) => setNewServer({ ...newServer, username: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    label="Password"
                    fullWidth
                    type={showPassword ? 'text' : 'password'}
                    value={newServer.password}
                    onChange={(e) => setNewServer({ ...newServer, password: e.target.value })}
                    InputProps={{
                      endAdornment: (
                        <IconButton onClick={() => setShowPassword(!showPassword)} edge="end">
                          {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                        </IconButton>
                      ),
                    }}
                  />
                </Grid>
              </>
            )}
            
            {newServer.type === 'api' && (
              <Grid item xs={12}>
                <TextField
                  label="API Key"
                  fullWidth
                  type={showPassword ? 'text' : 'password'}
                  value={newServer.api_key}
                  onChange={(e) => setNewServer({ ...newServer, api_key: e.target.value })}
                  InputProps={{
                    endAdornment: (
                      <IconButton onClick={() => setShowPassword(!showPassword)} edge="end">
                        {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                      </IconButton>
                    ),
                  }}
                />
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowAddDialog(false)}>Cancel</Button>
          <Button onClick={addServer} variant="contained" disabled={!newServer.name || !newServer.host}>
            Add Server
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Monitoring;
