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
  LinearProgress
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Update as UpdateIcon,
  Done as DoneIcon
} from '@mui/icons-material';

interface Dependency {
  name: string;
  currentVersion: string;
  latestVersion: string;
  status: 'up-to-date' | 'update-available' | 'major-update' | 'updating';
  type: 'backend' | 'frontend';
}

const Upgrades: React.FC = () => {
  const [dependencies, setDependencies] = useState<Dependency[]>([
    { name: 'FastAPI', currentVersion: '0.104.1', latestVersion: '0.105.0', status: 'update-available', type: 'backend' },
    { name: 'LangGraph', currentVersion: '0.0.40', latestVersion: '0.0.45', status: 'update-available', type: 'backend' },
    { name: 'React', currentVersion: '18.2.0', latestVersion: '18.2.0', status: 'up-to-date', type: 'frontend' },
    { name: 'Material UI', currentVersion: '5.14.5', latestVersion: '5.15.0', status: 'update-available', type: 'frontend' },
    { name: 'Python', currentVersion: '3.10.12', latestVersion: '3.11.6', status: 'major-update', type: 'backend' }
  ]);
  
  const [message, setMessage] = useState('');
  const [updating, setUpdating] = useState(false);
  const [updateProgress, setUpdateProgress] = useState(0);

  useEffect(() => {
    // Simulate progress when updating
    if (updating) {
      const interval = setInterval(() => {
        setUpdateProgress((prev) => {
          if (prev >= 100) {
            clearInterval(interval);
            setUpdating(false);
            setMessage('All dependencies updated successfully!');
            
            // Update the dependencies to show they're up-to-date
            setDependencies((deps) => {
              return deps.map(dep => {
                if (dep.status === 'updating') {
                  return {
                    ...dep,
                    currentVersion: dep.latestVersion,
                    status: 'up-to-date' as const
                  };
                }
                return dep;
              });
            });
            
            return 0;
          }
          return prev + 10;
        });
      }, 500);
      
      return () => clearInterval(interval);
    }
  }, [updating]);

  const handleUpdate = (index: number) => {
    // Mark the dependency as updating
    const newDependencies = [...dependencies];
    newDependencies[index] = { ...newDependencies[index], status: 'updating' };
    setDependencies(newDependencies);
    
    // Start the update process
    setUpdating(true);
    setUpdateProgress(0);
    setMessage(`Updating ${newDependencies[index].name}...`);
  };

  const handleUpdateAll = () => {
    // Mark all updatable dependencies as updating
    const newDependencies = dependencies.map(dep => {
      if (dep.status === 'update-available' || dep.status === 'major-update') {
        return { ...dep, status: 'updating' as const };
      }
      return dep;
    });
    setDependencies(newDependencies);
    
    // Start the update process
    setUpdating(true);
    setUpdateProgress(0);
    setMessage('Updating all dependencies...');
  };

  const getStatusChip = (status: 'up-to-date' | 'update-available' | 'major-update' | 'updating') => {
    switch (status) {
      case 'up-to-date':
        return <Chip icon={<CheckCircleIcon />} label="Up to date" color="success" size="small" />;
      case 'update-available':
        return <Chip icon={<InfoIcon />} label="Update available" color="info" size="small" />;
      case 'major-update':
        return <Chip icon={<WarningIcon />} label="Major update" color="warning" size="small" />;
      case 'updating':
        return <Chip icon={<CircularProgress size={16} />} label="Updating..." color="primary" size="small" />;
      default:
        return null;
    }
  };

  const updatesAvailable = dependencies.some(dep => 
    dep.status === 'update-available' || dep.status === 'major-update'
  );

  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Upgrades & Dependencies
      </Typography>
      
      {message && (
        <Alert 
          severity={message.includes('successfully') ? 'success' : 'info'} 
          sx={{ mb: 3 }}
          onClose={() => setMessage('')}
        >
          {message}
        </Alert>
      )}
      
      {updating && (
        <Box sx={{ mb: 3 }}>
          <LinearProgress variant="determinate" value={updateProgress} />
          <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
            Updating dependencies... {updateProgress}%
          </Typography>
        </Box>
      )}
      
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Summary
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography>Total Dependencies:</Typography>
                <Typography>{dependencies.length}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography>Up to Date:</Typography>
                <Typography>{dependencies.filter(d => d.status === 'up-to-date').length}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography>Updates Available:</Typography>
                <Typography>{dependencies.filter(d => d.status === 'update-available' || d.status === 'major-update').length}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography>Currently Updating:</Typography>
                <Typography>{dependencies.filter(d => d.status === 'updating').length}</Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Actions
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Button 
                  variant="contained" 
                  color="primary" 
                  startIcon={<UpdateIcon />}
                  onClick={handleUpdateAll}
                  disabled={!updatesAvailable || updating}
                  sx={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  }}
                >
                  Update All Dependencies
                </Button>
                <Button 
                  variant="outlined" 
                  startIcon={<DoneIcon />}
                  disabled={updating}
                >
                  Check for Updates
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Backend Dependencies
        </Typography>
        <List>
          {dependencies.filter(dep => dep.type === 'backend').map((dep, index) => (
            <ListItem key={dep.name} divider>
              <ListItemText 
                primary={`${dep.name} ${dep.currentVersion} → ${dep.latestVersion}`} 
                secondary={`Current: ${dep.currentVersion} | Latest: ${dep.latestVersion}`}
              />
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                {getStatusChip(dep.status)}
                <Button 
                  variant="outlined" 
                  disabled={dep.status === 'up-to-date' || dep.status === 'updating' || updating}
                  onClick={() => handleUpdate(dependencies.indexOf(dep))}
                >
                  {dep.status === 'updating' ? 'Updating...' : 'Update'}
                </Button>
              </Box>
            </ListItem>
          ))}
        </List>
        
        <Divider sx={{ my: 3 }} />
        
        <Typography variant="h6" sx={{ mb: 2 }}>
          Frontend Dependencies
        </Typography>
        <List>
          {dependencies.filter(dep => dep.type === 'frontend').map((dep, index) => (
            <ListItem key={dep.name} divider>
              <ListItemText 
                primary={`${dep.name} ${dep.currentVersion} → ${dep.latestVersion}`} 
                secondary={`Current: ${dep.currentVersion} | Latest: ${dep.latestVersion}`}
              />
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                {getStatusChip(dep.status)}
                <Button 
                  variant="outlined" 
                  disabled={dep.status === 'up-to-date' || dep.status === 'updating' || updating}
                  onClick={() => handleUpdate(dependencies.indexOf(dep))}
                >
                  {dep.status === 'updating' ? 'Updating...' : 'Update'}
                </Button>
              </Box>
            </ListItem>
          ))}
        </List>
      </Paper>
    </div>
  );
};

export default Upgrades;
