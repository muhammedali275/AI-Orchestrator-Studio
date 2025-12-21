import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Button, 
  List, 
  ListItem, 
  ListItemText, 
  Paper, 
  Divider, 
  CircularProgress, 
  Chip, 
  Box, 
  Alert,
  Grid,
  Card,
  CardContent,
  LinearProgress,
  Tabs,
  Tab,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Badge
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Update as UpdateIcon,
  Done as DoneIcon,
  Refresh as RefreshIcon,
  CloudDownload as CloudDownloadIcon,
  Code as CodeIcon,
  Language as LanguageIcon,
  Memory as MemoryIcon,
  ExpandMore as ExpandMoreIcon,
  Visibility as VisibilityIcon,
  Search as SearchIcon,
  FilterList as FilterListIcon
} from '@mui/icons-material';
import axios from 'axios';

interface ComponentVersion {
  name: string;
  current_version: string;
  latest_version?: string;
  status: 'up-to-date' | 'update-available' | 'major-update' | 'unknown' | 'updating';
  type: 'backend' | 'frontend' | 'ollama' | 'system';
  update_command?: string;
  changelog_url?: string;
}

interface UpgradeStatus {
  component: string;
  status: 'running' | 'completed' | 'failed';
  progress: number;
  message: string;
  logs: string[];
}

