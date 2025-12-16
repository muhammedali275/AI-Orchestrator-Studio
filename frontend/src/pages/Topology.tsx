import React, { useState, useEffect } from 'react';
import { 
  Typography, Paper, Box, Chip, Card, CardContent, IconButton, Tooltip, 
  Button, LinearProgress, Alert, CircularProgress, Dialog, DialogTitle, 
  DialogContent, DialogActions, List, ListItem, ListItemText, Divider,
  Drawer, TextField, Switch, FormControlLabel, Grid,
} from '@mui/material';
import {
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Router as RouterIcon,
  Psychology as LLMIcon,
  Build as ToolIcon,
  CheckCircle as EndIcon,
  Refresh as RefreshIcon,
  ArrowForward as ArrowIcon,
  BugReport as TestIcon,
  Error as ErrorIcon,
  FactCheck,
  Assessment,
  Storage as StorageIcon,
  Psychology,
  Close as CloseIcon,
  Save as SaveIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface GraphNode {
  id: string;
  type: string;
  label: string;
  description: string;
  status: string;
  config?: any;
}

interface GraphEdge {
  source: string;
  target: string;
  label: string;
}

interface ExecutionStatus {
  execution_id: string;
  status: string;
  current_node: string | null;
  progress: number;
  error: string | null;
  logs: Array<{
    timestamp: string;
    level: string;
    message: string;
    node: string;
  }>;
}

interface NodeConfig {
  enabled: boolean;
  timeout?: number;
  retry_count?: number;
  [key: string]: any;
}

const Topology: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [executing, setExecuting] = useState(false);
  const [executionStatus, setExecutionStatus] = useState<ExecutionStatus | null>(null);
  const [showLogs, setShowLogs] = useState(false);
  const [testingComponent, setTestingComponent] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<any>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [nodeConfig, setNodeConfig] = useState<NodeConfig>({
    enabled: true,
    timeout: 30,
    retry_count: 3,
  });
  const [showConfigPanel, setShowConfigPanel] = useState(false);

  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'start':
        return <StartIcon sx={{ fontSize: 40, color: '#10b981' }} />;
      case 'router':
      case 'intent_router':
        return <RouterIcon sx={{ fontSize: 40, color: '#667eea' }} />;
      case 'llm':
      case 'llm_agent':
        return <LLMIcon sx={{ fontSize: 40, color: '#f093fb' }} />;
      case 'external_agent':
        return <LLMIcon sx={{ fontSize: 40, color: '#9333ea' }} />;
      case 'tools':
      case 'tool_executor':
        return <ToolIcon sx={{ fontSize: 40, color: '#4facfe' }} />;
      case 'planner':
        return <Psychology sx={{ fontSize: 40, color: '#ec4899' }} />;
      case 'grounding':
        return <FactCheck sx={{ fontSize: 40, color: '#f59e0b' }} />;
      case 'memory_store':
        return <StorageIcon sx={{ fontSize: 40, color: '#3b82f6' }} />;
      case 'audit':
        return <Assessment sx={{ fontSize: 40, color: '#8b5cf6' }} />;
      case 'end':
        return <EndIcon sx={{ fontSize: 40, color: '#fa709a' }} />;
      case 'error_handler':
        return <ErrorIcon sx={{ fontSize: 40, color: '#ef4444' }} />;
      default:
        return null;
    }
  };

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'start':
        return '#10b981';
      case 'router':
      case 'intent_router':
        return '#667eea';
      case 'llm':
      case 'llm_agent':
        return '#f093fb';
      case 'external_agent':
        return '#9333ea';
      case 'tools':
      case 'tool_executor':
        return '#4facfe';
      case 'planner':
        return '#ec4899';
      case 'grounding':
        return '#f59e0b';
      case 'memory_store':
        return '#3b82f6';
      case 'audit':
        return '#8b5cf6';
      case 'end':
        return '#fa709a';
      case 'error_handler':
        return '#ef4444';
      default:
        return '#a1a1aa';
    }
  };

  const fetchGraph = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/api/topology/graph', { timeout: 5000 });
      const graphData = response.data;
      
      if (graphData.nodes && graphData.nodes.length > 0) {
        setNodes(graphData.nodes);
        setEdges(graphData.edges || []);
      } else {
        // Use fallback data if no nodes returned
        loadFallbackGraph();
      }
    } catch (error) {
      console.error('Error fetching graph:', error);
      // Load fallback graph on error
      loadFallbackGraph();
    } finally {
      setLoading(false);
    }
  };

  const loadFallbackGraph = () => {
    // Default 11-node topology
    const fallbackNodes: GraphNode[] = [
      { id: 'start', type: 'start', label: 'Start', description: 'Entry point', status: 'idle', config: {} },
      { id: 'router', type: 'router', label: 'Intent Router', description: 'Route based on intent', status: 'idle', config: { confidence_threshold: 0.7 } },
      { id: 'planner', type: 'planner', label: 'Task Planner', description: 'Break down complex tasks', status: 'idle', config: {} },
      { id: 'llm_agent', type: 'llm_agent', label: 'LLM Agent', description: 'Primary LLM reasoning', status: 'idle', config: { temperature: 0.7, max_tokens: 2000 } },
      { id: 'external_agent', type: 'external_agent', label: 'External Agent', description: 'Specialized agent', status: 'idle', config: {} },
      { id: 'tool_executor', type: 'tool_executor', label: 'Tool Executor', description: 'Execute tools', status: 'idle', config: { max_parallel: 3 } },
      { id: 'grounding', type: 'grounding', label: 'Data Grounding', description: 'Ground with data sources', status: 'idle', config: {} },
      { id: 'memory_store', type: 'memory_store', label: 'Memory Store', description: 'Store conversation context', status: 'idle', config: { max_items: 50 } },
      { id: 'audit', type: 'audit', label: 'Audit Logger', description: 'Log all interactions', status: 'idle', config: {} },
      { id: 'error_handler', type: 'error_handler', label: 'Error Handler', description: 'Handle errors gracefully', status: 'idle', config: {} },
      { id: 'end', type: 'end', label: 'End', description: 'Final response', status: 'idle', config: {} },
    ];
    
    const fallbackEdges: GraphEdge[] = [
      { source: 'start', target: 'router', label: 'Initial' },
      { source: 'router', target: 'planner', label: 'Complex Task' },
      { source: 'router', target: 'llm_agent', label: 'Simple Query' },
      { source: 'planner', target: 'llm_agent', label: 'Planned Steps' },
      { source: 'llm_agent', target: 'tool_executor', label: 'Need Tools' },
      { source: 'llm_agent', target: 'external_agent', label: 'Need Specialist' },
      { source: 'tool_executor', target: 'grounding', label: 'Get Data' },
      { source: 'external_agent', target: 'grounding', label: 'Verify' },
      { source: 'grounding', target: 'memory_store', label: 'Store Context' },
      { source: 'memory_store', target: 'audit', label: 'Log' },
      { source: 'audit', target: 'end', label: 'Complete' },
    ];
    
    setNodes(fallbackNodes);
    setEdges(fallbackEdges);
  };

  const startExecution = async () => {
    try {
      setExecuting(true);
      const response = await axios.post('http://localhost:8000/api/topology/execute', {
        input_data: {},
        test_mode: true,
      });
      if (response.data.success) {
        pollExecutionStatus(response.data.execution_id);
      }
    } catch (error) {
      console.error('Error starting execution:', error);
      setExecuting(false);
    }
  };

  const pollExecutionStatus = async (executionId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`http://localhost:8000/api/topology/execution/${executionId}`);
        setExecutionStatus(response.data);
        
        if (response.data.current_node) {
          setNodes((prevNodes) =>
            prevNodes.map((node) => ({
              ...node,
              status: node.id === response.data.current_node ? 'active' : 
                      node.status === 'active' ? 'completed' : node.status,
            }))
          );
        }
        
        if (['completed', 'failed', 'stopped'].includes(response.data.status)) {
          clearInterval(interval);
          setExecuting(false);
        }
      } catch (error) {
        clearInterval(interval);
        setExecuting(false);
      }
    }, 1000);
  };

  const stopExecution = async () => {
    if (executionStatus) {
      try {
        await axios.delete(`http://localhost:8000/api/topology/execution/${executionStatus.execution_id}`);
        setExecuting(false);
      } catch (error) {
        console.error('Error stopping execution:', error);
      }
    }
  };

  const testComponent = async (componentId: string) => {
    setTestingComponent(componentId);
    try {
      const response = await axios.post('http://localhost:8000/api/topology/test-component', {
        component_id: componentId,
      });
      setTestResults({ success: true, output: response.data });
    } catch (error: any) {
      setTestResults({ success: false, error: error.message || 'Test failed' });
    } finally {
      setTestingComponent(null);
    }
  };

  const handleNodeClick = (node: GraphNode) => {
    setSelectedNode(node);
    setShowConfigPanel(true);
    setNodeConfig({
      enabled: node.config?.enabled ?? true,
      timeout: node.config?.timeout ?? 30,
      retry_count: node.config?.retry_count ?? 3,
      ...node.config,
    });
  };

  const saveNodeConfig = async () => {
    if (!selectedNode) return;
    try {
      await axios.put(`http://localhost:8000/api/topology/nodes/${selectedNode.id}/config`, nodeConfig);
      // Update local state
      const updatedNodes = nodes.map(n => 
        n.id === selectedNode.id ? { ...n, config: nodeConfig } : n
      );
      setNodes(updatedNodes);
      setShowConfigPanel(false);
    } catch (error) {
      console.error('Error saving node config:', error);
    }
  };

  useEffect(() => {
    fetchGraph();
  }, []);

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
            Orchestrator Topology
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Real-time workflow execution and monitoring
          </Typography>
        </Box>
        <Tooltip title="Refresh Topology">
          <IconButton
            onClick={fetchGraph}
            disabled={loading || executing}
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              '&:hover': {
                background: 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)',
                transform: 'rotate(180deg)',
              },
              transition: 'all 0.5s ease-in-out',
            }}
          >
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>

      {/* Execution Controls */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Flow Execution
          </Typography>
          <Box sx={{ display: 'flex', gap: 2 }}>
            {!executing ? (
              <Button
                variant="contained"
                startIcon={<StartIcon />}
                onClick={startExecution}
                sx={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' }}
              >
                Start Flow
              </Button>
            ) : (
              <Button
                variant="contained"
                startIcon={<StopIcon />}
                onClick={stopExecution}
                sx={{ background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)' }}
              >
                Stop Flow
              </Button>
            )}
            <Button variant="outlined" onClick={() => setShowLogs(true)} disabled={!executionStatus}>
              View Logs
            </Button>
          </Box>
        </Box>

        {executionStatus && (
          <Box>
            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <Chip
                label={executionStatus.status.toUpperCase()}
                sx={{
                  background: executionStatus.status === 'running' ? '#3b82f620' : 
                             executionStatus.status === 'completed' ? '#10b98120' : '#ef444420',
                  color: executionStatus.status === 'running' ? '#3b82f6' : 
                         executionStatus.status === 'completed' ? '#10b981' : '#ef4444',
                  fontWeight: 600,
                }}
              />
              {executionStatus.current_node && (
                <Chip label={`Current: ${executionStatus.current_node}`} 
                      sx={{ background: 'rgba(102, 126, 234, 0.2)', color: '#667eea', fontWeight: 600 }} />
              )}
            </Box>
            <LinearProgress variant="determinate" value={executionStatus.progress}
              sx={{
                height: 8, borderRadius: 4, backgroundColor: 'rgba(102, 126, 234, 0.1)',
                '& .MuiLinearProgress-bar': { background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)' },
              }}
            />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Progress: {executionStatus.progress.toFixed(1)}%
            </Typography>
            {executionStatus.error && (
              <Alert severity="error" sx={{ mt: 2 }}>{executionStatus.error}</Alert>
            )}
          </Box>
        )}
      </Paper>

      {/* Legend */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        {[
          { label: 'Start/End', color: '#10b981' },
          { label: 'Router', color: '#667eea' },
          { label: 'LLM Agent', color: '#f093fb' },
          { label: 'Tools', color: '#4facfe' },
        ].map((item) => (
          <Chip
            key={item.label}
            label={item.label}
            sx={{
              background: `linear-gradient(135deg, ${item.color} 0%, ${item.color}dd 100%)`,
              color: 'white',
              fontWeight: 600,
              boxShadow: `0 0 12px ${item.color}40`,
            }}
          />
        ))}
      </Box>

      {/* Workflow Visualization */}
      <Paper
        sx={{
          p: 4,
          background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.02) 0%, rgba(118, 75, 162, 0.02) 100%)',
          border: '1px solid rgba(102, 126, 234, 0.1)',
          minHeight: '500px',
        }}
      >
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 4 }}>
          Workflow Flow
        </Typography>
        
        {/* Vertical Flow */}
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
          {nodes.map((node, index) => (
            <React.Fragment key={node.id}>
              {/* Node Card */}
              <Card
                className="card-hover"
                onClick={() => handleNodeClick(node)}
                sx={{
                  width: '100%',
                  maxWidth: 600,
                  background: `linear-gradient(135deg, ${getNodeColor(node.type)}15 0%, ${getNodeColor(node.type)}25 100%)`,
                  border: `2px solid ${getNodeColor(node.type)}`,
                  boxShadow: `0 0 20px ${getNodeColor(node.type)}40`,
                  cursor: 'pointer',
                  transition: 'all 0.3s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: `0 8px 32px ${getNodeColor(node.type)}60`,
                  },
                }}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    {getNodeIcon(node.type)}
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="h6" sx={{ fontWeight: 700, color: getNodeColor(node.type) }}>
                        {node.label}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {node.description}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Chip label={node.type} size="small"
                        sx={{ background: getNodeColor(node.type), color: 'white', fontWeight: 600 }} />
                      {node.status !== 'idle' && (
                        <Chip label={node.status} size="small"
                          sx={{ 
                            background: node.status === 'active' ? '#3b82f620' : 
                                       node.status === 'completed' ? '#10b98120' : '#ef444420',
                            color: node.status === 'active' ? '#3b82f6' : 
                                   node.status === 'completed' ? '#10b981' : '#ef4444',
                            fontWeight: 600 
                          }} />
                      )}
                      <Tooltip title="Test Component">
                        <IconButton size="small" onClick={() => testComponent(node.id)}
                          disabled={testingComponent === node.id}
                          sx={{ background: 'rgba(102, 126, 234, 0.1)' }}>
                          {testingComponent === node.id ? <CircularProgress size={16} /> : <TestIcon fontSize="small" />}
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Configure Node">
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleNodeClick(node);
                          }}
                          sx={{ background: 'rgba(102, 126, 234, 0.1)' }}
                        >
                          <SettingsIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </Box>
                </CardContent>
              </Card>

              {/* Arrow between nodes */}
              {index < nodes.length - 1 && (
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: 0.5,
                  }}
                >
                  <ArrowIcon
                    sx={{
                      fontSize: 40,
                      color: '#667eea',
                      transform: 'rotate(90deg)',
                      animation: 'pulse 2s ease-in-out infinite',
                    }}
                  />
                  {edges.find(e => e.source === node.id) && (
                    <Chip
                      label={edges.find(e => e.source === node.id)?.label}
                      size="small"
                      sx={{
                        background: 'rgba(102, 126, 234, 0.2)',
                        color: '#667eea',
                        fontWeight: 600,
                        fontSize: '0.7rem',
                      }}
                    />
                  )}
                </Box>
              )}
            </React.Fragment>
          ))}
        </Box>
      </Paper>

      {/* Connection Details */}
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
          Flow Connections
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 2 }}>
          {edges.map((edge, index) => (
            <Box
              key={index}
              sx={{
                p: 2,
                borderRadius: 2,
                background: 'rgba(102, 126, 234, 0.05)',
                border: '1px solid rgba(102, 126, 234, 0.1)',
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                transition: 'all 0.25s ease-in-out',
                '&:hover': {
                  background: 'rgba(102, 126, 234, 0.1)',
                  transform: 'translateX(4px)',
                },
              }}
            >
              <Typography variant="body2" fontWeight={600}>
                {nodes.find(n => n.id === edge.source)?.label}
              </Typography>
              <ArrowIcon sx={{ fontSize: 20, color: '#667eea' }} />
              <Typography variant="body2" fontWeight={600}>
                {nodes.find(n => n.id === edge.target)?.label}
              </Typography>
              <Chip
                label={edge.label}
                size="small"
                sx={{
                  ml: 'auto',
                  background: 'rgba(102, 126, 234, 0.2)',
                  color: '#667eea',
                  fontWeight: 600,
                }}
              />
            </Box>
          ))}
        </Box>
      </Paper>

      {/* Logs Dialog */}
      <Dialog open={showLogs} onClose={() => setShowLogs(false)} maxWidth="md" fullWidth>
        <DialogTitle>Execution Logs</DialogTitle>
        <DialogContent>
          {executionStatus && executionStatus.logs.length > 0 ? (
            <List>
              {executionStatus.logs.map((log, index) => (
                <React.Fragment key={index}>
                  <ListItem>
                    <ListItemText
                      primary={log.message}
                      secondary={`${new Date(log.timestamp).toLocaleTimeString()} - ${log.node} - ${log.level}`}
                      primaryTypographyProps={{
                        color: log.level === 'error' ? 'error' : log.level === 'warning' ? 'warning' : 'text.primary',
                      }}
                    />
                  </ListItem>
                  {index < executionStatus.logs.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          ) : (
            <Typography color="text.secondary">No logs available</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowLogs(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Test Results Dialog */}
      <Dialog open={testResults !== null} onClose={() => setTestResults(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Component Test Results</DialogTitle>
        <DialogContent>
          {testResults && (
            <Box>
              <Alert severity={testResults.success ? 'success' : 'error'} sx={{ mb: 2 }}>
                {testResults.success ? 'Component is healthy' : 'Component test failed'}
              </Alert>
              {testResults.error && (
                <Typography variant="body2" color="error">
                  Error: {testResults.error}
                </Typography>
              )}
              {testResults.output && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="caption" color="text.secondary">Output:</Typography>
                  <Box
                    component="pre"
                    sx={{
                      p: 2,
                      background: 'rgba(0, 0, 0, 0.05)',
                      borderRadius: 1,
                      overflow: 'auto',
                      fontSize: '0.8rem',
                      mt: 1,
                    }}
                  >
                    {JSON.stringify(testResults.output, null, 2)}
                  </Box>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestResults(null)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Node Configuration Drawer */}
      <Drawer
        anchor="right"
        open={showConfigPanel}
        onClose={() => setShowConfigPanel(false)}
        PaperProps={{
          sx: {
            width: 400,
            p: 3,
          },
        }}
      >
        {selectedNode && (
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Configure Node
              </Typography>
              <IconButton onClick={() => setShowConfigPanel(false)}>
                <CloseIcon />
              </IconButton>
            </Box>

            <Divider sx={{ mb: 3 }} />

            {/* Node Info */}
            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                {getNodeIcon(selectedNode.type)}
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 700, color: getNodeColor(selectedNode.type) }}>
                    {selectedNode.label}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {selectedNode.type}
                  </Typography>
                </Box>
              </Box>
              <Typography variant="body2" color="text.secondary">
                {selectedNode.description}
              </Typography>
            </Box>

            <Divider sx={{ mb: 3 }} />

            {/* Configuration Form */}
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={nodeConfig.enabled}
                    onChange={(e) => setNodeConfig({ ...nodeConfig, enabled: e.target.checked })}
                  />
                }
                label="Node Enabled"
              />

              <TextField
                label="Timeout (seconds)"
                type="number"
                value={nodeConfig.timeout}
                onChange={(e) => setNodeConfig({ ...nodeConfig, timeout: parseInt(e.target.value) || 30 })}
                fullWidth
              />

              <TextField
                label="Retry Count"
                type="number"
                value={nodeConfig.retry_count}
                onChange={(e) => setNodeConfig({ ...nodeConfig, retry_count: parseInt(e.target.value) || 3 })}
                fullWidth
              />

              {/* Node-specific configuration */}
              {selectedNode.type === 'llm_agent' && (
                <>
                  <TextField
                    label="Model"
                    value={nodeConfig.model || ''}
                    onChange={(e) => setNodeConfig({ ...nodeConfig, model: e.target.value })}
                    fullWidth
                  />
                  <TextField
                    label="Temperature"
                    type="number"
                    inputProps={{ step: 0.1, min: 0, max: 2 }}
                    value={nodeConfig.temperature || 0.7}
                    onChange={(e) => setNodeConfig({ ...nodeConfig, temperature: parseFloat(e.target.value) || 0.7 })}
                    fullWidth
                  />
                  <TextField
                    label="Max Tokens"
                    type="number"
                    value={nodeConfig.max_tokens || 1000}
                    onChange={(e) => setNodeConfig({ ...nodeConfig, max_tokens: parseInt(e.target.value) || 1000 })}
                    fullWidth
                  />
                </>
              )}

              {selectedNode.type === 'tool_executor' && (
                <>
                  <TextField
                    label="Max Parallel Tools"
                    type="number"
                    value={nodeConfig.max_parallel || 3}
                    onChange={(e) => setNodeConfig({ ...nodeConfig, max_parallel: parseInt(e.target.value) || 3 })}
                    fullWidth
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={nodeConfig.allow_dangerous || false}
                        onChange={(e) => setNodeConfig({ ...nodeConfig, allow_dangerous: e.target.checked })}
                      />
                    }
                    label="Allow Dangerous Operations"
                  />
                </>
              )}

              {selectedNode.type === 'intent_router' && (
                <>
                  <TextField
                    label="Confidence Threshold"
                    type="number"
                    inputProps={{ step: 0.1, min: 0, max: 1 }}
                    value={nodeConfig.confidence_threshold || 0.7}
                    onChange={(e) => setNodeConfig({ ...nodeConfig, confidence_threshold: parseFloat(e.target.value) || 0.7 })}
                    fullWidth
                  />
                </>
              )}

              {selectedNode.type === 'memory_store' && (
                <>
                  <TextField
                    label="Max Memory Items"
                    type="number"
                    value={nodeConfig.max_items || 50}
                    onChange={(e) => setNodeConfig({ ...nodeConfig, max_items: parseInt(e.target.value) || 50 })}
                    fullWidth
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={nodeConfig.enable_summary || true}
                        onChange={(e) => setNodeConfig({ ...nodeConfig, enable_summary: e.target.checked })}
                      />
                    }
                    label="Enable Summary"
                  />
                </>
              )}
            </Box>

            {/* Action Buttons */}
            <Box sx={{ mt: 4, display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                startIcon={<SaveIcon />}
                onClick={saveNodeConfig}
                sx={{
                  flex: 1,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)',
                  },
                }}
              >
                Save Configuration
              </Button>
              <Button
                variant="outlined"
                onClick={() => setShowConfigPanel(false)}
                sx={{ flex: 1 }}
              >
                Cancel
              </Button>
            </Box>

            {/* Configuration JSON Preview */}
            <Box sx={{ mt: 3 }}>
              <Typography variant="caption" color="text.secondary" gutterBottom>
                Configuration JSON:
              </Typography>
              <Paper
                sx={{
                  p: 2,
                  mt: 1,
                  background: 'rgba(0, 0, 0, 0.05)',
                  maxHeight: 200,
                  overflow: 'auto',
                }}
              >
                <pre style={{ margin: 0, fontSize: '0.75rem' }}>
                  {JSON.stringify(nodeConfig, null, 2)}
                </pre>
              </Paper>
            </Box>
          </Box>
        )}
      </Drawer>
    </Box>
  );
};

export default Topology;
