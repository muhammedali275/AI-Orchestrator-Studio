import React, { useState, useEffect } from 'react';
import {
  Typography,
  TextField,
  Button,
  Grid,
  Paper,
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  IconButton,
  Tooltip,
  Divider,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Cable as CableIcon,
  Speed as SpeedIcon,
  Psychology as PsychologyIcon,
  Memory as MemoryIcon,
  Dns as DnsIcon,
  Thermostat as ThermostatIcon,
  Storage as StorageIcon,
  Computer as ComputerIcon,
  Router as RouterIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface LLMSettings {
  llm_model: string;
  llm_endpoint: string;
  llm_server_path: string;
  llm_port: string;
  llm_timeout: string;
  llm_api_key: string;
}

interface ConnectionStatus {
  status: 'connected' | 'disconnected' | 'testing';
  message: string;
  latency?: number;
  model_info?: any;
}

interface SystemStats {
  cpu: {
    percent: number;
    count: number;
    frequency: number;
  };
  memory: {
    total_gb: number;
    used_gb: number;
    percent: number;
  };
  disk: {
    total_gb: number;
    used_gb: number;
    percent: number;
  };
  gpu: {
    available: boolean;
    count: number;
    devices: Array<{
      id: number;
      name: string;
      memory_used: number;
      memory_total: number;
      memory_percent: number;
      utilization: number;
      temperature: number;
    }>;
  };
}

interface PortTestResult {
  success: boolean;
  host: string;
  port: number;
  latency_ms?: number;
  message: string;
}

const LLMConfig: React.FC = () => {
  const [settings, setSettings] = useState<LLMSettings>({
    llm_model: '',
    llm_endpoint: '',
    llm_server_path: '',
    llm_port: '',
    llm_timeout: '60',
    llm_api_key: '',
  });
  const [showApiKey, setShowApiKey] = useState(false);
  const [message, setMessage] = useState('');
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    status: 'disconnected',
    message: 'Not tested',
  });
  const [testing, setTesting] = useState(false);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null);
  const [loadingStats, setLoadingStats] = useState(false);
  const [portTestResult, setPortTestResult] = useState<PortTestResult | null>(null);
  const [testingPort, setTestingPort] = useState(false);
  const [portTestHost, setPortTestHost] = useState('localhost');
  const [portTestPort, setPortTestPort] = useState('11434');

  useEffect(() => {
    fetchSettings();
    fetchAvailableModels();
    fetchSystemStats();
    
    // Auto-refresh system stats every 5 seconds
    const interval = setInterval(fetchSystemStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/config/settings');
      const fetchedSettings = response.data.settings;
      setSettings({
        llm_model: fetchedSettings.llm_model || '',
        llm_endpoint: fetchedSettings.llm_endpoint || '/v1/chat/completions',
        llm_server_path: fetchedSettings.llm_server_path || 'http://localhost',
        llm_port: fetchedSettings.llm_port || '11434',
        llm_timeout: fetchedSettings.llm_timeout || '60',
        llm_api_key: fetchedSettings.llm_api_key || '',
      });
    } catch (error) {
      console.error('Error fetching settings:', error);
      setMessage('Error loading settings');
    }
  };

  const fetchAvailableModels = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/llm/models');
      setAvailableModels(response.data.models || []);
    } catch (error) {
      console.error('Error fetching models:', error);
      // Default models if API fails
      setAvailableModels([
        'llama4-scout',
        'ossgpt-70b',
        'gpt-4',
        'gpt-3.5-turbo',
        'claude-3-opus',
        'claude-3-sonnet',
      ]);
    }
  };

  const handleSave = async () => {
    try {
      const settingsToSave = {
        llm_model: settings.llm_model,
        llm_endpoint: settings.llm_endpoint,
        llm_server_path: settings.llm_server_path,
        llm_port: settings.llm_port,
        llm_timeout: settings.llm_timeout,
        llm_api_key: settings.llm_api_key,
      };
      await axios.put('http://localhost:8000/api/config/settings', settingsToSave);
      setMessage('LLM settings updated successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Error saving settings:', error);
      setMessage('Error updating LLM settings');
    }
  };

  const testConnection = async () => {
    setTesting(true);
    setConnectionStatus({
      status: 'testing',
      message: 'Testing connection...',
    });

    try {
      const startTime = Date.now();
      
      // Ensure server_path has protocol
      let serverPath = settings.llm_server_path;
      if (!serverPath.startsWith('http://') && !serverPath.startsWith('https://')) {
        serverPath = `http://${serverPath}`;
      }
      
      const fullUrl = `${serverPath}:${settings.llm_port}${settings.llm_endpoint}`;
      
      const response = await axios.post(
        'http://localhost:8000/api/llm/test-connection',
        {
          server_path: serverPath,
          port: settings.llm_port,
          endpoint: settings.llm_endpoint,
          model: settings.llm_model,
          timeout: parseInt(settings.llm_timeout),
        },
        { timeout: parseInt(settings.llm_timeout) * 1000 }
      );

      const latency = Date.now() - startTime;

      if (response.data.success) {
        setConnectionStatus({
          status: 'connected',
          message: 'Connection successful!',
          latency,
          model_info: response.data.model_info,
        });
      } else {
        setConnectionStatus({
          status: 'disconnected',
          message: response.data.error || 'Connection failed',
        });
      }
    } catch (error: any) {
      setConnectionStatus({
        status: 'disconnected',
        message: error.response?.data?.detail || error.message || 'Connection failed',
      });
    } finally {
      setTesting(false);
    }
  };

  const fetchSystemStats = async () => {
    try {
      setLoadingStats(true);
      const response = await axios.get('http://localhost:8000/api/llm/system-stats');
      setSystemStats(response.data);
    } catch (error) {
      console.error('Error fetching system stats:', error);
    } finally {
      setLoadingStats(false);
    }
  };

  const testPortConnectivity = async () => {
    setTestingPort(true);
    setPortTestResult(null);

    try {
      const response = await axios.post('http://localhost:8000/api/llm/test-port', {
        host: portTestHost,
        port: parseInt(portTestPort),
        timeout: 5,
      });

      setPortTestResult(response.data);
    } catch (error: any) {
      setPortTestResult({
        success: false,
        host: portTestHost,
        port: parseInt(portTestPort),
        message: error.message || 'Connection test failed',
      });
    } finally {
      setTestingPort(false);
    }
  };

  const getFullUrl = () => {
    // Ensure server_path has protocol
    let serverPath = settings.llm_server_path;
    if (!serverPath.startsWith('http://') && !serverPath.startsWith('https://')) {
      serverPath = `http://${serverPath}`;
    }
    return `${serverPath}:${settings.llm_port}${settings.llm_endpoint}`;
  };

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
          LLM Configuration
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Configure LLM server connection and model settings
        </Typography>
      </Box>

      {message && (
        <Alert
          severity={message.includes('Error') ? 'error' : 'success'}
          sx={{ mb: 3 }}
          onClose={() => setMessage('')}
        >
          {message}
        </Alert>
      )}

      {/* Connection Status Card */}
      <Card
        sx={{
          mb: 3,
          background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)',
          border: '1px solid rgba(102, 126, 234, 0.1)',
        }}
      >
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <PsychologyIcon sx={{ fontSize: 40, color: '#667eea' }} />
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Connection Status
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {getFullUrl()}
                </Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              {connectionStatus.latency && (
                <Chip
                  icon={<SpeedIcon />}
                  label={`${connectionStatus.latency}ms`}
                  sx={{
                    background: 'rgba(102, 126, 234, 0.2)',
                    color: '#667eea',
                    fontWeight: 600,
                  }}
                />
              )}
              <Chip
                icon={
                  connectionStatus.status === 'connected' ? (
                    <CheckCircleIcon />
                  ) : connectionStatus.status === 'testing' ? (
                    <CircularProgress size={16} />
                  ) : (
                    <ErrorIcon />
                  )
                }
                label={
                  connectionStatus.status === 'connected'
                    ? 'Connected'
                    : connectionStatus.status === 'testing'
                    ? 'Testing...'
                    : 'Disconnected'
                }
                color={
                  connectionStatus.status === 'connected'
                    ? 'success'
                    : connectionStatus.status === 'testing'
                    ? 'info'
                    : 'error'
                }
                sx={{ fontWeight: 600 }}
              />
            </Box>
          </Box>
          <Typography variant="body2" color="text.secondary">
            {connectionStatus.message}
          </Typography>
        </CardContent>
      </Card>

      {/* Configuration Form */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
          Server Configuration
        </Typography>

        <Grid container spacing={3}>
          {/* Server Path */}
          <Grid item xs={12} md={6}>
            <TextField
              label="Server Path"
              fullWidth
              value={settings.llm_server_path}
              onChange={(e) => setSettings({ ...settings, llm_server_path: e.target.value })}
              placeholder="http://localhost"
              helperText="Base URL of the LLM server"
              InputProps={{
                startAdornment: <CableIcon sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
            />
          </Grid>

          {/* Port */}
          <Grid item xs={12} md={6}>
            <TextField
              label="Port"
              fullWidth
              value={settings.llm_port}
              onChange={(e) => setSettings({ ...settings, llm_port: e.target.value })}
              placeholder="11434"
              helperText="Server port number"
              type="number"
            />
          </Grid>

          {/* Endpoint */}
          <Grid item xs={12} md={8}>
            <TextField
              label="Endpoint Path"
              fullWidth
              value={settings.llm_endpoint}
              onChange={(e) => setSettings({ ...settings, llm_endpoint: e.target.value })}
              placeholder="/v1/chat/completions"
              helperText="API endpoint path (e.g., /v1/chat/completions, /api/generate)"
            />
          </Grid>

          {/* API Key / Auth Token */}
          <Grid item xs={12} md={4}>
            <TextField
              label="API Key / Auth Token"
              fullWidth
              type={showApiKey ? 'text' : 'password'}
              value={settings.llm_api_key}
              onChange={(e) => setSettings({ ...settings, llm_api_key: e.target.value })}
              placeholder="Optional"
              helperText="Authentication token (if required)"
              InputProps={{
                endAdornment: (
                  <IconButton
                    onClick={() => setShowApiKey(!showApiKey)}
                    edge="end"
                    size="small"
                  >
                    {showApiKey ? '👁️' : '🔒'}
                  </IconButton>
                ),
              }}
            />
          </Grid>

          {/* Full URL Preview */}
          <Grid item xs={12}>
            <Box
              sx={{
                p: 2,
                borderRadius: 2,
                background: 'rgba(102, 126, 234, 0.05)',
                border: '1px solid rgba(102, 126, 234, 0.1)',
              }}
            >
              <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                Full URL:
              </Typography>
              <Typography variant="body1" sx={{ fontFamily: 'monospace', color: '#667eea', fontWeight: 600 }}>
                {getFullUrl()}
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={12}>
            <Divider sx={{ my: 2 }} />
          </Grid>

          {/* Model Selection */}
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Model</InputLabel>
              <Select
                value={settings.llm_model}
                onChange={(e) => setSettings({ ...settings, llm_model: e.target.value })}
                label="Model"
              >
                {availableModels.map((model) => (
                  <MenuItem key={model} value={model}>
                    {model}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          {/* Timeout */}
          <Grid item xs={12} md={6}>
            <TextField
              label="Timeout (seconds)"
              fullWidth
              value={settings.llm_timeout}
              onChange={(e) => setSettings({ ...settings, llm_timeout: e.target.value })}
              placeholder="60"
              helperText="Request timeout in seconds"
              type="number"
            />
          </Grid>

          {/* Action Buttons */}
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
              <Button
                variant="outlined"
                onClick={testConnection}
                disabled={testing || !settings.llm_server_path || !settings.llm_port}
                startIcon={testing ? <CircularProgress size={20} /> : <CableIcon />}
                sx={{
                  borderColor: '#667eea',
                  color: '#667eea',
                  '&:hover': {
                    borderColor: '#764ba2',
                    background: 'rgba(102, 126, 234, 0.1)',
                  },
                }}
              >
                {testing ? 'Testing...' : 'Test Connection'}
              </Button>
              <Button
                variant="contained"
                onClick={handleSave}
                disabled={!settings.llm_server_path || !settings.llm_port}
                sx={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                }}
              >
                Save Configuration
              </Button>
              <Tooltip title="Refresh Models">
                <IconButton
                  onClick={fetchAvailableModels}
                  sx={{
                    ml: 'auto',
                    background: 'rgba(102, 126, 234, 0.1)',
                    '&:hover': {
                      background: 'rgba(102, 126, 234, 0.2)',
                    },
                  }}
                >
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* System Monitoring Section */}
      <Paper sx={{ p: 3, mt: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            System Monitoring
          </Typography>
          <Tooltip title="Refresh Stats">
            <IconButton
              onClick={fetchSystemStats}
              disabled={loadingStats}
              sx={{
                background: 'rgba(102, 126, 234, 0.1)',
                '&:hover': {
                  background: 'rgba(102, 126, 234, 0.2)',
                },
              }}
            >
              <RefreshIcon className={loadingStats ? 'rotate-360' : ''} />
            </IconButton>
          </Tooltip>
        </Box>

        {systemStats && (
          <Grid container spacing={3}>
            {/* CPU Usage */}
            <Grid item xs={12} md={6}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <ComputerIcon sx={{ fontSize: 32, color: getStatusColor(systemStats.cpu.percent) }} />
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        CPU Usage
                      </Typography>
                      <Typography variant="h4" sx={{ fontWeight: 700, color: getStatusColor(systemStats.cpu.percent) }}>
                        {systemStats.cpu.percent.toFixed(1)}%
                      </Typography>
                    </Box>
                  </Box>
                  <Box sx={{ mb: 1 }}>
                    <Box
                      sx={{
                        width: '100%',
                        height: 8,
                        borderRadius: 4,
                        background: 'rgba(102, 126, 234, 0.1)',
                        overflow: 'hidden',
                      }}
                    >
                      <Box
                        sx={{
                          width: `${systemStats.cpu.percent}%`,
                          height: '100%',
                          background: `linear-gradient(90deg, ${getStatusColor(systemStats.cpu.percent)}, ${getStatusColor(systemStats.cpu.percent)}dd)`,
                          transition: 'width 0.3s ease',
                        }}
                      />
                    </Box>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    {systemStats.cpu.count} Cores @ {systemStats.cpu.frequency.toFixed(0)} MHz
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* Memory Usage */}
            <Grid item xs={12} md={6}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <MemoryIcon sx={{ fontSize: 32, color: getStatusColor(systemStats.memory.percent) }} />
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Memory Usage
                      </Typography>
                      <Typography variant="h4" sx={{ fontWeight: 700, color: getStatusColor(systemStats.memory.percent) }}>
                        {systemStats.memory.percent.toFixed(1)}%
                      </Typography>
                    </Box>
                  </Box>
                  <Box sx={{ mb: 1 }}>
                    <Box
                      sx={{
                        width: '100%',
                        height: 8,
                        borderRadius: 4,
                        background: 'rgba(102, 126, 234, 0.1)',
                        overflow: 'hidden',
                      }}
                    >
                      <Box
                        sx={{
                          width: `${systemStats.memory.percent}%`,
                          height: '100%',
                          background: `linear-gradient(90deg, ${getStatusColor(systemStats.memory.percent)}, ${getStatusColor(systemStats.memory.percent)}dd)`,
                          transition: 'width 0.3s ease',
                        }}
                      />
                    </Box>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    {systemStats.memory.used_gb.toFixed(2)} GB / {systemStats.memory.total_gb.toFixed(2)} GB
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* Disk Usage */}
            <Grid item xs={12} md={6}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <StorageIcon sx={{ fontSize: 32, color: getStatusColor(systemStats.disk.percent) }} />
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Disk Usage
                      </Typography>
                      <Typography variant="h4" sx={{ fontWeight: 700, color: getStatusColor(systemStats.disk.percent) }}>
                        {systemStats.disk.percent.toFixed(1)}%
                      </Typography>
                    </Box>
                  </Box>
                  <Box sx={{ mb: 1 }}>
                    <Box
                      sx={{
                        width: '100%',
                        height: 8,
                        borderRadius: 4,
                        background: 'rgba(102, 126, 234, 0.1)',
                        overflow: 'hidden',
                      }}
                    >
                      <Box
                        sx={{
                          width: `${systemStats.disk.percent}%`,
                          height: '100%',
                          background: `linear-gradient(90deg, ${getStatusColor(systemStats.disk.percent)}, ${getStatusColor(systemStats.disk.percent)}dd)`,
                          transition: 'width 0.3s ease',
                        }}
                      />
                    </Box>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    {systemStats.disk.used_gb.toFixed(2)} GB / {systemStats.disk.total_gb.toFixed(2)} GB
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            {/* GPU Usage */}
            {systemStats.gpu.available && systemStats.gpu.devices.map((gpu) => (
              <Grid item xs={12} md={6} key={gpu.id}>
                <Card sx={{ height: '100%' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                      <DnsIcon sx={{ fontSize: 32, color: getStatusColor(gpu.utilization) }} />
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="body2" color="text.secondary">
                          {gpu.name}
                        </Typography>
                        <Typography variant="h4" sx={{ fontWeight: 700, color: getStatusColor(gpu.utilization) }}>
                          {gpu.utilization.toFixed(1)}%
                        </Typography>
                      </Box>
                      <Chip
                        icon={<ThermostatIcon />}
                        label={`${gpu.temperature}°C`}
                        size="small"
                        sx={{
                          background: gpu.temperature > 80 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                          color: gpu.temperature > 80 ? '#ef4444' : '#10b981',
                          fontWeight: 600,
                        }}
                      />
                    </Box>
                    <Box sx={{ mb: 1 }}>
                      <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                        GPU Utilization
                      </Typography>
                      <Box
                        sx={{
                          width: '100%',
                          height: 8,
                          borderRadius: 4,
                          background: 'rgba(102, 126, 234, 0.1)',
                          overflow: 'hidden',
                          mb: 2,
                        }}
                      >
                        <Box
                          sx={{
                            width: `${gpu.utilization}%`,
                            height: '100%',
                            background: `linear-gradient(90deg, ${getStatusColor(gpu.utilization)}, ${getStatusColor(gpu.utilization)}dd)`,
                            transition: 'width 0.3s ease',
                          }}
                        />
                      </Box>
                      <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                        GPU Memory
                      </Typography>
                      <Box
                        sx={{
                          width: '100%',
                          height: 8,
                          borderRadius: 4,
                          background: 'rgba(102, 126, 234, 0.1)',
                          overflow: 'hidden',
                        }}
                      >
                        <Box
                          sx={{
                            width: `${gpu.memory_percent}%`,
                            height: '100%',
                            background: `linear-gradient(90deg, ${getStatusColor(gpu.memory_percent)}, ${getStatusColor(gpu.memory_percent)}dd)`,
                            transition: 'width 0.3s ease',
                          }}
                        />
                      </Box>
                    </Box>
                    <Typography variant="caption" color="text.secondary">
                      {gpu.memory_used.toFixed(2)} GB / {gpu.memory_total.toFixed(2)} GB
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Paper>

      {/* Port Connectivity Testing */}
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
          Port Connectivity Test
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              label="Host"
              fullWidth
              value={portTestHost}
              onChange={(e) => setPortTestHost(e.target.value)}
              placeholder="localhost or IP address"
              helperText="Enter hostname or IP address to test"
              InputProps={{
                startAdornment: <RouterIcon sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              label="Port"
              fullWidth
              value={portTestPort}
              onChange={(e) => setPortTestPort(e.target.value)}
              placeholder="11434"
              helperText="Port number to test"
              type="number"
            />
          </Grid>

          <Grid item xs={12}>
            <Button
              variant="outlined"
              onClick={testPortConnectivity}
              disabled={testingPort || !portTestHost || !portTestPort}
              startIcon={testingPort ? <CircularProgress size={20} /> : <CableIcon />}
              sx={{
                borderColor: '#667eea',
                color: '#667eea',
                '&:hover': {
                  borderColor: '#764ba2',
                  background: 'rgba(102, 126, 234, 0.1)',
                },
              }}
            >
              {testingPort ? 'Testing Port...' : 'Test Port Connectivity'}
            </Button>
          </Grid>

          {portTestResult && (
            <Grid item xs={12}>
              <Alert
                severity={portTestResult.success ? 'success' : 'error'}
                icon={portTestResult.success ? <CheckCircleIcon /> : <ErrorIcon />}
                sx={{ mt: 2 }}
              >
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>
                    {portTestResult.message}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Host: {portTestResult.host} | Port: {portTestResult.port}
                    {portTestResult.latency_ms && ` | Latency: ${portTestResult.latency_ms}ms`}
                  </Typography>
                </Box>
              </Alert>
            </Grid>
          )}
        </Grid>
      </Paper>

      {/* Model Info */}
      {connectionStatus.model_info && (
        <Paper sx={{ p: 3, mt: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
            Model Information
          </Typography>
          <Grid container spacing={2}>
            {Object.entries(connectionStatus.model_info).map(([key, value]) => (
              <Grid item xs={12} sm={6} md={4} key={key}>
                <Box
                  sx={{
                    p: 2,
                    borderRadius: 2,
                    background: 'rgba(102, 126, 234, 0.05)',
                    border: '1px solid rgba(102, 126, 234, 0.1)',
                  }}
                >
                  <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                    {key.replace(/_/g, ' ').toUpperCase()}
                  </Typography>
                  <Typography variant="body1" sx={{ fontWeight: 600 }}>
                    {String(value)}
                  </Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}
    </Box>
  );
};

export default LLMConfig;
