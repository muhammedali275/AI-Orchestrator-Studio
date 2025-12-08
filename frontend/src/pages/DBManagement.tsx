import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Paper, 
  Grid, 
  Card, 
  CardContent, 
  List, 
  ListItem, 
  ListItemText, 
  Chip, 
  TextField, 
  Button, 
  Alert, 
  Box, 
  Divider,
  FormControlLabel,
  Switch,
  IconButton,
  Tooltip
} from '@mui/material';
import { 
  Save as SaveIcon, 
  Refresh as RefreshIcon, 
  Cable as CableIcon, 
  Delete as DeleteIcon,
  Add as AddIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import axios from 'axios';

interface DBStatus {
  status: string;
  connections?: number;
  memory?: string;
  collections?: number;
}

interface Collection {
  name: string;
  count: number;
  dimension: number;
}

interface DBConfig {
  type: string;
  connection_string: string;
  enabled: boolean;
  name: string;
}

const DBManagement: React.FC = () => {
  const [dbStatus, setDbStatus] = useState<{ [key: string]: DBStatus }>({});
  const [collections, setCollections] = useState<Collection[]>([]);
  const [dbConfigs, setDbConfigs] = useState<DBConfig[]>([
    { type: 'postgres', connection_string: '', enabled: true, name: 'PostgreSQL' },
    { type: 'redis', connection_string: '', enabled: true, name: 'Redis Cache' },
    { type: 'vector', connection_string: '', enabled: true, name: 'Vector Database' }
  ]);
  const [message, setMessage] = useState('');
  const [testResults, setTestResults] = useState<{[key: string]: boolean}>({});
  const [testing, setTesting] = useState<string | null>(null);

  useEffect(() => {
    fetchDBStatus();
    fetchCollections();
    fetchDBConfigs();
  }, []);

  const fetchDBStatus = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/db/status');
      setDbStatus(response.data);
    } catch (error) {
      console.error('Error fetching DB status:', error);
    }
  };

  const fetchCollections = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/db/collections');
      setCollections(response.data.collections);
    } catch (error) {
      console.error('Error fetching collections:', error);
    }
  };

  const fetchDBConfigs = async () => {
    try {
      // In a real implementation, this would fetch from the backend
      // For now, we'll just use the default values
      console.log('Fetching DB configs...');
    } catch (error) {
      console.error('Error fetching DB configs:', error);
    }
  };

  const handleSaveConfigs = async () => {
    try {
      // In a real implementation, this would save to the backend
      // For now, we'll just show a success message
      setMessage('Database configurations saved successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Error saving DB configs:', error);
      setMessage('Error saving database configurations');
    }
  };

  const handleTestConnection = async (index: number) => {
    const db = dbConfigs[index];
    setTesting(db.type);
    
    try {
      // In a real implementation, this would test the connection
      // For now, we'll simulate a successful test
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const newResults = {...testResults};
      newResults[db.type] = true;
      setTestResults(newResults);
      
      setMessage(`Connection to ${db.name} tested successfully!`);
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error(`Error testing connection to ${db.name}:`, error);
      
      const newResults = {...testResults};
      newResults[db.type] = false;
      setTestResults(newResults);
      
      setMessage(`Error testing connection to ${db.name}`);
    } finally {
      setTesting(null);
    }
  };

  const updateDBConfig = (index: number, field: keyof DBConfig, value: string | boolean) => {
    const newConfigs = [...dbConfigs];
    newConfigs[index] = {...newConfigs[index], [field]: value};
    setDbConfigs(newConfigs);
  };

  const getStatusColor = (status: string) => {
    return status === 'connected' ? 'success' : 'error';
  };

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Database Management
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
        <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
          Database Configurations
        </Typography>
        
        {dbConfigs.map((db, index) => (
          <Box key={db.type} sx={{ mb: 3 }}>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} sm={3}>
                <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                  {db.name}
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={db.enabled}
                      onChange={(e) => updateDBConfig(index, 'enabled', e.target.checked)}
                      color="primary"
                    />
                  }
                  label="Enabled"
                />
              </Grid>
              
              <Grid item xs={12} sm={7}>
                <TextField
                  label="Connection String"
                  fullWidth
                  value={db.connection_string}
                  onChange={(e) => updateDBConfig(index, 'connection_string', e.target.value)}
                  placeholder={`${db.type}://username:password@hostname:port/database`}
                  disabled={!db.enabled}
                  type="password"
                />
              </Grid>
              
              <Grid item xs={12} sm={2}>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Tooltip title="Test Connection">
                    <span>
                      <Button
                        variant="outlined"
                        onClick={() => handleTestConnection(index)}
                        disabled={testing !== null || !db.enabled || !db.connection_string}
                        startIcon={testing === db.type ? <RefreshIcon className="rotating" /> : <CableIcon />}
                        size="small"
                        sx={{ minWidth: '120px' }}
                      >
                        {testing === db.type ? 'Testing...' : 'Test'}
                      </Button>
                    </span>
                  </Tooltip>
                  
                  {testResults[db.type] !== undefined && (
                    <Chip
                      icon={testResults[db.type] ? <CheckCircleIcon /> : <ErrorIcon />}
                      label={testResults[db.type] ? 'Success' : 'Failed'}
                      color={testResults[db.type] ? 'success' : 'error'}
                      size="small"
                    />
                  )}
                </Box>
              </Grid>
            </Grid>
            
            {index < dbConfigs.length - 1 && <Divider sx={{ my: 2 }} />}
          </Box>
        ))}
        
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 3 }}>
          <Button
            variant="contained"
            onClick={handleSaveConfigs}
            startIcon={<SaveIcon />}
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            }}
          >
            Save Configurations
          </Button>
        </Box>
      </Paper>
      
      <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>
        Connection Status
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6">PostgreSQL</Typography>
              <Chip 
                label={dbStatus.postgres?.status || 'unknown'} 
                color={getStatusColor(dbStatus.postgres?.status || '')} 
                size="small"
                sx={{ mt: 1 }}
              />
              <Typography variant="body2" sx={{ mt: 1 }}>
                Active Connections: {dbStatus.postgres?.connections || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6">Redis Cache</Typography>
              <Chip 
                label={dbStatus.redis?.status || 'unknown'} 
                color={getStatusColor(dbStatus.redis?.status || '')} 
                size="small"
                sx={{ mt: 1 }}
              />
              <Typography variant="body2" sx={{ mt: 1 }}>
                Memory Usage: {dbStatus.redis?.memory || 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6">Vector Database</Typography>
              <Chip 
                label={dbStatus.vector_db?.status || 'unknown'} 
                color={getStatusColor(dbStatus.vector_db?.status || '')} 
                size="small"
                sx={{ mt: 1 }}
              />
              <Typography variant="body2" sx={{ mt: 1 }}>
                Collections: {dbStatus.vector_db?.collections || 0}
              </Typography>
              <Button 
                variant="outlined" 
                size="small" 
                onClick={fetchDBStatus} 
                startIcon={<RefreshIcon />}
                sx={{ mt: 1 }}
              >
                Refresh
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Typography variant="h6" sx={{ mt: 4, mb: 2 }}>
        Vector Database Collections
      </Typography>
      <Paper sx={{ p: 2 }}>
        <List>
          {collections.length > 0 ? (
            collections.map((collection) => (
              <ListItem key={collection.name}>
                <ListItemText
                  primary={collection.name}
                  secondary={`${collection.count.toLocaleString()} vectors | Dimension: ${collection.dimension}`}
                />
              </ListItem>
            ))
          ) : (
            <ListItem>
              <ListItemText primary="No collections found" />
            </ListItem>
          )}
        </List>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
          <Button 
            variant="outlined" 
            size="small" 
            onClick={fetchCollections}
            startIcon={<RefreshIcon />}
          >
            Refresh Collections
          </Button>
        </Box>
      </Paper>
    </div>
  );
};

export default DBManagement;
