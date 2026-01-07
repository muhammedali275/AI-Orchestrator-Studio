import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
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
  BugReport as BugReportIcon,
  Timeline as TimelineIcon,
  Build as BuildIcon,
  Speed as SpeedIcon,
  Mic as MicIcon,
  MicOff as MicOffIcon,
  ViewSidebar as ViewSidebarIcon,
} from '@mui/icons-material';
import ConversationList from '../components/chat/ConversationList';
import ChatMessage from '../components/chat/ChatMessage';
import ChatInput from '../components/chat/ChatInput';

interface Message {
  id: string;
  role: string;
  content: string;
  metadata?: {
    tools_used?: Array<{
      name: string;
      input: any;
      output: any;
      duration_ms: number;
    }>;
    execution_steps?: Array<{
      step: string;
      timestamp: string;
      status: string;
    }>;
    model?: string;
    tokens?: number;
  };
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
  connection_id?: string;
  connection_name?: string;
  model_id?: string;
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
  const [debugMode, setDebugMode] = useState(false);
  const [showExecutionPanel, setShowExecutionPanel] = useState(false);
  const [requestTimeout, setRequestTimeout] = useState<number>(120000); // Dynamic timeout from backend
  const [memoryInfo, setMemoryInfo] = useState<any | null>(null);
  const [memoryLoading, setMemoryLoading] = useState(false);
  const [llmStatus, setLlmStatus] = useState<{ source?: string; server_url?: string; error?: string } | null>(null);
  const [showConversations, setShowConversations] = useState<boolean>(() => {
    try {
      const v = localStorage.getItem('chat.showConversations');
      return v === null ? true : v === '1';
    } catch { return true; }
  });

