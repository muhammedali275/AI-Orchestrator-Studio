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
  Accordion,
  AccordionSummary,
  AccordionDetails,
  OutlinedInput,
  SelectChangeEvent,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Psychology as PsychologyIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  ExpandMore as ExpandMoreIcon,
  Cable as CableIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface Agent {
  name: string;
  url: string;
  auth_token?: string;
  timeout_seconds: number;
  enabled: boolean;
  metadata: {
    system_prompt?: string;
    llm_connection?: string;
    attached_tools?: string[];
    langgraph_profile?: string;
  };
}

interface LLMConnection {
  id: string;
  name: string;
}

interface Tool {
  name: string;
  type: string;
}

const SYSTEM_PROMPT_TEMPLATE = `You are an intelligent AI assistant with access to various tools and data sources.

Your responsibilities include:
1. Query Translation: Understand user intent and translate natural language queries into structured requests
2. Tool Routing: Determine which tools are needed to fulfill the request
   - For "top churn contracts" queries, use the Cube.js tool to query analytics data
   - For general information, use web search or knowledge base tools
   - For code execution, use the code executor tool
3. Grounding: Verify responses against source data and re-check if needed
4. Context Management: Maintain conversation context and use memory effectively

Always:
- Provide accurate, well-sourced responses
- Explain your reasoning when using tools
- Ask for clarification when queries are ambiguous
- Cite sources when providing factual information`;

