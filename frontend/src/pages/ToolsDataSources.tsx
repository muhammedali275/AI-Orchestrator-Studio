import React, { useState, useEffect } from 'react';
import {
  Typography,
  Paper,
  Box,
  Button,
  TextField,
  Grid,
  Card,
  CardContent,
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
  Divider,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Build as BuildIcon,
  Storage as StorageIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  ExpandMore as ExpandMoreIcon,
  Cable as CableIcon,
  PlayArrow as TestIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface Tool {
  name: string;
  type: string;
  enabled: boolean;
  config: {
    endpoint?: string;
    port?: string;
    api_key?: string;
    timeout?: string;
    [key: string]: any;
  };
  status?: {
    connected: boolean;
    message: string;
    latency?: number;
  };
}

interface DataSource {
  name: string;
  type: string;
  url: string;
  auth_token?: string;
  timeout_seconds: number;
  enabled: boolean;
  config: Record<string, any>;
}

const DATASOURCE_TYPES = [
  { value: 'cubejs', label: 'Cube.js Analytics' },
  { value: 'postgres', label: 'PostgreSQL Database' },
  { value: 'mysql', label: 'MySQL Database' },
  { value: 'mongodb', label: 'MongoDB' },
  { value: 'api', label: 'HTTP API' },
  { value: 'custom', label: 'Custom' },
];

const ToolsDataSources: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [tools, setTools] = useState<Tool[]>([]);
  const [datasources, setDatasources] = useState<DataSource[]>([]);
  const [message, setMessage] = useState('');
  const [testingTool, setTestingTool] = useState<string | null>(null);
  const [testingDatasource, setTestingDatasource] = useState<string | null>(null);
  const [openToolDialog, setOpenToolDialog] = useState(false);
  const [openDatasourceDialog, setOpenDatasourceDialog] = useState(false);
  const [editingTool, setEditingTool] = useState<Tool | null>(null);
  const [editingDatasource, setEditingDatasource] = useState<DataSource | null>(null);
  const [queryDialogOpen, setQueryDialogOpen] = useState(false);
  const [selectedDatasource, setSelectedDatasource] = useState<string>('');
  const [testQuery, setTestQuery] = useState('');
  const [queryResult, setQueryResult] = useState<any>(null);
  const [queryLoading, setQueryLoading] = useState(false);

  const [toolFormData, setToolFormData] = useState<Tool>({
    name: '',
    type: 'http_request',
    enabled: true,
    config: {
      endpoint: '',
      port: '',
      api_key: '',
      timeout: '30',
      base_url: '',
      headers: {},
    },
  });

  const TOOL_TYPES = [
    { value: 'http_request', label: 'HTTP Request', description: 'Make HTTP requests to external APIs' },
    { value: 'web_search', label: 'Web Search', description: 'Search the web for information' },
    { value: 'code_executor', label: 'Code Executor', description: 'Execute code in a sandboxed environment' },
    { value: 'custom', label: 'Custom Tool', description: 'Custom tool implementation' },
  ];

  const [datasourceFormData, setDatasourceFormData] = useState<DataSource>({
    name: '',
    type: 'cubejs',
    url: '',
    auth_token: '',
    timeout_seconds: 30,
    enabled: true,
    config: {},
  });

  useEffect(() => {
    fetchTools();
    fetchDatasources();
  }, []);

  const fetchTools = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/tools');
      // Backend returns array directly, not {tools: [...]}
      const fetchedTools = Array.isArray(response.data) ? response.data : [];
      const normalizedTools = fetchedTools.map((tool: any) => ({
        ...tool,
        enabled: tool.enabled !== undefined ? tool.enabled : true,
        config: {
          endpoint: tool.config?.endpoint || '',
          port: tool.config?.port || '',
          api_key: tool.config?.api_key || '',
          timeout: tool.config?.timeout || '30',
          ...tool.config,
        },
        status: tool.status || { connected: false, message: 'Not tested' },
      }));
      setTools(normalizedTools);
      setMessage(''); // Clear any previous errors
    } catch (error: any) {
      console.error('Error fetching tools:', error);
      // Only show error if it's not a network error (backend not running) or 404
      if (error.response && error.response.status !== 404) {
        setMessage(`Error fetching tools: ${error.response.data?.detail || error.message}`);
      } else if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
        setMessage('⚠️ Backend server is not running. Please start the backend at http://localhost:8000');
      }
      // If it's just a 404 or empty response, don't show error (empty state is fine)
    }
  };

  const fetchDatasources = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/datasources');
      setDatasources(Array.isArray(response.data) ? response.data : []);
      setMessage(''); // Clear any previous errors
    } catch (error: any) {
      console.error('Error fetching datasources:', error);
      // Only show error if it's not a network error (backend not running) or 404
      if (error.response && error.response.status !== 404) {
        setMessage(`Error fetching datasources: ${error.response.data?.detail || error.message}`);
      } else if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
        setMessage('⚠️ Backend server is not running. Please start the backend at http://localhost:8000');
      }
      // If it's just a 404 or empty response, don't show error (empty state is fine)
    }
  };

  const handleSaveTools = async () => {
    try {
      // Save each tool individually
      for (const tool of tools) {
        try {
          // Try to update first, if it fails, create new
          await axios.put(`http://localhost:8000/api/tools/${tool.name}`, tool);
        } catch (error: any) {
          if (error.response?.status === 404) {
            // Tool doesn't exist, create it
            await axios.post('http://localhost:8000/api/tools', tool);
          } else {
            throw error;
          }
        }
      }
      setMessage('Tools configuration updated successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      setMessage('Error updating tools configuration');
    }
  };

  const handleSaveTool = async () => {
    try {
      // Validate required fields
      if (!toolFormData.name || !toolFormData.type) {
        setMessage('Error: Tool name and type are required');
        return;
      }

      if (editingTool) {
        // Update existing tool
        await axios.put(`http://localhost:8000/api/tools/${editingTool.name}`, toolFormData);
        setMessage('Tool updated successfully!');
      } else {
        // Create new tool
        await axios.post('http://localhost:8000/api/tools', toolFormData);
        setMessage('Tool created successfully!');
      }
      
      fetchTools(); // Refresh the list
      setOpenToolDialog(false);
      setTimeout(() => setMessage(''), 3000);
    } catch (error: any) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleSaveDatasource = async () => {
    try {
      if (editingDatasource) {
        await axios.put(`http://localhost:8000/api/datasources/${editingDatasource.name}`, datasourceFormData);
        setMessage('Datasource updated successfully!');
      } else {
        await axios.post('http://localhost:8000/api/datasources', datasourceFormData);
        setMessage('Datasource created successfully!');
      }
      fetchDatasources();
      setOpenDatasourceDialog(false);
      setTimeout(() => setMessage(''), 3000);
    } catch (error: any) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleDeleteDatasource = async (name: string) => {
    if (!window.confirm(`Delete datasource "${name}"?`)) return;
    try {
      await axios.delete(`http://localhost:8000/api/datasources/${name}`);
      setMessage('Datasource deleted successfully!');
      fetchDatasources();
      setTimeout(() => setMessage(''), 3000);
    } catch (error: any) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  const testToolConnection = async (index: number) => {
    const tool = tools[index];
    setTestingTool(tool.name);
    try {
      const response = await axios.post(`http://localhost:8000/api/tools/${tool.name}/test`, {
        config: tool.config
      });
      const updatedTools = [...tools];
      updatedTools[index].status = {
        connected: response.data.success,
        message: response.data.message || (response.data.success ? 'Connection successful!' : 'Connection failed'),
        latency: response.data.latency,
      };
      setTools(updatedTools);
      setMessage(response.data.message || 'Test completed');
      setTimeout(() => setMessage(''), 3000);
    } catch (error: any) {
      const updatedTools = [...tools];
      updatedTools[index].status = {
        connected: false,
        message: error.response?.data?.detail || error.message || 'Connection failed',
      };
      setTools(updatedTools);
      setMessage(`Test failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setTestingTool(null);
    }
  };

  const testDatasourceConnection = async (name: string) => {
    setTestingDatasource(name);
    try {
      const response = await axios.post(`http://localhost:8000/api/datasources/${name}/test`);
      if (response.data.success) {
        setMessage(`Datasource "${name}" is healthy!`);
      } else {
        setMessage(`Datasource "${name}" test failed`);
      }
      setTimeout(() => setMessage(''), 3000);
    } catch (error: any) {
      setMessage(`Error testing datasource: ${error.message}`);
    } finally {
      setTestingDatasource(null);
    }
  };

  const handleTestQuery = async () => {
    setQueryLoading(true);
    try {
      const response = await axios.post(`http://localhost:8000/api/datasources/${selectedDatasource}/query`, {
        query: testQuery,
        parameters: {},
      });
      setQueryResult(response.data);
    } catch (error: any) {
      setQueryResult({ error: error.response?.data?.detail || error.message });
    } finally {
      setQueryLoading(false);
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
            Tools & Data Sources
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Configure integration tools and data sources
          </Typography>
        </Box>
        <Tooltip title="Refresh">
          <IconButton
            onClick={() => { fetchTools(); fetchDatasources(); }}
            sx={{ background: 'rgba(102, 126, 234, 0.1)', '&:hover': { background: 'rgba(102, 126, 234, 0.2)' } }}
          >
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Explanation of Tools vs Data Sources */}
      <Paper sx={{ p: 3, mb: 3, background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)' }}>
        <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
          Understanding Tools & Data Sources
        </Typography>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
              <BuildIcon sx={{ color: '#667eea', mt: 0.5 }} />
              <Box>
                <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
                  Tools
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Tools are <strong>actions</strong> the LLM can execute, such as API calls, 
                  functions, or external services. They allow the LLM to perform operations 
                  like searching the web, executing code, or accessing specialized services.
                  Tools are used to extend the LLM's capabilities beyond text generation.
                </Typography>
              </Box>
            </Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
              <StorageIcon sx={{ color: '#764ba2', mt: 0.5 }} />
              <Box>
                <Typography variant="subtitle1" sx={{ fontWeight: 600, mb: 1 }}>
                  Data Sources
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Data Sources are <strong>read-only</strong> information repositories used for 
                  grounding and retrieval-augmented generation (RAG). They provide context and 
                  knowledge to the LLM without allowing it to modify the underlying data. 
                  Data sources help the LLM access specific information it wasn't trained on.
                </Typography>
              </Box>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {message && (
        <Alert severity={message.includes('Error') ? 'error' : 'success'} sx={{ mb: 3 }} onClose={() => setMessage('')}>
          {message}
        </Alert>
      )}

      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)}>
          <Tab label="Tools" icon={<BuildIcon />} iconPosition="start" />
          <Tab label="Data Sources" icon={<StorageIcon />} iconPosition="start" />
        </Tabs>
      </Paper>

      {/* Tools Tab */}
      {tabValue === 0 && (
        <Box>
          <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Integration Tools
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Tools execute actions on behalf of the LLM (API calls, code execution, etc.)
              </Typography>
            </Box>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => {
                setEditingTool(null);
                setToolFormData({ 
                  name: '', 
                  type: 'http_request', 
                  enabled: true, 
                  config: { 
                    endpoint: '', 
                    port: '', 
                    api_key: '', 
                    timeout: '30',
                    base_url: '',
                    headers: {}
                  } 
                });
                setOpenToolDialog(true);
              }}
              sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
            >
              Add Tool
            </Button>
          </Box>

          {tools.map((tool, index) => (
            <Accordion key={index} sx={{ mb: 2, background: 'rgba(102, 126, 234, 0.02)', border: '1px solid rgba(102, 126, 234, 0.1)', '&:before': { display: 'none' } }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%', mr: 2 }}>
                  <BuildIcon sx={{ color: '#667eea' }} />
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>{tool.name}</Typography>
                    <Typography variant="caption" color="text.secondary">{tool.type}</Typography>
                  </Box>
                  <Chip label={tool.enabled ? 'Enabled' : 'Disabled'} size="small" color={tool.enabled ? 'success' : 'default'} />
                  {tool.status && (
                    <Chip icon={tool.status.connected ? <CheckCircleIcon /> : <ErrorIcon />}
                      label={tool.status.connected ? 'Connected' : 'Disconnected'}
                      size="small" color={tool.status.connected ? 'success' : 'error'} />
                  )}
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <TextField label="Endpoint" value={tool.config.endpoint || ''} size="small" fullWidth disabled />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField label="Port" value={tool.config.port || ''} size="small" fullWidth disabled />
                  </Grid>
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', gap: 2 }}>
                      <Button variant="outlined" startIcon={testingTool === tool.name ? <CircularProgress size={20} /> : <CableIcon />}
                        onClick={() => testToolConnection(index)} disabled={testingTool === tool.name}>
                        Test Connection
                      </Button>
                      <Button variant="outlined" startIcon={<EditIcon />} onClick={() => {
                        setEditingTool(tool);
                        setToolFormData(tool);
                        setOpenToolDialog(true);
                      }}>
                        Edit
                      </Button>
                      <Button variant="outlined" color="error" startIcon={<DeleteIcon />} onClick={() => {
                        const updatedTools = tools.filter((_, i) => i !== index);
                        setTools(updatedTools);
                      }} sx={{ ml: 'auto' }}>
                        Delete
                      </Button>
                    </Box>
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          ))}

          <Button variant="outlined" onClick={handleSaveTools} sx={{ mt: 2 }}>
            Save All Tools
          </Button>
        </Box>
      )}

      {/* Data Sources Tab */}
      {tabValue === 1 && (
        <Box>
          <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Data Sources
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Read-only knowledge repositories for grounding and context (RAG)
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button variant="outlined" startIcon={<TestIcon />} onClick={() => setQueryDialogOpen(true)}
                disabled={datasources.length === 0}>
                Test Query
              </Button>
              <Button variant="contained" startIcon={<AddIcon />}
                onClick={() => {
                  setEditingDatasource(null);
                  setDatasourceFormData({ name: '', type: 'cubejs', url: '', auth_token: '', timeout_seconds: 30, enabled: true, config: {} });
                  setOpenDatasourceDialog(true);
                }}
                sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
                Add Data Source
              </Button>
            </Box>
          </Box>

          {datasources.length === 0 ? (
            <Paper sx={{ p: 4, textAlign: 'center' }}>
              <StorageIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" color="text.secondary" gutterBottom>No data sources configured</Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Add your first data source to enable data access
              </Typography>
              <Button variant="contained" startIcon={<AddIcon />}
                onClick={() => {
                  setEditingDatasource(null);
                  setDatasourceFormData({ name: '', type: 'cubejs', url: '', auth_token: '', timeout_seconds: 30, enabled: true, config: {} });
                  setOpenDatasourceDialog(true);
                }}
                sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
                Add Data Source
              </Button>
            </Paper>
          ) : (
            datasources.map((ds) => (
              <Accordion key={ds.name} sx={{ mb: 2, background: 'rgba(102, 126, 234, 0.02)', border: '1px solid rgba(102, 126, 234, 0.1)', '&:before': { display: 'none' } }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%', mr: 2 }}>
                    <StorageIcon sx={{ color: '#764ba2' }} />
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="h6" sx={{ fontWeight: 600 }}>{ds.name}</Typography>
                      <Typography variant="caption" color="text.secondary">{ds.type} - {ds.url}</Typography>
                    </Box>
                    <Chip label={ds.enabled ? 'Enabled' : 'Disabled'} size="small" color={ds.enabled ? 'success' : 'default'} />
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <TextField label="Type" value={DATASOURCE_TYPES.find(t => t.value === ds.type)?.label || ds.type} size="small" fullWidth disabled />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <TextField label="Timeout" value={`${ds.timeout_seconds}s`} size="small" fullWidth disabled />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField label="URL" value={ds.url} size="small" fullWidth disabled />
                    </Grid>
                    <Grid item xs={12}>
                      <Box sx={{ display: 'flex', gap: 2 }}>
                        <Button variant="outlined" startIcon={testingDatasource === ds.name ? <CircularProgress size={20} /> : <CableIcon />}
                          onClick={() => testDatasourceConnection(ds.name)} disabled={testingDatasource === ds.name}>
                          Test Connection
                        </Button>
                        <Button variant="outlined" startIcon={<EditIcon />} onClick={() => {
                          setEditingDatasource(ds);
                          setDatasourceFormData(ds);
                          setOpenDatasourceDialog(true);
                        }}>
                          Edit
                        </Button>
                        <Button variant="outlined" color="error" startIcon={<DeleteIcon />}
                          onClick={() => handleDeleteDatasource(ds.name)} sx={{ ml: 'auto' }}>
                          Delete
                        </Button>
                      </Box>
                    </Grid>
                  </Grid>
                </AccordionDetails>
              </Accordion>
            ))
          )}
        </Box>
      )}

      {/* Tool Dialog */}
      <Dialog open={openToolDialog} onClose={() => setOpenToolDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>{editingTool ? 'Edit Tool' : 'Add Tool'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField 
                label="Tool Name" 
                fullWidth 
                required
                value={toolFormData.name}
                onChange={(e) => setToolFormData({ ...toolFormData, name: e.target.value })}
                disabled={!!editingTool}
                helperText="Unique identifier for the tool"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth required>
                <InputLabel>Tool Type</InputLabel>
                <Select 
                  value={toolFormData.type} 
                  label="Tool Type"
                  onChange={(e) => setToolFormData({ ...toolFormData, type: e.target.value })}
                >
                  {TOOL_TYPES.map(t => (
                    <MenuItem key={t.value} value={t.value}>
                      {t.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField 
                label="Description" 
                fullWidth 
                multiline
                rows={2}
                value={toolFormData.config.description || ''}
                onChange={(e) => setToolFormData({ ...toolFormData, config: { ...toolFormData.config, description: e.target.value } })}
                helperText="Brief description of what this tool does"
              />
            </Grid>
            
            {/* HTTP Request Tool Fields */}
            {toolFormData.type === 'http_request' && (
              <>
                <Grid item xs={12}>
                  <TextField 
                    label="Base URL" 
                    fullWidth 
                    required
                    value={toolFormData.config.base_url || ''}
                    onChange={(e) => setToolFormData({ ...toolFormData, config: { ...toolFormData.config, base_url: e.target.value } })}
                    placeholder="https://api.example.com"
                    helperText="Base URL for HTTP requests"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField 
                    label="Auth Token (Optional)" 
                    fullWidth 
                    type="password"
                    value={toolFormData.config.auth_token || ''}
                    onChange={(e) => setToolFormData({ ...toolFormData, config: { ...toolFormData.config, auth_token: e.target.value } })}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField 
                    label="Timeout (seconds)" 
                    fullWidth 
                    type="number"
                    value={toolFormData.config.timeout || '30'}
                    onChange={(e) => setToolFormData({ ...toolFormData, config: { ...toolFormData.config, timeout: e.target.value } })}
                  />
                </Grid>
              </>
            )}

            {/* Web Search Tool Fields */}
            {toolFormData.type === 'web_search' && (
              <>
                <Grid item xs={12} md={6}>
                  <TextField 
                    label="API Key" 
                    fullWidth 
                    required
                    type="password"
                    value={toolFormData.config.api_key || ''}
                    onChange={(e) => setToolFormData({ ...toolFormData, config: { ...toolFormData.config, api_key: e.target.value } })}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField 
                    label="Endpoint" 
                    fullWidth 
                    required
                    value={toolFormData.config.endpoint || ''}
                    onChange={(e) => setToolFormData({ ...toolFormData, config: { ...toolFormData.config, endpoint: e.target.value } })}
                    placeholder="https://api.search.com/v1"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField 
                    label="Max Results" 
                    fullWidth 
                    type="number"
                    value={toolFormData.config.max_results || '10'}
                    onChange={(e) => setToolFormData({ ...toolFormData, config: { ...toolFormData.config, max_results: e.target.value } })}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField 
                    label="Provider" 
                    fullWidth 
                    value={toolFormData.config.provider || 'google'}
                    onChange={(e) => setToolFormData({ ...toolFormData, config: { ...toolFormData.config, provider: e.target.value } })}
                  />
                </Grid>
              </>
            )}

            {/* Code Executor Tool Fields */}
            {toolFormData.type === 'code_executor' && (
              <>
                <Grid item xs={12} md={6}>
                  <TextField 
                    label="Timeout (seconds)" 
                    fullWidth 
                    type="number"
                    value={toolFormData.config.timeout || '30'}
                    onChange={(e) => setToolFormData({ ...toolFormData, config: { ...toolFormData.config, timeout: e.target.value } })}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField 
                    label="Max Memory (MB)" 
                    fullWidth 
                    type="number"
                    value={toolFormData.config.max_memory || '512'}
                    onChange={(e) => setToolFormData({ ...toolFormData, config: { ...toolFormData.config, max_memory: e.target.value } })}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField 
                    label="Allowed Languages (comma-separated)" 
                    fullWidth 
                    value={toolFormData.config.allowed_languages || 'python,javascript'}
                    onChange={(e) => setToolFormData({ ...toolFormData, config: { ...toolFormData.config, allowed_languages: e.target.value } })}
                    helperText="e.g., python,javascript,bash"
                  />
                </Grid>
              </>
            )}

            {/* Custom Tool Fields */}
            {toolFormData.type === 'custom' && (
              <>
                <Grid item xs={12} md={6}>
                  <TextField 
                    label="Endpoint" 
                    fullWidth 
                    value={toolFormData.config.endpoint || ''}
                    onChange={(e) => setToolFormData({ ...toolFormData, config: { ...toolFormData.config, endpoint: e.target.value } })}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField 
                    label="Port" 
                    fullWidth 
                    value={toolFormData.config.port || ''}
                    onChange={(e) => setToolFormData({ ...toolFormData, config: { ...toolFormData.config, port: e.target.value } })}
                  />
                </Grid>
              </>
            )}

            <Grid item xs={12}>
              <FormControl component="fieldset">
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="body2">Enabled:</Typography>
                  <Chip 
                    label={toolFormData.enabled ? 'Yes' : 'No'} 
                    size="small" 
                    color={toolFormData.enabled ? 'success' : 'default'}
                    onClick={() => setToolFormData({ ...toolFormData, enabled: !toolFormData.enabled })}
                    sx={{ cursor: 'pointer' }}
                  />
                </Box>
              </FormControl>
            </Grid>

            {/* Info Alert */}
            <Grid item xs={12}>
              <Alert severity="info">
                {TOOL_TYPES.find(t => t.value === toolFormData.type)?.description || 'Configure your tool settings'}
              </Alert>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenToolDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleSaveTool} 
            variant="contained"
            disabled={!toolFormData.name || !toolFormData.type}
          >
            {editingTool ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Datasource Dialog */}
      <Dialog open={openDatasourceDialog} onClose={() => setOpenDatasourceDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>{editingDatasource ? 'Edit Data Source' : 'Add Data Source'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField label="Name" fullWidth value={datasourceFormData.name}
                onChange={(e) => setDatasourceFormData({ ...datasourceFormData, name: e.target.value })}
                disabled={!!editingDatasource} />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Type</InputLabel>
                <Select value={datasourceFormData.type} label="Type"
                  onChange={(e) => setDatasourceFormData({ ...datasourceFormData, type: e.target.value })}>
                  {DATASOURCE_TYPES.map(t => <MenuItem key={t.value} value={t.value}>{t.label}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField label="URL" fullWidth value={datasourceFormData.url}
                onChange={(e) => setDatasourceFormData({ ...datasourceFormData, url: e.target.value })}
                placeholder="http://localhost:4000" />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField label="Auth Token (Optional)" fullWidth type="password" value={datasourceFormData.auth_token}
                onChange={(e) => setDatasourceFormData({ ...datasourceFormData, auth_token: e.target.value })} />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField label="Timeout (seconds)" fullWidth type="number" value={datasourceFormData.timeout_seconds}
                onChange={(e) => setDatasourceFormData({ ...datasourceFormData, timeout_seconds: parseInt(e.target.value) })} />
            </Grid>
            {datasourceFormData.type === 'cubejs' && (
              <Grid item xs={12}>
                <Alert severity="info">
                  Cube.js datasource for analytics queries. Configure base URL and authentication header.
                </Alert>
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDatasourceDialog(false)}>Cancel</Button>
          <Button onClick={handleSaveDatasource} variant="contained" disabled={!datasourceFormData.name || !datasourceFormData.url}>
            {editingDatasource ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Test Query Dialog */}
      <Dialog open={queryDialogOpen} onClose={() => setQueryDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Test Query</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Data Source</InputLabel>
                <Select value={selectedDatasource} label="Data Source"
                  onChange={(e) => setSelectedDatasource(e.target.value)}>
                  {datasources.map(ds => <MenuItem key={ds.name} value={ds.name}>{ds.name} ({ds.type})</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField label="Query" fullWidth multiline rows={6} value={testQuery}
                onChange={(e) => setTestQuery(e.target.value)}
                placeholder="Enter your query (SQL, GraphQL, etc.)" />
            </Grid>
            {queryResult && (
              <Grid item xs={12}>
                <Paper sx={{ p: 2, background: '#1e1e1e', borderRadius: 2 }}>
                  <Typography variant="caption" color="text.secondary" gutterBottom display="block">Result:</Typography>
                  <Typography component="pre" sx={{ m: 0, color: '#d4d4d4', fontSize: '0.85rem', overflow: 'auto', maxHeight: 300 }}>
                    {JSON.stringify(queryResult, null, 2)}
                  </Typography>
                </Paper>
              </Grid>
            )}
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setQueryDialogOpen(false)}>Close</Button>
          <Button onClick={handleTestQuery} variant="contained" disabled={!selectedDatasource || !testQuery || queryLoading}
            startIcon={queryLoading ? <CircularProgress size={20} /> : <TestIcon />}>
            Execute Query
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ToolsDataSources;
