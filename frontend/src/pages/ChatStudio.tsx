import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  CircularProgress,
  Alert,
  Divider,
  Tooltip,
  useTheme,
} from '@mui/material';
import {
  Send as SendIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import ConversationList from '../components/chat/ConversationList';
import ChatMessage from '../components/chat/ChatMessage';
import ChatInput from '../components/chat/ChatInput';

interface Message {
  id: string;
  role: string;
  content: string;
  metadata?: any;
  created_at: string;
}

interface Conversation {
  id: string;
  title: string;
  model_id?: string;
  routing_profile: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

interface Model {
  id: string;
  name?: string;
}

interface RoutingProfile {
  id: string;
  name: string;
  description: string;
}

const ChatStudio: React.FC = () => {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // State
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [routingProfiles, setRoutingProfiles] = useState<RoutingProfile[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [selectedProfile, setSelectedProfile] = useState<string>('direct_llm');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [useMemory, setUseMemory] = useState(true);
  const [useTools, setUseTools] = useState(false);

  // Load initial data
  useEffect(() => {
    loadConversations();
    loadModels();
    loadRoutingProfiles();
  }, []);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // API base URL
  const API_BASE_URL = 'http://localhost:8001'; // Use the Chat Studio API server port

  const loadConversations = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/ui/conversations`);
      const data = await response.json();
      setConversations(data.conversations || []);
    } catch (err) {
      console.error('Error loading conversations:', err);
      // Use fallback data if API fails
      setConversations([]);
    }
  };

  const loadModels = async () => {
    try {
      console.log('[ChatStudio] Fetching models from:', `${API_BASE_URL}/api/chat/ui/models`);
      const response = await fetch(`${API_BASE_URL}/api/chat/ui/models`);
      const data = await response.json();
      console.log('[ChatStudio] Models response:', data);
      
      if (data.success && data.models && data.models.length > 0) {
        setModels(data.models);
        if (data.default_model) {
          setSelectedModel(data.default_model);
        } else if (data.models.length > 0) {
          setSelectedModel(data.models[0].id);
        }
        setError(null);
      } else {
        // No models available
        setError('No LLM models configured. Please add an LLM connection first.');
        setModels([]);
      }
    } catch (err) {
      console.error('Error loading models:', err);
      setError('Failed to load models. Please check if the backend is running and LLM is configured.');
      setModels([]);
    }
  };

  const loadRoutingProfiles = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/ui/profiles`);
      const data = await response.json();
      setRoutingProfiles(data.profiles || []);
    } catch (err) {
      console.error('Error loading routing profiles:', err);
      // Use fallback profiles if API fails
      const fallbackProfiles = [
        {
          id: 'direct_llm',
          name: 'Direct LLM',
          description: 'Direct connection to LLM server without additional processing'
        },
        {
          id: 'zain_agent',
          name: 'Zain Agent',
          description: 'Route through Zain orchestrator agent with data access'
        },
        {
          id: 'tools_data',
          name: 'Tools + Data',
          description: 'Full orchestration with tools, data sources, and reasoning'
        }
      ];
      setRoutingProfiles(fallbackProfiles);
    }
  };

  const loadConversationMessages = async (conversationId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/ui/conversations/${conversationId}`);
      const data = await response.json();
      setMessages(data.messages || []);
      setSelectedConversation(data.conversation);
    } catch (err) {
      console.error('Error loading messages:', err);
      setError('Failed to load conversation');
    }
  };

  const handleConversationSelect = (conversation: Conversation) => {
    setSelectedConversation(conversation);
    setSelectedModel(conversation.model_id || selectedModel);
    setSelectedProfile(conversation.routing_profile);
    loadConversationMessages(conversation.id);
  };

  const handleNewConversation = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/ui/conversations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: `New Chat ${new Date().toLocaleTimeString()}`,
          model_id: selectedModel,
          routing_profile: selectedProfile,
        }),
      });
      const data = await response.json();
      if (data.success) {
        await loadConversations();
        setSelectedConversation(data.conversation);
        setMessages([]);
      }
    } catch (err) {
      console.error('Error creating conversation:', err);
      setError('Failed to create conversation');
    }
  };

  const handleDeleteConversation = async (conversationId: string) => {
    try {
      await fetch(`${API_BASE_URL}/api/chat/ui/conversations/${conversationId}`, {
        method: 'DELETE',
      });
      await loadConversations();
      if (selectedConversation?.id === conversationId) {
        setSelectedConversation(null);
        setMessages([]);
      }
    } catch (err) {
      console.error('Error deleting conversation:', err);
      setError('Failed to delete conversation');
    }
  };

  const handleSendMessage = async (message: string) => {
    if (!message.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat/ui/send`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: selectedConversation?.id,
          message: message,
          model_id: selectedModel,
          routing_profile: selectedProfile,
          use_memory: useMemory,
          use_tools: useTools,
        }),
      });

      const data = await response.json();

      if (data.conversation_id) {
        // Reload conversation if it was just created
        if (!selectedConversation) {
          await loadConversations();
          const conv = conversations.find(c => c.id === data.conversation_id);
          if (conv) setSelectedConversation(conv);
        }
        // Reload messages
        await loadConversationMessages(data.conversation_id);
      }
    } catch (err) {
      console.error('Error sending message:', err);
      setError('Failed to send message');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 48px)', gap: 2 }}>
      {/* Left Panel - Conversations */}
      <Paper
        sx={{
          width: 300,
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        <Box sx={{ p: 2, borderBottom: `1px solid ${isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}` }}>
          <Button
            fullWidth
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleNewConversation}
          >
            New Chat
          </Button>
        </Box>
        <ConversationList
          conversations={conversations}
          selectedConversation={selectedConversation}
          onSelect={handleConversationSelect}
          onDelete={handleDeleteConversation}
          onRefresh={loadConversations}
        />
      </Paper>

      {/* Main Panel - Chat */}
      <Paper sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Top Bar */}
        <Box
          sx={{
            p: 2,
            borderBottom: `1px solid ${isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}`,
            display: 'flex',
            gap: 2,
            alignItems: 'center',
          }}
        >
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Model</InputLabel>
            <Select
              value={selectedModel}
              label="Model"
              onChange={(e) => setSelectedModel(e.target.value)}
              disabled={models.length === 0}
            >
              {models.length === 0 ? (
                <MenuItem value="" disabled>
                  No models available
                </MenuItem>
              ) : (
                models.map((model) => (
                  <MenuItem key={model.id} value={model.id}>
                    {model.name || model.id}
                  </MenuItem>
                ))
              )}
            </Select>
          </FormControl>

          <Tooltip title="Refresh Models">
            <IconButton
              size="small"
              onClick={loadModels}
              sx={{
                background: 'rgba(102, 126, 234, 0.1)',
                '&:hover': { background: 'rgba(102, 126, 234, 0.2)' },
              }}
            >
              <RefreshIcon fontSize="small" />
            </IconButton>
          </Tooltip>

          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Routing Profile</InputLabel>
            <Select
              value={selectedProfile}
              label="Routing Profile"
              onChange={(e) => setSelectedProfile(e.target.value)}
            >
              {routingProfiles.map((profile) => (
                <MenuItem key={profile.id} value={profile.id}>
                  {profile.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Box sx={{ flex: 1 }} />

          <Tooltip title={useMemory ? 'Memory: ON' : 'Memory: OFF'}>
            <Chip
              label="Memory"
              color={useMemory ? 'primary' : 'default'}
              onClick={() => setUseMemory(!useMemory)}
              size="small"
            />
          </Tooltip>

          <Tooltip title={useTools ? 'Tools: ON' : 'Tools: OFF'}>
            <Chip
              label="Tools"
              color={useTools ? 'primary' : 'default'}
              onClick={() => setUseTools(!useTools)}
              size="small"
            />
          </Tooltip>
        </Box>

        {/* Messages Area */}
        <Box
          sx={{
            flex: 1,
            overflow: 'auto',
            p: 3,
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
          }}
        >
          {error && (
            <Alert severity="error" onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {messages.length === 0 && !selectedConversation && (
            <Box
              sx={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexDirection: 'column',
                gap: 2,
              }}
            >
              <Typography variant="h5" color="text.secondary">
                Welcome to Chat Studio
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Start a new conversation or select an existing one
              </Typography>
            </Box>
          )}

          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}

          {loading && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <CircularProgress size={20} />
              <Typography variant="body2" color="text.secondary">
                Thinking...
              </Typography>
            </Box>
          )}

          <div ref={messagesEndRef} />
        </Box>

        {/* Input Area */}
        <ChatInput onSend={handleSendMessage} disabled={loading} />
      </Paper>
    </Box>
  );
};

export default ChatStudio;
