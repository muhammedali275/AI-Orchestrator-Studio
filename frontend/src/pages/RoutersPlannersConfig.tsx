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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  CircularProgress,
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  AccountTree as RouterIcon,
  Timeline as PlannerIcon,
  ExpandMore as ExpandMoreIcon,
  PlayArrow as TestIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface Router {
  name: string;
  type: string;
  enabled: boolean;
  priority: number;
  rules: Record<string, any>;
  description?: string;
}

interface Planner {
  name: string;
  type: string;
  enabled: boolean;
  strategy: string;
  templates: Record<string, any>;
  description?: string;
}

const ROUTER_TYPES = [
  { value: 'rule_based', label: 'Rule-Based', description: 'Rule-based intent classification using keywords and patterns' },
  { value: 'llm_based', label: 'LLM-Based', description: 'LLM-powered intent classification' },
  { value: 'hybrid', label: 'Hybrid', description: 'Combination of rule-based and LLM-based routing' },
  { value: 'keyword', label: 'Keyword', description: 'Simple keyword matching for intent classification' },
];

const PLANNER_TYPES = [
  { value: 'sequential', label: 'Sequential', description: 'Execute tasks one after another in sequence' },
  { value: 'parallel', label: 'Parallel', description: 'Execute independent tasks in parallel' },
  { value: 'conditional', label: 'Conditional', description: 'Execute tasks based on conditions and branching logic' },
  { value: 'llm_based', label: 'LLM-Based', description: 'LLM-powered dynamic task planning' },
];

