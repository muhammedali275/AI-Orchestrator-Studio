import React, { useState, useEffect } from 'react';
import {
  Typography,
  Paper,
  Button,
  Alert,
  TextField,
  Grid,
  Box,
  Card,
  CardContent,
  Chip,
  IconButton,
  Tooltip,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Cable as CableIcon,
  Build as BuildIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface ToolConfig {
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

const ToolsConfig: React.FC = () => {
  const [tools, setTools] = useState<ToolConfig[]>([]);
  const [message, setMessage] = useState('');
  const [testingTool, setTestingTool] = useState<string | null>(null);

  useEffect(() => {
    fetchTools();
  }, []);

  const fetchTools = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/tools/config');
      const fetchedTools = response.data.tools || [];
      
      // Ensure all tools have the required structure
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
    } catch (error) {
      console.error('Error fetching tools config:', error);
      // Set default tools if API fails
      setTools([
        {
          name: 'semantic_data',
          type: 'data_retrieval',
          enabled: true,
          config: {
            endpoint: '/api/query',
            port: '8080',
            api_key: '',
            timeout: '30',
          },
          status: { connected: false, message: 'Not tested' },
        },
        {
          name: 'web_search',
          type: 'search',
          enabled: true,
          config: {
            endpoint: '/search',
            port: '443',
            api_key: '',
            timeout: '30',
          },
          status: { connected: false, message: 'Not tested' },
        },
        {
          name: 'code_executor',
          type: 'execution',
          enabled: true,
          config: {
            endpoint: '/execute',
            port: '9000',
            timeout: '60',
            max_memory: '512MB',
          },
          status: { connected: false, message: 'Not tested' },
        },
      ]);
    }
  };

  const handleSaveTools = async () => {
    try {
      await axios.put('http://localhost:8000/api/tools/config', { tools });
      setMessage('Tools configuration updated successfully!');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Error saving tools config:', error);
      setMessage('Error updating tools configuration');
    }
  };

  const updateToolConfig = (index: number, key: string, value: any) => {
    const updatedTools = [...tools];
    updatedTools[index].config[key] = value;
    setTools(updatedTools);
  };

  const toggleToolEnabled = (index: number) => {
    const updatedTools = [...tools];
    updatedTools[index].enabled = !updatedTools[index].enabled;
    setTools(updatedTools);
  };

  const testToolConnection = async (index: number) => {
    const tool = tools[index];
    setTestingTool(tool.name);

    try {
      const startTime = Date.now();
      const response = await axios.post(
        'http://localhost:8000/api/tools/test-connection',
        {
          name: tool.name,
          endpoint: tool.config.endpoint,
          port: tool.config.port,
          timeout: parseInt(tool.config.timeout || '30'),
        },
        { timeout: parseInt(tool.config.timeout || '30') * 1000 }
      );

      const latency = Date.now() - startTime;
      const updatedTools = [...tools];
      
      if (response.data.success) {
        updatedTools[index].status = {
          connected: true,
          message: 'Connection successful!',
          latency,
        };
      } else {
        updatedTools[index].status = {
          connected: false,
          message: response.data.error || 'Connection failed',
        };
      }
      
      setTools(updatedTools);
    } catch (error: any) {
      const updatedTools = [...tools];
      updatedTools[index].status = {
        connected: false,
        message: error.response?.data?.detail || error.message || 'Connection failed',
      };
      setTools(updatedTools);
    } finally {
      setTestingTool(null);
    }
  };

  const addNewTool = () => {
    const newTool: ToolConfig = {
      name: 'new_tool',
      type: 'custom',
      enabled: true,
      config: {
        endpoint: '',
        port: '',
        api_key: '',
        timeout: '30',
      },
      status: { connected: false, message: 'Not tested' },
    };
    setTools([...tools, newTool]);
  };

  const deleteTool = (index: number) => {
    const updatedTools = tools.filter((_, i) => i !== index);
    setTools(updatedTools);
  };

  const getToolIcon = (type: string) => {
    return <BuildIcon sx={{ color: '#667eea' }} />;
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
          Tools Configuration
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Configure integration tools and test connectivity
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

      {/* Tools List */}
      <Box sx={{ mb: 3 }}>
        {tools.map((tool, index) => (
          <Accordion
            key={index}
            sx={{
              mb: 2,
              background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.02) 0%, rgba(118, 75, 162, 0.02) 100%)',
              border: '1px solid rgba(102, 126, 234, 0.1)',
              '&:before': { display: 'none' },
            }}
          >
            <AccordionSummary
              expandIcon={<ExpandMoreIcon />}
              sx={{
                '&:hover': {
                  background: 'rgba(102, 126, 234, 0.05)',
                },
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%', mr: 2 }}>
                {getToolIcon(tool.type)}
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    {tool.name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {tool.type}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {tool.status?.latency && (
                    <Chip
                      icon={<SpeedIcon />}
                      label={`${tool.status.latency}ms`}
                      size="small"
                      sx={{
                        background: 'rgba(102, 126, 234, 0.2)',
                        color: '#667eea',
                        fontWeight: 600,
                      }}
                    />
                  )}
                  <Chip
                    icon={tool.status?.connected ? <CheckCircleIcon /> : <ErrorIcon />}
                    label={tool.status?.connected ? 'Connected' : 'Disconnected'}
                    size="small"
                    color={tool.status?.connected ? 'success' : 'error'}
                    sx={{ fontWeight: 600 }}
                  />
                  <Chip
                    label={tool.enabled ? 'Enabled' : 'Disabled'}
                    size="small"
                    color={tool.enabled ? 'success' : 'default'}
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleToolEnabled(index);
                    }}
                    sx={{ fontWeight: 600, cursor: 'pointer' }}
                  />
                </Box>
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={2}>
                {/* Tool Name */}
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Tool Name"
                    value={tool.name}
                    onChange={(e) => {
                      const updatedTools = [...tools];
                      updatedTools[index].name = e.target.value;
                      setTools(updatedTools);
                    }}
                    size="small"
                    fullWidth
                  />
                </Grid>

                {/* Tool Type */}
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Tool Type"
                    value={tool.type}
                    onChange={(e) => {
                      const updatedTools = [...tools];
                      updatedTools[index].type = e.target.value;
                      setTools(updatedTools);
                    }}
                    size="small"
                    fullWidth
                  />
                </Grid>

                {/* Endpoint */}
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Endpoint"
                    value={tool.config.endpoint || ''}
                    onChange={(e) => updateToolConfig(index, 'endpoint', e.target.value)}
                    size="small"
                    fullWidth
                    placeholder="/api/endpoint"
                  />
                </Grid>

                {/* Port */}
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Port"
                    value={tool.config.port || ''}
                    onChange={(e) => updateToolConfig(index, 'port', e.target.value)}
                    size="small"
                    fullWidth
                    placeholder="8080"
                    type="number"
                  />
                </Grid>

                {/* API Key */}
                {tool.config.api_key !== undefined && (
                  <Grid item xs={12}>
                    <TextField
                      label="API Key"
                      value={tool.config.api_key || ''}
                      onChange={(e) => updateToolConfig(index, 'api_key', e.target.value)}
                      size="small"
                      fullWidth
                      type="password"
                      placeholder="Enter API key if required"
                    />
                  </Grid>
                )}

                {/* Timeout */}
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Timeout (seconds)"
                    value={tool.config.timeout || '30'}
                    onChange={(e) => updateToolConfig(index, 'timeout', e.target.value)}
                    size="small"
                    fullWidth
                    type="number"
                  />
                </Grid>

                {/* Additional Config Fields */}
                {Object.entries(tool.config).map(([key, value]) => {
                  if (['endpoint', 'port', 'api_key', 'timeout'].includes(key)) return null;
                  return (
                    <Grid item xs={12} md={6} key={key}>
                      <TextField
                        label={key.replace(/_/g, ' ').toUpperCase()}
                        value={value}
                        onChange={(e) => updateToolConfig(index, key, e.target.value)}
                        size="small"
                        fullWidth
                      />
                    </Grid>
                  );
                })}

                {/* Status Message */}
                {tool.status && (
                  <Grid item xs={12}>
                    <Box
                      sx={{
                        p: 2,
                        borderRadius: 2,
                        background: tool.status.connected
                          ? 'rgba(16, 185, 129, 0.1)'
                          : 'rgba(239, 68, 68, 0.1)',
                        border: `1px solid ${
                          tool.status.connected ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'
                        }`,
                      }}
                    >
                      <Typography variant="body2" color="text.secondary">
                        {tool.status.message}
                      </Typography>
                    </Box>
                  </Grid>
                )}

                {/* Action Buttons */}
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', gap: 2, mt: 1 }}>
                    <Button
                      variant="outlined"
                      onClick={() => testToolConnection(index)}
                      disabled={testingTool === tool.name || !tool.config.endpoint}
                      startIcon={testingTool === tool.name ? <CircularProgress size={20} /> : <CableIcon />}
                      sx={{
                        borderColor: '#667eea',
                        color: '#667eea',
                        '&:hover': {
                          borderColor: '#764ba2',
                          background: 'rgba(102, 126, 234, 0.1)',
                        },
                      }}
                    >
                      {testingTool === tool.name ? 'Testing...' : 'Test Connection'}
                    </Button>
                    <Tooltip title="Delete Tool">
                      <IconButton
                        onClick={() => deleteTool(index)}
                        sx={{
                          ml: 'auto',
                          color: '#ef4444',
                          '&:hover': {
                            background: 'rgba(239, 68, 68, 0.1)',
                          },
                        }}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Grid>
              </Grid>
            </AccordionDetails>
          </Accordion>
        ))}
      </Box>

      {/* Action Buttons */}
      <Box sx={{ display: 'flex', gap: 2 }}>
        <Button
          variant="outlined"
          onClick={addNewTool}
          startIcon={<AddIcon />}
          sx={{
            borderColor: '#667eea',
            color: '#667eea',
            '&:hover': {
              borderColor: '#764ba2',
              background: 'rgba(102, 126, 234, 0.1)',
            },
          }}
        >
          Add New Tool
        </Button>
        <Button
          variant="contained"
          onClick={handleSaveTools}
          sx={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          }}
        >
          Save All Tools
        </Button>
      </Box>
    </Box>
  );
};

export default ToolsConfig;