const Upgrades: React.FC = () => {
  const [components, setComponents] = useState<{ [key: string]: ComponentVersion[] }>({
    backend: [],
    frontend: [],
    ollama: [],
    system: []
  });
  const [summary, setSummary] = useState({
    total: 0,
    up_to_date: 0,
    updates_available: 0,
    unknown: 0
  });
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [upgradeStatuses, setUpgradeStatuses] = useState<{ [key: string]: UpgradeStatus }>({});
  const [logDialog, setLogDialog] = useState<{ open: boolean; component: string; logs: string[] }>({
    open: false,
    component: '',
    logs: []
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [connectivityStatus, setConnectivityStatus] = useState<any>(null);

  useEffect(() => {
    checkUpdates();
  }, []);

  const testConnectivity = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/upgrades/test-connectivity');
      setConnectivityStatus(response.data);
      
      const pypiOk = response.data.pypi?.status === 'connected';
      const npmOk = response.data.npm?.status === 'connected';
      
      if (pypiOk && npmOk) {
        setMessage('✓ Internet connectivity OK - Both PyPI and npm registries accessible');
      } else if (pypiOk) {
        setMessage('⚠ Partial connectivity - PyPI OK, npm registry failed');
      } else if (npmOk) {
        setMessage('⚠ Partial connectivity - npm OK, PyPI registry failed');
      } else {
        setMessage('✗ Internet connectivity issues - Cannot reach PyPI or npm registries');
      }
    } catch (error: any) {
      setMessage(`Connectivity test failed: ${error.message}`);
    }
  };

  const checkUpdates = async () => {
    setLoading(true);
    setMessage('');
    try {
      const response = await axios.get('http://localhost:8000/api/upgrades/check');
      if (response.data.success) {
        setComponents(response.data.components);
        setSummary(response.data.summary);
        setMessage(`✓ Update check completed - Found ${response.data.summary.total} components (${response.data.summary.updates_available} updates available)`);
      }
    } catch (error: any) {
      console.error('Error checking updates:', error);
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (component: ComponentVersion) => {
    const statusKey = `${component.type}:${component.name}`;
    try {
      const response = await axios.post('http://localhost:8000/api/upgrades/upgrade', {
        name: component.name,
        type: component.type,
        target_version: component.latest_version
      });
      
      if (response.data.success) {
        setMessage(`Upgrade started for ${component.name}`);
        // Start polling for status
        pollUpgradeStatus(statusKey);
      }
    } catch (error: any) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  const pollUpgradeStatus = async (statusKey: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`http://localhost:8000/api/upgrades/status/${encodeURIComponent(statusKey)}`);
        const status = response.data;
        
        setUpgradeStatuses(prev => ({ ...prev, [statusKey]: status }));
        
        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(interval);
          if (status.status === 'completed') {
            setMessage(`Successfully upgraded ${status.component}`);
            // Refresh component list
            checkUpdates();
          } else {
            setMessage(`Failed to upgrade ${status.component}: ${status.message}`);
          }
        }
      } catch (error) {
        clearInterval(interval);
      }
    }, 2000);
  };

  const showLogs = (component: string, logs: string[]) => {
    setLogDialog({ open: true, component, logs });
  };

  const getStatusChip = (component: ComponentVersion, statusKey: string) => {
    const upgradeStatus = upgradeStatuses[statusKey];
    
    if (upgradeStatus?.status === 'running') {
      return <Chip icon={<CircularProgress size={16} />} label={`${upgradeStatus.progress}%`} color="primary" size="small" />;
    }
    
    switch (component.status) {
      case 'up-to-date':
        return <Chip icon={<CheckCircleIcon />} label="Up to date" color="success" size="small" />;
      case 'update-available':
        return <Chip icon={<InfoIcon />} label="Update available" color="info" size="small" />;
      case 'major-update':
        return <Chip icon={<WarningIcon />} label="Major update" color="warning" size="small" />;
      case 'unknown':
        return <Chip label="Unknown" size="small" />;
      default:
        return null;
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'backend':
        return <CodeIcon />;
      case 'frontend':
        return <LanguageIcon />;
      case 'ollama':
        return <MemoryIcon />;
      case 'system':
        return <CloudDownloadIcon />;
      default:
        return <InfoIcon />;
    }
  };

  const renderComponentList = (type: string, items: ComponentVersion[]) => {
    // Apply filters
    let filteredItems = items.filter(component => {
      const matchesSearch = component.name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = statusFilter === 'all' || component.status === statusFilter;
      return matchesSearch && matchesStatus;
    });

    if (filteredItems.length === 0) {
      return (
        <Alert severity="info" sx={{ mt: 2 }}>
          {items.length === 0 
            ? `No ${type} components found` 
            : 'No components match the current filters'}
        </Alert>
      );
    }

    return (
      <List>
        {filteredItems.map((component, index) => {
          const statusKey = `${component.type}:${component.name}`;
          const upgradeStatus = upgradeStatuses[statusKey];
          
          return (
            <ListItem key={index} divider>
              <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
                {getTypeIcon(component.type)}
              </Box>
              <ListItemText 
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body1" sx={{ fontWeight: 600 }}>
                      {component.name}
                    </Typography>
                    {component.changelog_url && (
                      <Tooltip title="View changelog">
                        <IconButton
                          size="small"
                          onClick={() => window.open(component.changelog_url, '_blank')}
                        >
                          <InfoIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    )}
                  </Box>
                }
                secondary={
                  <Box>
                    <Typography variant="caption" display="block">
                      Current: {component.current_version}
                      {component.latest_version && ` → Latest: ${component.latest_version}`}
                    </Typography>
                    {component.update_command && (
                      <Typography variant="caption" display="block" sx={{ fontFamily: 'monospace', color: 'text.secondary', mt: 0.5 }}>
                        {component.update_command}
                      </Typography>
                    )}
                    {upgradeStatus?.message && (
                      <Typography variant="caption" display="block" color="primary" sx={{ mt: 0.5 }}>
                        {upgradeStatus.message}
                      </Typography>
                    )}
                  </Box>
                }
              />
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                {getStatusChip(component, statusKey)}
                {upgradeStatus?.logs && upgradeStatus.logs.length > 0 && (
                  <Tooltip title="View logs">
                    <IconButton
                      size="small"
                      onClick={() => showLogs(component.name, upgradeStatus.logs)}
                    >
                      <VisibilityIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                )}
                {component.status !== 'up-to-date' && component.status !== 'unknown' && (
                  <Button 
                    variant="outlined" 
                    size="small"
                    disabled={upgradeStatus?.status === 'running'}
                    onClick={() => handleUpgrade(component)}
                    startIcon={<UpdateIcon />}
                  >
                    {upgradeStatus?.status === 'running' ? 'Updating...' : 'Update'}
                  </Button>
                )}
              </Box>
            </ListItem>
          );
        })}
      </List>
    );
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
            Upgrades & Dependencies
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage updates for backend packages, frontend dependencies, Ollama models, and system components
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Tooltip title="Test internet connectivity to PyPI and npm">
            <Button
              variant="outlined"
              onClick={testConnectivity}
              disabled={loading}
              startIcon={<CloudDownloadIcon />}
              size="small"
            >
              Test Connectivity
            </Button>
          </Tooltip>
          <Tooltip title="Check for updates">
            <IconButton
              onClick={checkUpdates}
              disabled={loading}
              sx={{
                background: 'rgba(102, 126, 234, 0.1)',
                '&:hover': { background: 'rgba(102, 126, 234, 0.2)' },
              }}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>
      
      {/* Connectivity Status */}
      {connectivityStatus && (
        <Alert 
          severity={
            connectivityStatus.pypi?.status === 'connected' && connectivityStatus.npm?.status === 'connected' 
              ? 'success' 
              : connectivityStatus.pypi?.status === 'connected' || connectivityStatus.npm?.status === 'connected'
              ? 'warning'
              : 'error'
          } 
          sx={{ mb: 2 }}
          onClose={() => setConnectivityStatus(null)}
        >
          <Box>
            <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>Internet Connectivity Test Results:</Typography>
            <Typography variant="caption" display="block">
              PyPI (Python): {connectivityStatus.pypi?.status === 'connected' 
                ? `✓ Connected (${connectivityStatus.pypi?.latency_ms}ms)` 
                : `✗ Failed - ${connectivityStatus.pypi?.error}`}
            </Typography>
            <Typography variant="caption" display="block">
              npm Registry: {connectivityStatus.npm?.status === 'connected' 
                ? `✓ Connected (${connectivityStatus.npm?.latency_ms}ms)` 
                : `✗ Failed - ${connectivityStatus.npm?.error}`}
            </Typography>
          </Box>
        </Alert>
      )}
      
      {/* Messages */}
      {message && (
        <Alert 
          severity={message.includes('Error') ? 'error' : message.includes('successfully') || message.includes('completed') ? 'success' : 'info'} 
          sx={{ mb: 3 }}
          onClose={() => setMessage('')}
        >
          {message}
        </Alert>
      )}
      
      {/* Loading */}
      {loading && (
        <Box sx={{ mb: 3 }}>
          <LinearProgress />
          <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
            Checking for updates...
          </Typography>
        </Box>
      )}
      
      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <InfoIcon sx={{ fontSize: 40, color: '#667eea' }} />
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#667eea' }}>
                    {summary.total}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Components
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <CheckCircleIcon sx={{ fontSize: 40, color: '#10b981' }} />
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#10b981' }}>
                    {summary.up_to_date}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Up to Date
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <WarningIcon sx={{ fontSize: 40, color: '#f59e0b' }} />
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#f59e0b' }}>
                    {summary.updates_available}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Updates Available
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <InfoIcon sx={{ fontSize: 40, color: '#6b7280' }} />
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#6b7280' }}>
                    {summary.unknown}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Unknown Status
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Component Tabs */}
      <Paper sx={{ mb: 3 }}>
        {/* Filters */}
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider', display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <TextField
            placeholder="Search components..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            size="small"
            sx={{ flexGrow: 1, minWidth: 200 }}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
          <FormControl size="small" sx={{ minWidth: 180 }}>
            <InputLabel>Filter by Status</InputLabel>
            <Select
              value={statusFilter}
              label="Filter by Status"
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <MenuItem value="all">All Status</MenuItem>
              <MenuItem value="up-to-date">Up to date</MenuItem>
              <MenuItem value="update-available">Update available</MenuItem>
              <MenuItem value="major-update">Major update</MenuItem>
              <MenuItem value="unknown">Unknown</MenuItem>
            </Select>
          </FormControl>
          <Tooltip title="Clear filters">
            <Button 
              variant="outlined" 
              size="small"
              onClick={() => {
                setSearchTerm('');
                setStatusFilter('all');
              }}
            >
              Clear
            </Button>
          </Tooltip>
        </Box>
        
        <Tabs 
          value={activeTab} 
          onChange={(e, newValue) => setActiveTab(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab 
            icon={<CodeIcon />} 
            label={
              <Badge 
                badgeContent={components.backend?.filter(c => c.status === 'update-available' || c.status === 'major-update').length || 0} 
                color="warning"
              >
                <span>Backend ({components.backend?.length || 0})</span>
              </Badge>
            } 
            iconPosition="start"
          />
          <Tab 
            icon={<LanguageIcon />} 
            label={
              <Badge 
                badgeContent={components.frontend?.filter(c => c.status === 'update-available' || c.status === 'major-update').length || 0} 
                color="warning"
              >
                <span>Frontend ({components.frontend?.length || 0})</span>
              </Badge>
            } 
            iconPosition="start"
          />
          <Tab 
            icon={<MemoryIcon />} 
            label={
              <Badge 
                badgeContent={components.ollama?.filter(c => c.status === 'update-available' || c.status === 'major-update').length || 0} 
                color="warning"
              >
                <span>Ollama Models ({components.ollama?.length || 0})</span>
              </Badge>
            } 
            iconPosition="start"
          />
          <Tab 
            icon={<CloudDownloadIcon />} 
            label={
              <Badge 
                badgeContent={components.system?.filter(c => c.status === 'update-available' || c.status === 'major-update').length || 0} 
                color="warning"
              >
                <span>System ({components.system?.length || 0})</span>
              </Badge>
            } 
            iconPosition="start"
          />
        </Tabs>
        
        <Box sx={{ p: 2 }}>
          {activeTab === 0 && renderComponentList('backend', components.backend || [])}
          {activeTab === 1 && renderComponentList('frontend', components.frontend || [])}
          {activeTab === 2 && renderComponentList('ollama', components.ollama || [])}
          {activeTab === 3 && renderComponentList('system', components.system || [])}
        </Box>
      </Paper>

      {/* Logs Dialog */}
      <Dialog
        open={logDialog.open}
        onClose={() => setLogDialog({ open: false, component: '', logs: [] })}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Upgrade Logs: {logDialog.component}
        </DialogTitle>
        <DialogContent>
          <Paper
            sx={{
              p: 2,
              bgcolor: '#1e1e1e',
              color: '#d4d4d4',
              fontFamily: 'monospace',
              fontSize: '0.875rem',
              maxHeight: '400px',
              overflow: 'auto'
            }}
          >
            {logDialog.logs.map((log, index) => (
              <Box key={index} sx={{ mb: 1, whiteSpace: 'pre-wrap' }}>
                {log}
              </Box>
            ))}
          </Paper>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLogDialog({ open: false, component: '', logs: [] })}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Upgrades;
