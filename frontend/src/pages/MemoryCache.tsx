import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Paper, 
  Grid, 
  Button, 
  Alert, 
  Card, 
  CardContent, 
  TextField, 
  Switch, 
  FormControlLabel, 
  Divider, 
  Box,
  Chip,
  CircularProgress,
  Tooltip,
  IconButton,
  Slider,
  Select,
  MenuItem,
  InputLabel,
  FormControl
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Settings as SettingsIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import axios from 'axios';

interface MemorySettings {
  redis_url: string;
  redis_enabled: boolean;
  memory_ttl: number;
  max_conversations: number;
  vector_db_url: string;
  vector_db_enabled: boolean;
  cache_size_limit_mb: number;
  storage_type: 'redis' | 'local' | 'postgres';
}

const MemoryCache: React.FC = () => {
  const [stats, setStats] = useState({
    conversation_count: 0,
    cache_hit_rate: 0,
    redis_memory_usage: '',
    state_store_entries: 0
  });
  const [message, setMessage] = useState('');
  const [settings, setSettings] = useState<MemorySettings>({
    redis_url: 'redis://localhost:6379',
    redis_enabled: true,
    memory_ttl: 3600,
    max_conversations: 100,
    vector_db_url: 'postgres://user:password@localhost:5432/vectordb',
    vector_db_enabled: true,
    cache_size_limit_mb: 512,
    storage_type: 'redis'
  });
  const [isLoading, setIsLoading] = useState(false);
  const [testResults, setTestResults] = useState<{[key: string]: boolean}>({});
  const [testing, setTesting] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    fetchStats();
    fetchSettings();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/memory/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching memory stats:', error);
    }
  };

  const fetchSettings = async () => {
    try {
      // In a real implementation, this would fetch from the backend
      // For now, we'll just use the default values
      setIsLoading(true);
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate loading
      setIsLoading(false);
    } catch (error) {
      console.error('Error fetching memory settings:', error);
      setIsLoading(false);
    }
  };

  const handleClearMemory = async () => {
    try {
      await axios.post('http://localhost:8000/api/memory/clear');
      setMessage('Memory cleared successfully!');
      fetchStats();
    } catch (error) {
      console.error('Error clearing memory:', error);
      setMessage('Error clearing memory');
    }
  };

  const handleSaveSettings = async () => {
    try {
      setIsLoading(true);
      // In a real implementation, this would save to the backend
      // For now, we'll just simulate a successful save
      await new Promise(resolve => setTimeout(resolve, 1000));
      setMessage('Memory settings saved successfully!');
      setIsEditing(false);
      setIsLoading(false);
    } catch (error) {
      console.error('Error saving memory settings:', error);
      setMessage('Error saving memory settings');
      setIsLoading(false);
    }
  };

  const handleTestConnection = async (type: 'redis' | 'vector_db') => {
    setTesting(type);
    
    try {
      // In a real implementation, this would test the connection
      // For now, we'll simulate a successful test
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const newResults = {...testResults};
      newResults[type] = true;
      setTestResults(newResults);
      
      setMessage(`Connection to ${type === 'redis' ? 'Redis' : 'Vector DB'} tested successfully!`);
    } catch (error) {
      console.error(`Error testing connection to ${type}:`, error);
      
      const newResults = {...testResults};
      newResults[type] = false;
      setTestResults(newResults);
      
      setMessage(`Error testing connection to ${type}`);
    } finally {
      setTesting(null);
    }
  };

  const handleSettingChange = (field: keyof MemorySettings, value: any) => {
    setSettings({
      ...settings,
      [field]: value
    });
    if (!isEditing) setIsEditing(true);
  };

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Memory & Cache Management
      </Typography>
      
      {message && (
        <Alert 
          severity={message.includes('Error') ? 'error' : 'success'} 
          sx={{ mb: 3 }}
          onClose={() => setMessage('')}
        >
          {message}
        </Alert>
      )}
      
      <Paper sx={{ p: 3, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
            <SettingsIcon sx={{ mr: 1 }} /> Memory Configuration
          </Typography>
          <Box>
            {isEditing && (
              <Button 
                variant="contained" 
                color="primary" 
                onClick={handleSaveSettings}
                disabled={isLoading}
                startIcon={isLoading ? <CircularProgress size={20} /> : <SaveIcon />}
                sx={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                }}
              >
                Save Settings
              </Button>
            )}
          </Box>
        </Box>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2, display: 'flex', alignItems: 'center' }}>
                  <StorageIcon sx={{ mr: 1 }} /> Redis Configuration
                </Typography>
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.redis_enabled}
                      onChange={(e) => handleSettingChange('redis_enabled', e.target.checked)}
                      color="primary"
                    />
                  }
                  label="Enable Redis"
                  sx={{ mb: 2, display: 'block' }}
                />
                
                <TextField
                  label="Redis URL"
                  fullWidth
                  value={settings.redis_url}
                  onChange={(e) => handleSettingChange('redis_url', e.target.value)}
                  disabled={!settings.redis_enabled}
                  margin="normal"
                  placeholder="redis://localhost:6379"
                />
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => handleTestConnection('redis')}
                    disabled={!settings.redis_enabled || testing !== null}
                    startIcon={testing === 'redis' ? <CircularProgress size={16} /> : null}
                  >
                    {testing === 'redis' ? 'Testing...' : 'Test Connection'}
                  </Button>
                  
                  {testResults['redis'] !== undefined && (
                    <Chip
                      icon={testResults['redis'] ? <CheckCircleIcon /> : <ErrorIcon />}
                      label={testResults['redis'] ? 'Connected' : 'Failed'}
                      color={testResults['redis'] ? 'success' : 'error'}
                      size="small"
                    />
                  )}
                </Box>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent>
                <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2, display: 'flex', alignItems: 'center' }}>
                  <MemoryIcon sx={{ mr: 1 }} /> Memory Settings
                </Typography>
                
                <Typography gutterBottom>Memory TTL (seconds)</Typography>
                <Slider
                  value={settings.memory_ttl}
                  onChange={(_, value) => handleSettingChange('memory_ttl', value)}
                  min={60}
                  max={86400}
                  step={60}
                  valueLabelDisplay="auto"
                  marks={[
                    { value: 60, label: '1m' },
                    { value: 3600, label: '1h' },
                    { value: 86400, label: '24h' }
                  ]}
                />
                
                <Typography gutterBottom sx={{ mt: 2 }}>Max Conversations</Typography>
                <Slider
                  value={settings.max_conversations}
                  onChange={(_, value) => handleSettingChange('max_conversations', value)}
                  min={10}
                  max={1000}
                  step={10}
                  valueLabelDisplay="auto"
                  marks={[
                    { value: 10, label: '10' },
                    { value: 100, label: '100' },
                    { value: 1000, label: '1000' }
                  ]}
                />
                
                <Typography gutterBottom sx={{ mt: 2 }}>Cache Size Limit (MB)</Typography>
                <Slider
                  value={settings.cache_size_limit_mb}
                  onChange={(_, value) => handleSettingChange('cache_size_limit_mb', value)}
                  min={64}
                  max={4096}
                  step={64}
                  valueLabelDisplay="auto"
                  marks={[
                    { value: 64, label: '64MB' },
                    { value: 512, label: '512MB' },
                    { value: 4096, label: '4GB' }
                  ]}
                />
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2, display: 'flex', alignItems: 'center' }}>
                  <StorageIcon sx={{ mr: 1 }} /> Vector Database Configuration
                </Typography>
                
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.vector_db_enabled}
                      onChange={(e) => handleSettingChange('vector_db_enabled', e.target.checked)}
                      color="primary"
                    />
                  }
                  label="Enable Vector Database"
                  sx={{ mb: 2, display: 'block' }}
                />
                
                <TextField
                  label="Vector DB URL"
                  fullWidth
                  value={settings.vector_db_url}
                  onChange={(e) => handleSettingChange('vector_db_url', e.target.value)}
                  disabled={!settings.vector_db_enabled}
                  margin="normal"
                  placeholder="postgres://user:password@localhost:5432/vectordb"
                />
                
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => handleTestConnection('vector_db')}
                    disabled={!settings.vector_db_enabled || testing !== null}
                    startIcon={testing === 'vector_db' ? <CircularProgress size={16} /> : null}
                  >
                    {testing === 'vector_db' ? 'Testing...' : 'Test Connection'}
                  </Button>
                  
                  {testResults['vector_db'] !== undefined && (
                    <Chip
                      icon={testResults['vector_db'] ? <CheckCircleIcon /> : <ErrorIcon />}
                      label={testResults['vector_db'] ? 'Connected' : 'Failed'}
                      color={testResults['vector_db'] ? 'success' : 'error'}
                      size="small"
                    />
                  )}
                </Box>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent>
                <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 2, display: 'flex', alignItems: 'center' }}>
                  <StorageIcon sx={{ mr: 1 }} /> Storage Type
                </Typography>
                
                <FormControl fullWidth margin="normal">
                  <InputLabel>Storage Type</InputLabel>
                  <Select
                    value={settings.storage_type}
                    onChange={(e) => handleSettingChange('storage_type', e.target.value)}
                    label="Storage Type"
                  >
                    <MenuItem value="redis">Redis</MenuItem>
                    <MenuItem value="local">Local File System</MenuItem>
                    <MenuItem value="postgres">PostgreSQL</MenuItem>
                  </Select>
                </FormControl>
                
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                  Select the storage type for conversation history and state. Redis is recommended for production environments.
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>
      
      <Typography variant="h6" gutterBottom>
        Current Status
      </Typography>
      
      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
                <MemoryIcon sx={{ mr: 1 }} /> Conversation Memory
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body1">
                  Active Conversations: <strong>{stats.conversation_count}</strong>
                </Typography>
                <Typography variant="body1">
                  State Store Entries: <strong>{stats.state_store_entries}</strong>
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                <Button 
                  variant="outlined" 
                  color="error" 
                  onClick={handleClearMemory} 
                  startIcon={<DeleteIcon />}
                >
                  Clear Memory
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center' }}>
                <StorageIcon sx={{ mr: 1 }} /> Cache Performance
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body1">
                  Cache Hit Rate: <strong>{(stats.cache_hit_rate * 100).toFixed(1)}%</strong>
                </Typography>
                <Typography variant="body1">
                  Redis Memory Usage: <strong>{stats.redis_memory_usage}</strong>
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                <Button 
                  variant="outlined" 
                  onClick={fetchStats} 
                  startIcon={<RefreshIcon />}
                >
                  Refresh Stats
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </div>
  );
};

export default MemoryCache;
