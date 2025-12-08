import React, { useState, useEffect } from 'react';
import {
  Typography,
  Paper,
  Box,
  Button,
  Grid,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  Alert,
  Chip,
  CircularProgress,
  LinearProgress,
  Divider,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  MonitorHeart as MonitorIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Computer as ComputerIcon,
  Storage as StorageIcon,
  Memory as MemoryIcon,
  Dns as DnsIcon,
  RestartAlt as RestartIcon,
  Public as PublicIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface ServiceStatus {
  name: string;
  status: 'UP' | 'DOWN' | 'DEGRADED';
  uptime?: number;
  last_check?: string;
  message?: string;
}

interface SystemMetrics {
  cpu: { percent: number; count: number };
  memory: { total_mb: number; used_mb: number; percent: number };
  disk: { total_gb: number; used_gb: number; percent: number };
}

interface LocationInfo {
  zone: string;
  region: string;
  country: string;
  coordinates?: { lat: number; lng: number };
}

const MonitoringServices: React.FC = () => {
  const [services, setServices] = useState<ServiceStatus[]>([]);
  const [orchestratorMetrics, setOrchestratorMetrics] = useState<SystemMetrics | null>(null);
  const [llmMetrics, setLlmMetrics] = useState<SystemMetrics | null>(null);
  const [location, setLocation] = useState<LocationInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [restarting, setRestarting] = useState<string | null>(null);

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchServices(),
        fetchMetrics(),
        fetchLocation(),
      ]);
    } catch (error) {
      console.error('Error fetching monitoring data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchServices = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/monitoring/connectivity');
      const servicesData: ServiceStatus[] = [];
      
      // LLM Service
      if (response.data.services?.llm) {
        servicesData.push({
          name: 'LLM Service (Ollama)',
          status: response.data.services.llm.reachable ? 'UP' : 'DOWN',
          message: response.data.services.llm.error || 'Healthy',
        });
      }
      
      // Agents
      if (response.data.services?.agents) {
        Object.entries(response.data.services.agents).forEach(([name, data]: [string, any]) => {
          servicesData.push({
            name: `Agent: ${name}`,
            status: data.reachable ? 'UP' : 'DOWN',
            message: data.error || 'Healthy',
          });
        });
      }
      
      // Datasources
      if (response.data.services?.datasources) {
        Object.entries(response.data.services.datasources).forEach(([name, data]: [string, any]) => {
          servicesData.push({
            name: `Datasource: ${name}`,
            status: data.reachable ? 'UP' : 'DOWN',
            message: data.error || 'Healthy',
          });
        });
      }
      
      // Add default services if none configured
      if (servicesData.length === 0) {
        servicesData.push(
          { name: 'Orchestrator', status: 'UP', message: 'Running' },
          { name: 'LLM Service', status: 'DOWN', message: 'Not configured' },
          { name: 'Redis Cache', status: 'DEGRADED', message: 'Optional' },
        );
      }
      
      setServices(servicesData);
    } catch (error) {
      console.error('Error fetching services:', error);
    }
  };

  const fetchMetrics = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/monitoring/metrics');
      if (response.data.system) {
        setOrchestratorMetrics(response.data.system);
        // For now, use same metrics for LLM (in production, would be separate endpoint)
        setLlmMetrics(response.data.system);
      }
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  };

  const fetchLocation = async () => {
    try {
      // Mock location data - in production would call /api/monitor/location
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      setLocation({
        zone: timezone,
        region: timezone.split('/')[0] || 'Unknown',
        country: timezone.split('/')[1] || 'Unknown',
        coordinates: { lat: 29.3759, lng: 47.9774 }, // Kuwait coordinates as example
      });
    } catch (error) {
      console.error('Error fetching location:', error);
    }
  };

  const handleRestartService = async (serviceName: string) => {
    if (!window.confirm(`Restart service "${serviceName}"?`)) return;
    
    setRestarting(serviceName);
    try {
      await axios.post(`http://localhost:8000/api/monitor/services/${serviceName}/restart`);
      setMessage(`Service "${serviceName}" restarted successfully!`);
      setTimeout(() => {
        fetchServices();
        setMessage('');
      }, 2000);
    } catch (error: any) {
      setMessage(`Error restarting service: ${error.message}`);
    } finally {
      setRestarting(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'UP': return '#10b981';
      case 'DOWN': return '#ef4444';
      case 'DEGRADED': return '#f59e0b';
      default: return '#a1a1aa';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'UP': return <CheckCircleIcon />;
      case 'DOWN': return <ErrorIcon />;
      case 'DEGRADED': return <WarningIcon />;
      default: return <WarningIcon />;
    }
  };

  const getMetricColor = (percent: number) => {
    if (percent < 60) return '#10b981';
    if (percent < 80) return '#f59e0b';
    return '#ef4444';
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
            Monitoring & Services
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Real-time system health and service status monitoring
          </Typography>
        </Box>
        <Tooltip title="Refresh All">
          <IconButton
            onClick={fetchAllData}
            disabled={loading}
            sx={{
              background: 'rgba(102, 126, 234, 0.1)',
              '&:hover': { background: 'rgba(102, 126, 234, 0.2)' },
            }}
          >
            <RefreshIcon className={loading ? 'rotate-360' : ''} />
          </IconButton>
        </Tooltip>
      </Box>

      {message && (
        <Alert severity={message.includes('Error') ? 'error' : 'success'} sx={{ mb: 3 }} onClose={() => setMessage('')}>
          {message}
        </Alert>
      )}

      {/* Location & Zone */}
      {location && (
        <Card sx={{ mb: 3, background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(37, 99, 235, 0.1) 100%)', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <PublicIcon sx={{ fontSize: 48, color: '#3b82f6' }} />
              <Box sx={{ flexGrow: 1 }}>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                  System Location
                </Typography>
                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                  <Chip label={`Zone: ${location.zone}`} sx={{ background: 'rgba(59, 130, 246, 0.2)', color: '#3b82f6' }} />
                  <Chip label={`Region: ${location.region}`} sx={{ background: 'rgba(59, 130, 246, 0.2)', color: '#3b82f6' }} />
                  <Chip label={`Country: ${location.country}`} sx={{ background: 'rgba(59, 130, 246, 0.2)', color: '#3b82f6' }} />
                </Box>
              </Box>
              {location.coordinates && (
                <Box sx={{ textAlign: 'right' }}>
                  <Typography variant="caption" color="text.secondary" display="block">
                    Coordinates
                  </Typography>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                    {location.coordinates.lat.toFixed(4)}, {location.coordinates.lng.toFixed(4)}
                  </Typography>
                </Box>
              )}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Service Status Cards */}
      <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
        Service Status
      </Typography>
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {services.map((service) => (
          <Grid item xs={12} md={6} lg={4} key={service.name}>
            <Card
              sx={{
                background: `linear-gradient(135deg, ${getStatusColor(service.status)}15 0%, ${getStatusColor(service.status)}25 100%)`,
                border: `1px solid ${getStatusColor(service.status)}40`,
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                      {service.name}
                    </Typography>
                    <Chip
                      icon={getStatusIcon(service.status)}
                      label={service.status}
                      size="small"
                      sx={{
                        background: getStatusColor(service.status),
                        color: 'white',
                        fontWeight: 600,
                      }}
                    />
                  </Box>
                  <Tooltip title="Restart Service">
                    <IconButton
                      size="small"
                      onClick={() => handleRestartService(service.name)}
                      disabled={restarting === service.name}
                      sx={{
                        background: 'rgba(102, 126, 234, 0.1)',
                        '&:hover': { background: 'rgba(102, 126, 234, 0.2)' },
                      }}
                    >
                      {restarting === service.name ? (
                        <CircularProgress size={20} />
                      ) : (
                        <RestartIcon fontSize="small" />
                      )}
                    </IconButton>
                  </Tooltip>
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {service.message}
                </Typography>
                {service.last_check && (
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                    Last checked: {new Date(service.last_check).toLocaleTimeString()}
                  </Typography>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* System Metrics */}
      <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
        System Metrics
      </Typography>
      <Grid container spacing={3}>
        {/* Orchestrator VM */}
        {orchestratorMetrics && (
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <ComputerIcon sx={{ fontSize: 40, color: '#667eea' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Orchestrator VM
                </Typography>
              </Box>
              
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">CPU Usage</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600, color: getMetricColor(orchestratorMetrics.cpu.percent) }}>
                    {orchestratorMetrics.cpu.percent.toFixed(1)}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={orchestratorMetrics.cpu.percent}
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    '& .MuiLinearProgress-bar': {
                      background: `linear-gradient(90deg, ${getMetricColor(orchestratorMetrics.cpu.percent)}, ${getMetricColor(orchestratorMetrics.cpu.percent)}dd)`,
                      borderRadius: 4,
                    },
                  }}
                />
                <Typography variant="caption" color="text.secondary">
                  {orchestratorMetrics.cpu.count} cores
                </Typography>
              </Box>

              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">Memory Usage</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600, color: getMetricColor(orchestratorMetrics.memory.percent) }}>
                    {orchestratorMetrics.memory.percent.toFixed(1)}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={orchestratorMetrics.memory.percent}
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    '& .MuiLinearProgress-bar': {
                      background: `linear-gradient(90deg, ${getMetricColor(orchestratorMetrics.memory.percent)}, ${getMetricColor(orchestratorMetrics.memory.percent)}dd)`,
                      borderRadius: 4,
                    },
                  }}
                />
                <Typography variant="caption" color="text.secondary">
                  {orchestratorMetrics.memory.used_mb.toFixed(0)} MB / {orchestratorMetrics.memory.total_mb.toFixed(0)} MB
                </Typography>
              </Box>

              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">Disk Usage</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600, color: getMetricColor(orchestratorMetrics.disk.percent) }}>
                    {orchestratorMetrics.disk.percent.toFixed(1)}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={orchestratorMetrics.disk.percent}
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    '& .MuiLinearProgress-bar': {
                      background: `linear-gradient(90deg, ${getMetricColor(orchestratorMetrics.disk.percent)}, ${getMetricColor(orchestratorMetrics.disk.percent)}dd)`,
                      borderRadius: 4,
                    },
                  }}
                />
                <Typography variant="caption" color="text.secondary">
                  {orchestratorMetrics.disk.used_gb.toFixed(2)} GB / {orchestratorMetrics.disk.total_gb.toFixed(2)} GB
                </Typography>
              </Box>
            </Paper>
          </Grid>
        )}

        {/* LLM VM */}
        {llmMetrics && (
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <DnsIcon sx={{ fontSize: 40, color: '#764ba2' }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  LLM VM
                </Typography>
              </Box>
              
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">CPU Usage</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600, color: getMetricColor(llmMetrics.cpu.percent) }}>
                    {llmMetrics.cpu.percent.toFixed(1)}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={llmMetrics.cpu.percent}
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: 'rgba(118, 75, 162, 0.1)',
                    '& .MuiLinearProgress-bar': {
                      background: `linear-gradient(90deg, ${getMetricColor(llmMetrics.cpu.percent)}, ${getMetricColor(llmMetrics.cpu.percent)}dd)`,
                      borderRadius: 4,
                    },
                  }}
                />
                <Typography variant="caption" color="text.secondary">
                  {llmMetrics.cpu.count} cores
                </Typography>
              </Box>

              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">Memory Usage</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600, color: getMetricColor(llmMetrics.memory.percent) }}>
                    {llmMetrics.memory.percent.toFixed(1)}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={llmMetrics.memory.percent}
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: 'rgba(118, 75, 162, 0.1)',
                    '& .MuiLinearProgress-bar': {
                      background: `linear-gradient(90deg, ${getMetricColor(llmMetrics.memory.percent)}, ${getMetricColor(llmMetrics.memory.percent)}dd)`,
                      borderRadius: 4,
                    },
                  }}
                />
                <Typography variant="caption" color="text.secondary">
                  {llmMetrics.memory.used_mb.toFixed(0)} MB / {llmMetrics.memory.total_mb.toFixed(0)} MB
                </Typography>
              </Box>

              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2" color="text.secondary">Disk Usage</Typography>
                  <Typography variant="body2" sx={{ fontWeight: 600, color: getMetricColor(llmMetrics.disk.percent) }}>
                    {llmMetrics.disk.percent.toFixed(1)}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={llmMetrics.disk.percent}
                  sx={{
                    height: 8,
                    borderRadius: 4,
                    backgroundColor: 'rgba(118, 75, 162, 0.1)',
                    '& .MuiLinearProgress-bar': {
                      background: `linear-gradient(90deg, ${getMetricColor(llmMetrics.disk.percent)}, ${getMetricColor(llmMetrics.disk.percent)}dd)`,
                      borderRadius: 4,
                    },
                  }}
                />
                <Typography variant="caption" color="text.secondary">
                  {llmMetrics.disk.used_gb.toFixed(2)} GB / {llmMetrics.disk.total_gb.toFixed(2)} GB
                </Typography>
              </Box>
            </Paper>
          </Grid>
        )}

        {/* Summary Statistics */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <CheckCircleIcon sx={{ fontSize: 40, color: '#10b981' }} />
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#10b981' }}>
                    {services.filter(s => s.status === 'UP').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Services Online
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
                <WarningIcon sx={{ fontSize: 40, color: '#f59e0b' }} />
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#f59e0b' }}>
                    {services.filter(s => s.status === 'DEGRADED').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Services Degraded
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
                <ErrorIcon sx={{ fontSize: 40, color: '#ef4444' }} />
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#ef4444' }}>
                    {services.filter(s => s.status === 'DOWN').length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Services Down
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

export default MonitoringServices;
