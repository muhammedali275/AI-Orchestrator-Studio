import React, { useState, useEffect } from 'react';
import {
  Typography,
  Box,
  Paper,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Avatar,
} from '@mui/material';
import {
  AdminPanelSettings as AdminIcon,
  Person as PersonIcon,
  Settings as SettingsIcon,
  Security as SecurityIcon,
  Refresh as RefreshIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  status: 'active' | 'inactive';
  lastLogin: string;
}

interface SystemMetric {
  name: string;
  value: string;
  status: 'healthy' | 'warning' | 'critical';
  description: string;
}

interface FeatureFlag {
  name: string;
  enabled: boolean;
  description: string;
}

const AdminPanel: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [metrics, setMetrics] = useState<SystemMetric[]>([]);
  const [featureFlags, setFeatureFlags] = useState<FeatureFlag[]>([]);
  const [openUserDialog, setOpenUserDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchAdminData();
  }, []);

  const fetchAdminData = async () => {
    try {
      // Fetch users
      const usersResponse = await axios.get('http://localhost:8000/api/admin/users');
      setUsers(usersResponse.data.users || getMockUsers());

      // Fetch system metrics
      const metricsResponse = await axios.get('http://localhost:8000/api/admin/metrics');
      setMetrics(metricsResponse.data.metrics || getMockMetrics());

      // Fetch feature flags
      const flagsResponse = await axios.get('http://localhost:8000/api/admin/feature-flags');
      setFeatureFlags(flagsResponse.data.flags || getMockFeatureFlags());
    } catch (error) {
      console.error('Error fetching admin data:', error);
      // Use mock data if API fails
      setUsers(getMockUsers());
      setMetrics(getMockMetrics());
      setFeatureFlags(getMockFeatureFlags());
    }
  };

  const getMockUsers = (): User[] => [
    {
      id: '1',
      username: 'admin',
      email: 'admin@zainone.com',
      role: 'Administrator',
      status: 'active',
      lastLogin: '2024-01-15 10:30:00',
    },
    {
      id: '2',
      username: 'developer',
      email: 'dev@zainone.com',
      role: 'Developer',
      status: 'active',
      lastLogin: '2024-01-15 09:15:00',
    },
    {
      id: '3',
      username: 'viewer',
      email: 'viewer@zainone.com',
      role: 'Viewer',
      status: 'inactive',
      lastLogin: '2024-01-14 16:45:00',
    },
  ];

  const getMockMetrics = (): SystemMetric[] => [
    {
      name: 'API Response Time',
      value: '45ms',
      status: 'healthy',
      description: 'Average API response time',
    },
    {
      name: 'Error Rate',
      value: '0.5%',
      status: 'healthy',
      description: 'Percentage of failed requests',
    },
    {
      name: 'Active Sessions',
      value: '12',
      status: 'healthy',
      description: 'Currently active user sessions',
    },
    {
      name: 'Database Connections',
      value: '8/20',
      status: 'healthy',
      description: 'Active database connections',
    },
    {
      name: 'Cache Hit Rate',
      value: '85%',
      status: 'healthy',
      description: 'Redis cache hit rate',
    },
    {
      name: 'Disk Usage',
      value: '72%',
      status: 'warning',
      description: 'System disk usage',
    },
  ];

  const getMockFeatureFlags = (): FeatureFlag[] => [
    {
      name: 'advanced_analytics',
      enabled: true,
      description: 'Enable advanced analytics features',
    },
    {
      name: 'experimental_llm',
      enabled: false,
      description: 'Enable experimental LLM models',
    },
    {
      name: 'auto_scaling',
      enabled: true,
      description: 'Enable automatic resource scaling',
    },
    {
      name: 'debug_mode',
      enabled: false,
      description: 'Enable debug logging',
    },
  ];

  const toggleFeatureFlag = async (index: number) => {
    const updatedFlags = [...featureFlags];
    updatedFlags[index].enabled = !updatedFlags[index].enabled;
    setFeatureFlags(updatedFlags);

    try {
      await axios.put('http://localhost:8000/api/admin/feature-flags', {
        flags: updatedFlags,
      });
      setMessage('Feature flag updated successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Error updating feature flag:', error);
      setMessage('Error updating feature flag');
    }
  };

  const handleUserAction = (action: string, user?: User) => {
    setSelectedUser(user || null);
    setOpenUserDialog(true);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'warning':
        return 'warning';
      case 'critical':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon />;
      case 'warning':
        return <WarningIcon />;
      case 'critical':
        return <WarningIcon />;
      default:
        return <InfoIcon />;
    }
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
              background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              mb: 1,
            }}
          >
            Admin Panel
          </Typography>
          <Typography variant="body1" color="text.secondary">
            System administration and management
          </Typography>
        </Box>
        <Tooltip title="Refresh Data">
          <IconButton
            onClick={fetchAdminData}
            sx={{
              background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
              color: 'white',
              '&:hover': {
                background: 'linear-gradient(135deg, #dc2626 0%, #ef4444 100%)',
                transform: 'rotate(180deg)',
              },
              transition: 'all 0.5s ease-in-out',
            }}
          >
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {message && (
        <Alert severity={message.includes('Error') ? 'error' : 'success'} sx={{ mb: 3 }}>
          {message}
        </Alert>
      )}

      {/* System Metrics */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
          System Metrics
        </Typography>
        <Grid container spacing={2}>
          {metrics.map((metric, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <Card
                sx={{
                  background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)',
                  border: '1px solid rgba(102, 126, 234, 0.1)',
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Typography variant="body2" color="text.secondary">
                      {metric.name}
                    </Typography>
                    <Chip
                      icon={getStatusIcon(metric.status)}
                      label={metric.status}
                      size="small"
                      color={getStatusColor(metric.status) as any}
                      sx={{ fontWeight: 600 }}
                    />
                  </Box>
                  <Typography variant="h5" sx={{ fontWeight: 700, mb: 0.5 }}>
                    {metric.value}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {metric.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* User Management */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            User Management
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleUserAction('add')}
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            }}
          >
            Add User
          </Button>
        </Box>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>User</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Role</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Last Login</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id} hover>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Avatar sx={{ width: 32, height: 32, background: '#667eea' }}>
                        <PersonIcon fontSize="small" />
                      </Avatar>
                      <Typography variant="body2" fontWeight={600}>
                        {user.username}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>
                    <Chip label={user.role} size="small" sx={{ fontWeight: 600 }} />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={user.status}
                      size="small"
                      color={user.status === 'active' ? 'success' : 'default'}
                      sx={{ fontWeight: 600 }}
                    />
                  </TableCell>
                  <TableCell>{user.lastLogin}</TableCell>
                  <TableCell align="right">
                    <Tooltip title="Edit User">
                      <IconButton size="small" onClick={() => handleUserAction('edit', user)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete User">
                      <IconButton size="small" color="error">
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Feature Flags */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
          Feature Flags
        </Typography>
        <Grid container spacing={2}>
          {featureFlags.map((flag, index) => (
            <Grid item xs={12} sm={6} key={index}>
              <Box
                sx={{
                  p: 2,
                  borderRadius: 2,
                  background: 'rgba(102, 126, 234, 0.05)',
                  border: '1px solid rgba(102, 126, 234, 0.1)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <Box>
                  <Typography variant="body1" fontWeight={600}>
                    {flag.name.replace(/_/g, ' ').toUpperCase()}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {flag.description}
                  </Typography>
                </Box>
                <FormControlLabel
                  control={
                    <Switch
                      checked={flag.enabled}
                      onChange={() => toggleFeatureFlag(index)}
                      color="primary"
                    />
                  }
                  label=""
                />
              </Box>
            </Grid>
          ))}
        </Grid>
      </Paper>

      {/* User Dialog */}
      <Dialog open={openUserDialog} onClose={() => setOpenUserDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {selectedUser ? 'Edit User' : 'Add New User'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField label="Username" fullWidth defaultValue={selectedUser?.username} />
            <TextField label="Email" type="email" fullWidth defaultValue={selectedUser?.email} />
            <TextField label="Role" fullWidth defaultValue={selectedUser?.role} />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenUserDialog(false)}>Cancel</Button>
          <Button
            variant="contained"
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            }}
          >
            {selectedUser ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AdminPanel;