const AgentsConfig: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [llmConnections, setLlmConnections] = useState<LLMConnection[]>([]);
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);
  const [testingAgent, setTestingAgent] = useState<string | null>(null);

  const [formData, setFormData] = useState<Agent>({
    name: '',
    url: '',
    auth_token: '',
    timeout_seconds: 30,
    enabled: true,
    metadata: {
      system_prompt: SYSTEM_PROMPT_TEMPLATE,
      llm_connection: '',
      attached_tools: [],
      langgraph_profile: 'default',
    },
  });

  useEffect(() => {
    fetchAgents();
    fetchLLMConnections();
    fetchTools();
  }, []);

  const fetchAgents = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/api/agents');
      setAgents(response.data || []);
    } catch (error) {
      console.error('Error fetching agents:', error);
      setMessage('Error loading agents');
    } finally {
      setLoading(false);
    }
  };

  const fetchLLMConnections = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/config/llm-connections');
      const conns = (response.data?.connections || []).map((c: any) => ({ id: c.id, name: c.name || c.id }));
      if (conns.length > 0) {
        setLlmConnections(conns);
      } else {
        // Fallback: derive from single-config if present
        const single = await axios.get('http://localhost:8000/api/llm/config');
        const base = single.data?.base_url ? [{ id: 'default', name: 'Default LLM' }] : [];
        setLlmConnections(base.length ? base : [
          { id: 'local_ollama', name: 'Local Ollama' },
          { id: 'azure_openai', name: 'Azure OpenAI' },
          { id: 'openai_gpt4', name: 'OpenAI GPT-4' },
        ]);
      }
    } catch (error) {
      console.error('Error fetching LLM connections:', error);
      // Keep minimal mock for UI continuity
      setLlmConnections([
        { id: 'local_ollama', name: 'Local Ollama' },
        { id: 'azure_openai', name: 'Azure OpenAI' },
        { id: 'openai_gpt4', name: 'OpenAI GPT-4' },
      ]);
    }
  };

  const fetchTools = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/tools');
      setTools(response.data || []);
    } catch (error) {
      console.error('Error fetching tools:', error);
      setTools([]);
    }
  };

  const handleOpenDialog = (agent?: Agent) => {
    if (agent) {
      setEditingAgent(agent);
      setFormData(agent);
    } else {
      setEditingAgent(null);
      setFormData({
        name: '',
        url: '',
        auth_token: '',
        timeout_seconds: 30,
        enabled: true,
        metadata: {
          system_prompt: SYSTEM_PROMPT_TEMPLATE,
          llm_connection: '',
          attached_tools: [],
          langgraph_profile: 'default',
        },
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingAgent(null);
  };

  const handleSaveAgent = async () => {
    try {
      if (editingAgent) {
        await axios.put(`http://localhost:8000/api/agents/${editingAgent.name}`, formData);
        setMessage('Agent updated successfully!');
      } else {
        await axios.post('http://localhost:8000/api/agents', formData);
        setMessage('Agent created successfully!');
      }
      fetchAgents();
      handleCloseDialog();
      setTimeout(() => setMessage(''), 3000);
    } catch (error: any) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleDeleteAgent = async (name: string) => {
    if (!window.confirm(`Are you sure you want to delete agent "${name}"?`)) return;
    
    try {
      await axios.delete(`http://localhost:8000/api/agents/${name}`);
      setMessage('Agent deleted successfully!');
      fetchAgents();
      setTimeout(() => setMessage(''), 3000);
    } catch (error: any) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleTestAgent = async (name: string) => {
    setTestingAgent(name);
    try {
      const response = await axios.post(`http://localhost:8000/api/agents/${name}/test`);
      if (response.data.success) {
        setMessage(`Agent "${name}" is healthy!`);
      } else {
        setMessage(`Agent "${name}" test failed: ${response.data.message}`);
      }
      setTimeout(() => setMessage(''), 3000);
    } catch (error: any) {
      setMessage(`Error testing agent: ${error.response?.data?.detail || error.message}`);
    } finally {
      setTestingAgent(null);
    }
  };

  const handleToolsChange = (event: SelectChangeEvent<string[]>) => {
    const value = event.target.value;
    setFormData({
      ...formData,
      metadata: {
        ...formData.metadata,
        attached_tools: typeof value === 'string' ? value.split(',') : value,
      },
    });
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
            Agents & System Prompts
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Configure AI agents with system prompts, LLM connections, and tools
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Tooltip title="Refresh Agents">
            <IconButton
              onClick={fetchAgents}
              disabled={loading}
              sx={{
                background: 'rgba(102, 126, 234, 0.1)',
                '&:hover': { background: 'rgba(102, 126, 234, 0.2)' },
              }}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
            sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
          >
            Add Agent
          </Button>
        </Box>
      </Box>

      {/* Messages */}
      {message && (
        <Alert
          severity={message.includes('Error') ? 'error' : 'success'}
          sx={{ mb: 3 }}
          onClose={() => setMessage('')}
        >
          {message}
        </Alert>
      )}

      {/* Agents List */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : agents.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <PsychologyIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No agents configured
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Create your first agent to get started
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
            sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
          >
            Add Agent
          </Button>
        </Paper>
      ) : (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {agents.map((agent) => (
            <Accordion
              key={agent.name}
              sx={{
                background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.02) 0%, rgba(118, 75, 162, 0.02) 100%)',
                border: '1px solid rgba(102, 126, 234, 0.1)',
                '&:before': { display: 'none' },
              }}
            >
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%', mr: 2 }}>
                  <PsychologyIcon sx={{ color: '#667eea' }} />
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {agent.name}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {agent.url}
                    </Typography>
                  </Box>
                  <Chip
                    label={agent.enabled ? 'Enabled' : 'Disabled'}
                    size="small"
                    color={agent.enabled ? 'success' : 'default'}
                    sx={{ fontWeight: 600 }}
                  />
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={3}>
                  {/* System Prompt */}
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
                      System Prompt
                    </Typography>
                    <Paper
                      sx={{
                        p: 2,
                        background: 'rgba(102, 126, 234, 0.05)',
                        border: '1px solid rgba(102, 126, 234, 0.1)',
                        maxHeight: 200,
                        overflow: 'auto',
                      }}
                    >
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                        {agent.metadata.system_prompt || 'No system prompt configured'}
                      </Typography>
                    </Paper>
                  </Grid>

                  {/* Configuration Details */}
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
                      LLM Connection
                    </Typography>
                    <Chip
                      label={agent.metadata.llm_connection || 'Not configured'}
                      sx={{ background: 'rgba(102, 126, 234, 0.2)', color: '#667eea' }}
                    />
                  </Grid>

                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
                      LangGraph Profile
                    </Typography>
                    <Chip
                      label={agent.metadata.langgraph_profile || 'default'}
                      sx={{ background: 'rgba(118, 75, 162, 0.2)', color: '#764ba2' }}
                    />
                  </Grid>

                  <Grid item xs={12}>
                    <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
                      Attached Tools
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {agent.metadata.attached_tools && agent.metadata.attached_tools.length > 0 ? (
                        agent.metadata.attached_tools.map((tool) => (
                          <Chip key={tool} label={tool} size="small" />
                        ))
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          No tools attached
                        </Typography>
                      )}
                    </Box>
                  </Grid>

                  {/* Actions */}
                  <Grid item xs={12}>
                    <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                      <Button
                        variant="outlined"
                        startIcon={testingAgent === agent.name ? <CircularProgress size={20} /> : <CableIcon />}
                        onClick={() => handleTestAgent(agent.name)}
                        disabled={testingAgent === agent.name}
                        sx={{
                          borderColor: '#667eea',
                          color: '#667eea',
                          '&:hover': { borderColor: '#764ba2', background: 'rgba(102, 126, 234, 0.1)' },
                        }}
                      >
                        Test Connection
                      </Button>
                      <Button
                        variant="outlined"
                        startIcon={<EditIcon />}
                        onClick={() => handleOpenDialog(agent)}
                      >
                        Edit
                      </Button>
                      <Button
                        variant="outlined"
                        color="error"
                        startIcon={<DeleteIcon />}
                        onClick={() => handleDeleteAgent(agent.name)}
                        sx={{ ml: 'auto' }}
                      >
                        Delete
                      </Button>
                    </Box>
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          ))}
        </Box>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingAgent ? 'Edit Agent' : 'Add New Agent'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                label="Agent Name"
                fullWidth
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                disabled={!!editingAgent}
                placeholder="my_agent"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="URL"
                fullWidth
                value={formData.url}
                onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                placeholder="http://localhost:8080"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Auth Token (Optional)"
                fullWidth
                type="password"
                value={formData.auth_token}
                onChange={(e) => setFormData({ ...formData, auth_token: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Timeout (seconds)"
                fullWidth
                type="number"
                value={formData.timeout_seconds}
                onChange={(e) => setFormData({ ...formData, timeout_seconds: parseInt(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="System Prompt"
                fullWidth
                multiline
                rows={8}
                value={formData.metadata.system_prompt}
                onChange={(e) => setFormData({
                  ...formData,
                  metadata: { ...formData.metadata, system_prompt: e.target.value },
                })}
                placeholder="Enter system prompt..."
              />
              <Button
                size="small"
                onClick={() => setFormData({
                  ...formData,
                  metadata: { ...formData.metadata, system_prompt: SYSTEM_PROMPT_TEMPLATE },
                })}
                sx={{ mt: 1 }}
              >
                Use Template
              </Button>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>LLM Connection</InputLabel>
                <Select
                  value={formData.metadata.llm_connection}
                  onChange={(e) => setFormData({
                    ...formData,
                    metadata: { ...formData.metadata, llm_connection: e.target.value },
                  })}
                  label="LLM Connection"
                >
                  {llmConnections.map((conn) => (
                    <MenuItem key={conn.id} value={conn.id}>
                      {conn.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>LangGraph Profile</InputLabel>
                <Select
                  value={formData.metadata.langgraph_profile}
                  onChange={(e) => setFormData({
                    ...formData,
                    metadata: { ...formData.metadata, langgraph_profile: e.target.value },
                  })}
                  label="LangGraph Profile"
                >
                  <MenuItem value="default">Default</MenuItem>
                  <MenuItem value="advanced">Advanced</MenuItem>
                  <MenuItem value="custom">Custom</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Attached Tools</InputLabel>
                <Select
                  multiple
                  value={formData.metadata.attached_tools || []}
                  onChange={handleToolsChange}
                  input={<OutlinedInput label="Attached Tools" />}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
                        <Chip key={value} label={value} size="small" />
                      ))}
                    </Box>
                  )}
                >
                  {tools.map((tool) => (
                    <MenuItem key={tool.name} value={tool.name}>
                      {tool.name} ({tool.type})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSaveAgent}
            variant="contained"
            disabled={!formData.name || !formData.url}
            sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
          >
            {editingAgent ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AgentsConfig;