const RoutersPlannersConfig: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [routers, setRouters] = useState<Router[]>([]);
  const [planners, setPlanners] = useState<Planner[]>([]);
  const [message, setMessage] = useState('');
  const [testingRouter, setTestingRouter] = useState<string | null>(null);
  const [testingPlanner, setTestingPlanner] = useState<string | null>(null);
  const [openRouterDialog, setOpenRouterDialog] = useState(false);
  const [openPlannerDialog, setOpenPlannerDialog] = useState(false);
  const [editingRouter, setEditingRouter] = useState<Router | null>(null);
  const [editingPlanner, setEditingPlanner] = useState<Planner | null>(null);

  const [routerFormData, setRouterFormData] = useState<Router>({
    name: '',
    type: 'keyword',
    enabled: true,
    priority: 0,
    rules: {},
    description: '',
  });

  const [plannerFormData, setPlannerFormData] = useState<Planner>({
    name: '',
    type: 'sequential',
    enabled: true,
    strategy: 'sequential',
    templates: {},
    description: '',
  });

  useEffect(() => {
    fetchRouters();
    fetchPlanners();
  }, []);

  const fetchRouters = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/routers');
      setRouters(Array.isArray(response.data) ? response.data : []);
      setMessage('');
    } catch (error: any) {
      console.error('Error fetching routers:', error);
      if (error.response && error.response.status !== 404) {
        setMessage(`Error fetching routers: ${error.response.data?.detail || error.message}`);
      } else if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
        setMessage('⚠️ Backend server is not running. Please start the backend at http://localhost:8000');
      }
    }
  };

  const fetchPlanners = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/planners');
      setPlanners(Array.isArray(response.data) ? response.data : []);
      setMessage('');
    } catch (error: any) {
      console.error('Error fetching planners:', error);
      if (error.response && error.response.status !== 404) {
        setMessage(`Error fetching planners: ${error.response.data?.detail || error.message}`);
      } else if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
        setMessage('⚠️ Backend server is not running. Please start the backend at http://localhost:8000');
      }
    }
  };

  const handleSaveRouter = async () => {
    try {
      if (!routerFormData.name || !routerFormData.type) {
        setMessage('Error: Router name and type are required');
        return;
      }

      if (editingRouter) {
        await axios.put(`http://localhost:8000/api/routers/${editingRouter.name}`, routerFormData);
        setMessage('Router updated successfully!');
      } else {
        await axios.post('http://localhost:8000/api/routers', routerFormData);
        setMessage('Router created successfully!');
      }
      
      fetchRouters();
      setOpenRouterDialog(false);
      setTimeout(() => setMessage(''), 3000);
    } catch (error: any) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleSavePlanner = async () => {
    try {
      if (!plannerFormData.name || !plannerFormData.type) {
        setMessage('Error: Planner name and type are required');
        return;
      }

      if (editingPlanner) {
        await axios.put(`http://localhost:8000/api/planners/${editingPlanner.name}`, plannerFormData);
        setMessage('Planner updated successfully!');
      } else {
        await axios.post('http://localhost:8000/api/planners', plannerFormData);
        setMessage('Planner created successfully!');
      }
      
      fetchPlanners();
      setOpenPlannerDialog(false);
      setTimeout(() => setMessage(''), 3000);
    } catch (error: any) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleDeleteRouter = async (name: string) => {
    if (!window.confirm(`Delete router "${name}"?`)) return;
    try {
      await axios.delete(`http://localhost:8000/api/routers/${name}`);
      setMessage('Router deleted successfully!');
      fetchRouters();
      setTimeout(() => setMessage(''), 3000);
    } catch (error: any) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleDeletePlanner = async (name: string) => {
    if (!window.confirm(`Delete planner "${name}"?`)) return;
    try {
      await axios.delete(`http://localhost:8000/api/planners/${name}`);
      setMessage('Planner deleted successfully!');
      fetchPlanners();
      setTimeout(() => setMessage(''), 3000);
    } catch (error: any) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  const testRouter = async (name: string) => {
    setTestingRouter(name);
    try {
      const response = await axios.post(`http://localhost:8000/api/routers/${name}/test`, {
        input_text: "Analyze customer churn patterns",
        context: {}
      });
      if (response.data.success) {
        setMessage(`Router "${name}" test successful! Intent: ${response.data.classification?.intent}`);
      } else {
        setMessage(`Router "${name}" test failed`);
      }
      setTimeout(() => setMessage(''), 5000);
    } catch (error: any) {
      setMessage(`Error testing router: ${error.message}`);
    } finally {
      setTestingRouter(null);
    }
  };

  const testPlanner = async (name: string) => {
    setTestingPlanner(name);
    try {
      const response = await axios.post(`http://localhost:8000/api/planners/${name}/test`, {
        user_input: "Analyze customer churn",
        intent: "churn_analytics",
        context: {}
      });
      if (response.data.success) {
        setMessage(`Planner "${name}" test successful! Generated ${response.data.plan?.tasks?.length || 0} tasks`);
      } else {
        setMessage(`Planner "${name}" test failed`);
      }
      setTimeout(() => setMessage(''), 5000);
    } catch (error: any) {
      setMessage(`Error testing planner: ${error.message}`);
    } finally {
      setTestingPlanner(null);
    }
  };

  return (
    <Box className="fade-in">
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
            Routers & Planners
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Configure intent routers and task planners
          </Typography>
        </Box>
        <Tooltip title="Refresh">
          <IconButton
            onClick={() => { fetchRouters(); fetchPlanners(); }}
            sx={{ background: 'rgba(102, 126, 234, 0.1)', '&:hover': { background: 'rgba(102, 126, 234, 0.2)' } }}
          >
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      <Paper sx={{ p: 3, mb: 3, background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)' }}>
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
          Understanding Routers & Planners
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
              <RouterIcon sx={{ color: '#667eea', mt: 0.5 }} />
              <Box>
                <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
                  Routers
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Routers classify user intent to determine the appropriate workflow path.
                </Typography>
              </Box>
            </Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
              <PlannerIcon sx={{ color: '#764ba2', mt: 0.5 }} />
              <Box>
                <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
                  Planners
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Planners decompose complex tasks into executable steps.
                </Typography>
              </Box>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {message && (
        <Alert severity={message.includes('Error') || message.includes('⚠️') ? 'error' : 'success'} sx={{ mb: 3 }} onClose={() => setMessage('')}>
          {message}
        </Alert>
      )}

      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab label="Routers" icon={<RouterIcon />} iconPosition="start" />
          <Tab label="Planners" icon={<PlannerIcon />} iconPosition="start" />
        </Tabs>
      </Paper>

      {tabValue === 0 && (
        <Box>
          <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>Intent Routers</Typography>
              <Typography variant="body2" color="text.secondary">Classify user intent and route to appropriate workflows</Typography>
            </Box>
            <Button variant="contained" startIcon={<AddIcon />}
              onClick={() => {
                setEditingRouter(null);
                setRouterFormData({ name: '', type: 'keyword', enabled: true, priority: 0, rules: {}, description: '' });
                setOpenRouterDialog(true);
              }}
              sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
              Add Router
            </Button>
          </Box>

          {routers.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <RouterIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>No routers configured</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>Add your first router to enable intent classification</Typography>
              <Button variant="contained" startIcon={<AddIcon />}
                onClick={() => {
                  setEditingRouter(null);
                  setRouterFormData({ name: '', type: 'keyword', enabled: true, priority: 0, rules: {}, description: '' });
                  setOpenRouterDialog(true);
                }}
                sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>Add Router</Button>
            </Paper>
          ) : (
            routers.map((router) => (
              <Accordion key={router.name} sx={{ mb: 2, background: 'rgba(102, 126, 234, 0.02)', border: '1px solid rgba(102, 126, 234, 0.1)', '&:before': { display: 'none' } }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%', mr: 2 }}>
                    <RouterIcon sx={{ color: '#667eea' }} />
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>{router.name}</Typography>
                      <Typography variant="caption" color="text.secondary">{router.type} - Priority: {router.priority}</Typography>
                    </Box>
                    <Chip label={router.enabled ? 'Enabled' : 'Disabled'} size="small" color={router.enabled ? 'success' : 'default'} />
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <TextField label="Type" value={ROUTER_TYPES.find(t => t.value === router.type)?.label || router.type} size="small" fullWidth disabled />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <TextField label="Priority" value={router.priority} size="small" fullWidth disabled />
                    </Grid>
                    {router.description && (
                      <Grid item xs={12}>
                        <TextField label="Description" value={router.description} size="small" fullWidth disabled multiline rows={2} />
                      </Grid>
                    )}
                    <Grid item xs={12}>
                      <Box sx={{ display: 'flex', gap: 2 }}>
                        <Button variant="outlined" startIcon={testingRouter === router.name ? <CircularProgress size={20} /> : <TestIcon />}
                          onClick={() => testRouter(router.name)} disabled={testingRouter === router.name}>Test Router</Button>
                        <Button variant="outlined" startIcon={<EditIcon />} onClick={() => {
                          setEditingRouter(router);
                          setRouterFormData(router);
                          setOpenRouterDialog(true);
                        }}>Edit</Button>
                        <Button variant="outlined" color="error" startIcon={<DeleteIcon />}
                          onClick={() => handleDeleteRouter(router.name)} sx={{ ml: 'auto' }}>Delete</Button>
                      </Box>
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            ))
          )}
        </Box>
      )}

      {tabValue === 1 && (
        <Box>
          <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>Task Planners</Typography>
              <Typography variant="body2" color="text.secondary">Decompose complex tasks into executable steps</Typography>
            </Box>
            <Button variant="contained" startIcon={<AddIcon />}
              onClick={() => {
                setEditingPlanner(null);
                setPlannerFormData({ name: '', type: 'sequential', enabled: true, strategy: 'sequential', templates: {}, description: '' });
                setOpenPlannerDialog(true);
              }}
              sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>Add Planner</Button>
          </Box>

          {planners.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <PlannerIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>No planners configured</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>Add your first planner to enable task decomposition</Typography>
              <Button variant="contained" startIcon={<AddIcon />}
                onClick={() => {
                  setEditingPlanner(null);
                  setPlannerFormData({ name: '', type: 'sequential', enabled: true, strategy: 'sequential', templates: {}, description: '' });
                  setOpenPlannerDialog(true);
                }}
                sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>Add Planner</Button>
            </Paper>
          ) : (
            planners.map((planner) => (
              <Accordion key={planner.name} sx={{ mb: 2, background: 'rgba(102, 126, 234, 0.02)', border: '1px solid rgba(102, 126, 234, 0.1)', '&:before': { display: 'none' } }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%', mr: 2 }}>
                    <PlannerIcon sx={{ color: '#764ba2' }} />
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>{planner.name}</Typography>
                      <Typography variant="caption" color="text.secondary">{planner.type} - Strategy: {planner.strategy}</Typography>
                    </Box>
                    <Chip label={planner.enabled ? 'Enabled' : 'Disabled'} size="small" color={planner.enabled ? 'success' : 'default'} />
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <TextField label="Type" value={PLANNER_TYPES.find(t => t.value === planner.type)?.label || planner.type} size="small" fullWidth disabled />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <TextField label="Strategy" value={planner.strategy} size="small" fullWidth disabled />
                    </Grid>
                    {planner.description && (
                      <Grid item xs={12}>
                        <TextField label="Description" value={planner.description} size="small" fullWidth disabled multiline rows={2} />
                      </Grid>
                    )}
                    <Grid item xs={12}>
                      <Box sx={{ display: 'flex', gap: 2 }}>
                        <Button variant="outlined" startIcon={testingPlanner === planner.name ? <CircularProgress size={20} /> : <TestIcon />}
                          onClick={() => testPlanner(planner.name)} disabled={testingPlanner === planner.name}>Test Planner</Button>
                        <Button variant="outlined" startIcon={<EditIcon />} onClick={() => {
                          setEditingPlanner(planner);
                          setPlannerFormData(planner);
                          setOpenPlannerDialog(true);
                        }}>Edit</Button>
                        <Button variant="outlined" color="error" startIcon={<DeleteIcon />}
                          onClick={() => handleDeletePlanner(planner.name)} sx={{ ml: 'auto' }}>Delete</Button>
                      </Box>
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            ))
          )}
        </Box>
      )}

      <Dialog open={openRouterDialog} onClose={() => setOpenRouterDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>{editingRouter ? 'Edit Router' : 'Add Router'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField label="Router Name" fullWidth required value={routerFormData.name}
                onChange={(e) => setRouterFormData({ ...routerFormData, name: e.target.value })}
                disabled={!!editingRouter} helperText="Unique identifier for the router" />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth required>
                <InputLabel>Router Type</InputLabel>
                <Select value={routerFormData.type} label="Router Type"
                  onChange={(e) => setRouterFormData({ ...routerFormData, type: e.target.value })}>
                  {ROUTER_TYPES.map(t => <MenuItem key={t.value} value={t.value}>{t.label}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField label="Priority" fullWidth type="number" value={routerFormData.priority}
                onChange={(e) => setRouterFormData({ ...routerFormData, priority: parseInt(e.target.value) || 0 })}
                helperText="Higher priority routers are evaluated first" />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl component="fieldset">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2 }}>
                  <Typography variant="body2">Enabled:</Typography>
                  <Chip label={routerFormData.enabled ? 'Yes' : 'No'} size="small" 
                    color={routerFormData.enabled ? 'success' : 'default'}
                    onClick={() => setRouterFormData({ ...routerFormData, enabled: !routerFormData.enabled })}
                    sx={{ cursor: 'pointer' }} />
                </Box>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField label="Description" fullWidth multiline rows={2} value={routerFormData.description || ''}
                onChange={(e) => setRouterFormData({ ...routerFormData, description: e.target.value })}
                helperText="Brief description of what this router does" />
            </Grid>
            <Grid item xs={12}>
              <TextField label="Rules (JSON)" fullWidth multiline rows={6}
                value={JSON.stringify(routerFormData.rules, null, 2)}
                onChange={(e) => {
                  try {
                    const parsed = JSON.parse(e.target.value);
                    setRouterFormData({ ...routerFormData, rules: parsed });
                  } catch (err) { }
                }}
                helperText="Router-specific rules and patterns in JSON format" />
            </Grid>
            <Grid item xs={12}>
              <Alert severity="info">
                {ROUTER_TYPES.find(t => t.value === routerFormData.type)?.description || 'Configure your router settings'}
              </Alert>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenRouterDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveRouter} variant="contained" disabled={!routerFormData.name || !routerFormData.type}>
            {editingRouter ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={openPlannerDialog} onClose={() => setOpenPlannerDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>{editingPlanner ? 'Edit Planner' : 'Add Planner'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField label="Planner Name" fullWidth required value={plannerFormData.name}
                onChange={(e) => setPlannerFormData({ ...plannerFormData, name: e.target.value })}
                disabled={!!editingPlanner} helperText="Unique identifier for the planner" />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth required>
                <InputLabel>Planner Type</InputLabel>
                <Select value={plannerFormData.type} label="Planner Type"
                  onChange={(e) => setPlannerFormData({ ...plannerFormData, type: e.target.value })}>
                  {PLANNER_TYPES.map(t => <MenuItem key={t.value} value={t.value}>{t.label}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField label="Strategy" fullWidth value={plannerFormData.strategy}
                onChange={(e) => setPlannerFormData({ ...plannerFormData, strategy: e.target.value })}
                helperText="Planning strategy (sequential, parallel, adaptive, etc.)" />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl component="fieldset">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2 }}>
                  <Typography variant="body2">Enabled:</Typography>
                  <Chip label={plannerFormData.enabled ? 'Yes' : 'No'} size="small" 
                    color={plannerFormData.enabled ? 'success' : 'default'}
                    onClick={() => setPlannerFormData({ ...plannerFormData, enabled: !plannerFormData.enabled })}
                    sx={{ cursor: 'pointer' }} />
                </Box>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField label="Description" fullWidth multiline rows={2} value={plannerFormData.description || ''}
                onChange={(e) => setPlannerFormData({ ...plannerFormData, description: e.target.value })}
                helperText="Brief description of what this planner does" />
            </Grid>
            <Grid item xs={12}>
              <TextField label="Templates (JSON)" fullWidth multiline rows={8}
                value={JSON.stringify(plannerFormData.templates, null, 2)}
                onChange={(e) => {
                  try {
                    const parsed = JSON.parse(e.target.value);
                    setPlannerFormData({ ...plannerFormData, templates: parsed });
                  } catch (err) { }
                }}
                helperText="Plan templates for different intents in JSON format" />
            </Grid>
            <Grid item xs={12}>
              <Alert severity="info">
                {PLANNER_TYPES.find(t => t.value === plannerFormData.type)?.description || 'Configure your planner settings'}
              </Alert>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenPlannerDialog(false)}>Cancel</Button>
          <Button onClick={handleSavePlanner} variant="contained" disabled={!plannerFormData.name || !plannerFormData.type}>
            {editingPlanner ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default RoutersPlannersConfig;