  // Voice: TTS and STT
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoiceUri, setSelectedVoiceUri] = useState<string>('');
  const [listening, setListening] = useState<boolean>(false);
  const recognitionRef = useRef<any>(null);
  const lastTranscriptRef = useRef<string>('');
  const SpeechRecognition: any = (typeof window !== 'undefined' && ((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition)) || null;

  // Load configuration and initial data on mount
  useEffect(() => {
    loadConfig(); // Load timeout and other config from backend
    loadConversations();
    loadModels();
    loadRoutingProfiles();
  }, []);

  // Load browser TTS voices and handle voice=1 auto-start
  useEffect(() => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;
    const synth = window.speechSynthesis;
    const load = () => {
      const v = synth.getVoices();
      if (v && v.length) {
        setVoices(v);
        if (!selectedVoiceUri) setSelectedVoiceUri(v[0].voiceURI);
      }
    };
    load();
    synth.onvoiceschanged = load;

    // Auto-enable voice mode if query has voice=1
    try {
      const sp = new URLSearchParams(window.location.search);
      if (sp.get('voice') === '1') {
        // Start listening after a tick to allow voices to populate
        setTimeout(() => startListening(), 300);
      }
    } catch {}
  }, []);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // API base URL
  const API_BASE_URL = 'http://localhost:8000'; // Backend API server port

  /**
   * Load configuration from backend.
   * This ensures frontend and backend timeouts are synchronized.
   */
  const loadConfig = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/config/timeout`, {
        timeout: 5000, // Short timeout for config endpoint
      });
      if (response.data && response.data.frontend_timeout_ms) {
        setRequestTimeout(response.data.frontend_timeout_ms);
        console.log('[ChatStudio] Loaded config - timeout:', response.data.frontend_timeout_ms, 'ms');
      }
    } catch (err) {
      console.warn('[ChatStudio] Failed to load config, using default 120s timeout:', err);
      setRequestTimeout(120000); // Fallback to 120 seconds
    }
  };

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
      console.log('[ChatStudio] Fetching LLM connections...');
      
      // First, get all LLM connections
      const connectionsResp = await axios.get(`${API_BASE_URL}/api/config/llm-connections`, {
        timeout: 10000,
      });
      
      const connections = connectionsResp.data?.connections || [];
      console.log('[ChatStudio] Found connections:', connections.length);
      
      if (connections.length === 0) {
        setError('No LLM connections configured. Go to LLM Connections to add one.');
        setModels([]);
        return;
      }
      
      // Fetch models from all connections
      const allModels: Model[] = [];
      let defaultModel = '';
      
      for (const conn of connections) {
        try {
          console.log(`[ChatStudio] Fetching models from connection: ${conn.name}`);
          const modelsResp = await axios.get(`${API_BASE_URL}/api/config/llm-connections/${conn.id}/models`, {
            timeout: 15000,
          });
          
          if (modelsResp.data?.success && modelsResp.data?.models) {
            // Add connection name prefix to model IDs for clarity
            modelsResp.data.models.forEach((model: any) => {
              allModels.push({
                id: `${conn.id}:${model.id}`,
                name: `${conn.name} - ${model.name || model.id}`,
                connection_id: conn.id,
                connection_name: conn.name,
                model_id: model.id
              });
            });
            
            // Use first connection's first model as default
            if (!defaultModel && modelsResp.data.models.length > 0) {
              defaultModel = `${conn.id}:${modelsResp.data.models[0].id}`;
            }
          }
        } catch (err) {
          console.warn(`[ChatStudio] Failed to fetch models from ${conn.name}:`, err);
        }
      }
      
      console.log('[ChatStudio] Total models loaded:', allModels.length);
      
      if (allModels.length > 0) {
        setModels(allModels);
        if (defaultModel) {
          setSelectedModel(defaultModel);
        }
        setError(null);
      } else {
        setError('No models available from configured LLM connections. Check if your LLM servers are running.');
        setModels([]);
      }
      
    } catch (err: any) {
      console.error('[ChatStudio] Error loading models:', err);
      setError(`Failed to load models: ${err.message}. Check your LLM connections.`);
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
          id: 'tools_data',
          name: 'Tools + Data',
          description: 'Full orchestration with tools, data sources, and reasoning'
        }
      ];
      setRoutingProfiles(fallbackProfiles);
    }
  };

  // Voice helpers
  const speak = (text: string) => {
    if (!text) return;
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) return;
    const synth = window.speechSynthesis;
    const utter = new SpeechSynthesisUtterance(text);
    const voice = voices.find(v => v.voiceURI === selectedVoiceUri) || voices[0];
    if (voice) utter.voice = voice;
    utter.rate = 1;
    utter.pitch = 1;
    synth.cancel();
    synth.speak(utter);
  };

  const startListening = () => {
    if (!SpeechRecognition) {
      setError('Browser speech recognition not supported.');
      return;
    }
    try {
      const rec = new SpeechRecognition();
      rec.lang = 'en-US';
      rec.continuous = false;
      rec.interimResults = true;
      lastTranscriptRef.current = '';
      rec.onresult = (e: any) => {
        let t = '';
        for (let i = e.resultIndex; i < e.results.length; i++) {
          t += e.results[i][0].transcript;
        }
        lastTranscriptRef.current = t;
      };
      rec.onerror = (e: any) => {
        console.warn('SpeechRecognition error:', e);
      };
      rec.onend = () => {
        setListening(false);
        const finalText = (lastTranscriptRef.current || '').trim();
        if (finalText) {
          handleSendMessage(finalText);
        }
      };
      recognitionRef.current = rec;
      rec.start();
      setListening(true);
    } catch (e) {
      console.error('Failed to start SpeechRecognition', e);
      setError('Failed to start microphone.');
    }
  };

  const stopListening = () => {
    try {
      recognitionRef.current?.stop?.();
    } finally {
      setListening(false);
    }
  };

  const toggleConversations = () => {
    setShowConversations(prev => {
      const next = !prev;
      try { localStorage.setItem('chat.showConversations', next ? '1' : '0'); } catch {}
      return next;
    });
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

  const handleViewMemory = async () => {
    if (!selectedConversation) return;
    setMemoryLoading(true);
    setError(null);
    try {
      const res = await axios.get(`${API_BASE_URL}/api/memory/conversations/${selectedConversation.id}`, {
        timeout: 15000,
      });
      setMemoryInfo(res.data);
    } catch (err) {
      console.error('Error loading memory info:', err);
      setError('Failed to load memory for conversation');
    } finally {
      setMemoryLoading(false);
    }
  };

  const handleClearMemory = async () => {
    if (!selectedConversation) return;
    setMemoryLoading(true);
    setError(null);
    try {
      await axios.delete(`${API_BASE_URL}/api/memory/conversations/${selectedConversation.id}`, {
        timeout: 15000,
      });
      setMemoryInfo(null);
    } catch (err) {
      console.error('Error clearing memory:', err);
      setError('Failed to clear memory for conversation');
    } finally {
      setMemoryLoading(false);
    }
  };
  const handleSendMessage = async (message: string) => {
    if (!message.trim()) return;
    
    if (!selectedModel) {
      setError('Please select a model first. Go to LLM Connections to add one.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Find the selected model object to get connection_id and model_id
      const modelObj = models.find(m => m.id === selectedModel);
      const connectionId = modelObj?.connection_id || '';
      const modelId = modelObj?.model_id || selectedModel;
      
      console.log('[ChatStudio] Sending message with:', { connectionId, modelId, routing: selectedProfile });

      // Prefer SSE streaming for better UX
      const payload = {
        conversation_id: selectedConversation?.id,
        message: message,
        model_id: modelId,
        connection_id: connectionId || undefined,
        routing_profile: selectedProfile,
        use_memory: useMemory,
        use_tools: useTools,
      };

      const streamUrl = `${API_BASE_URL}/api/chat/ui/send/stream`;
      console.log('[ChatStudio] Streaming to:', streamUrl, payload);

      // Create a temporary assistant message to append streamed tokens
      const tempId = `temp_${Date.now()}`;
      setMessages(prev => ([
        ...prev,
        { id: tempId, role: 'user', content: message, created_at: new Date().toISOString() },
        { id: `${tempId}_assistant`, role: 'assistant', content: '', created_at: new Date().toISOString() },
      ]));

      // Use EventSource via fetch-based polyfill for sending POST body
      const controller = new AbortController();
      const timeoutMs = requestTimeout || 120000;
      const timeoutHandle = setTimeout(() => controller.abort(), timeoutMs);

      const response = await fetch(streamUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`Stream failed with status ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder('utf-8');
      let assistantContent = '';

      if (reader) {
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value, { stream: true });
          // Parse SSE frames: lines starting with 'data: '
          const lines = chunk.split(/\r?\n/);
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const token = line.slice(6);
              assistantContent += token;
              setMessages(prev => prev.map(m => (
                m.id === `${tempId}_assistant` ? { ...m, content: assistantContent } : m
              )));
            } else if (line.startsWith('event: done')) {
              // Completion event
              clearTimeout(timeoutHandle);
            }
          }
        }
      }

      // After streaming completes, reload messages from backend to get final metadata
      if (selectedConversation?.id) {
        await loadConversationMessages(selectedConversation.id);
      } else {
        await loadConversations();
      }

      // Speak the assistant response
      speak(assistantContent);
    } catch (err: any) {
      console.error('Error streaming message:', err);
      const errorMsg = err.name === 'AbortError'
        ? `Streaming timed out (${Math.round((requestTimeout || 120000) / 1000)}s).`
        : 'Failed to stream message';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 48px)', gap: 2 }}>
      {/* Left Panel - Conversations */}
      {showConversations && (
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
      )}

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
          <FormControl size="small" sx={{ minWidth: 200 }} error={models.length === 0 && error !== null}>
            <InputLabel>Model</InputLabel>
            <Select
              value={selectedModel}
              label="Model"
              onChange={(e) => setSelectedModel(e.target.value)}
              disabled={models.length === 0}
            >
              {models.length === 0 ? (
                <MenuItem value="" disabled>
                  {error ? 'No models - Configure LLM' : 'Loading...'}
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

          <IconButton size="small" onClick={loadModels} title="Reload models">
            <RefreshIcon />
          </IconButton>

          <IconButton size="small" title="Settings">
            <SettingsIcon />
          </IconButton>

          <Tooltip title={showConversations ? 'Hide conversations' : 'Show conversations'}>
            <IconButton size="small" onClick={toggleConversations}>
              <ViewSidebarIcon />
            </IconButton>
          </Tooltip>

          <Box sx={{ flex: 1 }} />

          {/* Voice Controls */}
          <FormControl size="small" sx={{ minWidth: 220 }} disabled={voices.length === 0}>
            <InputLabel>Voice</InputLabel>
            <Select
              value={selectedVoiceUri}
              label="Voice"
              onChange={(e) => setSelectedVoiceUri(String(e.target.value))}
            >
              {voices.length === 0 ? (
                <MenuItem value="" disabled>
                  No voices available
                </MenuItem>
              ) : (
                voices.map((v) => (
                  <MenuItem key={v.voiceURI} value={v.voiceURI}>
                    {v.name} {v.lang ? `(${v.lang})` : ''}
                  </MenuItem>
                ))
              )}
            </Select>
          </FormControl>

          {/* Microphone disabled - text chat only
          <Tooltip title={listening ? 'Stop voice input' : 'Start voice input'}>
            <span>
              <IconButton size="small" onClick={() => (listening ? stopListening() : startListening())} color={listening ? 'error' : 'primary'}>
                {listening ? <MicOffIcon /> : <MicIcon />}
              </IconButton>
            </span>
          </Tooltip>
          */}

          {/* LLM Connectivity Badge */}
          {llmStatus && (
            <Chip
              label={llmStatus.error
                ? `LLM: Disconnected`
                : llmStatus.source === 'ollama-local'
                ? `LLM: Local`
                : llmStatus.source
                ? `LLM: ${llmStatus.source}`
                : 'LLM: Unknown'}
              color={llmStatus.error ? 'warning' : 'success'}
              variant="outlined"
              sx={{ mr: 1 }}
            />
          )}

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

          <Tooltip title="Debug mode">
            <IconButton
              size="small"
              onClick={() => setDebugMode(!debugMode)}
              color={debugMode ? 'primary' : 'default'}
            >
              <BugReportIcon />
            </IconButton>
          </Tooltip>

          <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />

          <Button
            size="small"
            variant="outlined"
            onClick={handleViewMemory}
            disabled={!selectedConversation || memoryLoading}
          >
            {memoryLoading ? 'Loading Memory…' : 'View Memory'}
          </Button>
          <Button
            size="small"
            variant="outlined"
            color="error"
            onClick={handleClearMemory}
            disabled={!selectedConversation || memoryLoading}
          >
            Clear Memory
          </Button>
        </Box>

        {/* Error Banner */}
        {error && (
          <Alert severity="warning" sx={{ m: 2 }}>
            {error}
          </Alert>
        )}

        {/* Messages Area */}
        <Box
          sx={{
            flex: 1,
            overflowY: 'auto',
            p: 2,
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
          }}
        >
          {memoryInfo && (
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Conversation Memory
              </Typography>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Messages in memory: {memoryInfo.message_count} · Tokens: {memoryInfo.total_tokens} · Size: {(memoryInfo.size_bytes / (1024)).toFixed(1)} KB
              </Typography>
              <Divider sx={{ my: 1 }} />
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, maxHeight: 240, overflowY: 'auto' }}>
                {(memoryInfo.memory_entries || []).map((entry: any, idx: number) => (
                  <Box key={idx} sx={{ p: 1, borderRadius: 1, bgcolor: isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' }}>
                    <Typography variant="caption" color="textSecondary">
                      {entry.role} {entry.tokens ? `· ${entry.tokens} tokens` : ''}
                    </Typography>
                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>{entry.content}</Typography>
                  </Box>
                ))}
              </Box>
            </Paper>
          )}
          {messages.length === 0 ? (
            <Box
              sx={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Typography color="textSecondary" align="center">
                Welcome to Chat Studio<br />
                Start a new conversation or select an existing one
              </Typography>
            </Box>
          ) : (
            messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))
          )}
          <div ref={messagesEndRef} />
        </Box>

        {/* Input Area */}
        <Box sx={{ p: 2, borderTop: `1px solid ${isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}` }}>
          <ChatInput
            onSend={handleSendMessage}
            disabled={loading || !selectedModel}
            placeholder={loading ? 'Waiting for response...' : 'Type your message...'}
          />
        </Box>
      </Paper>
    </Box>
  );
};

export default ChatStudio;
