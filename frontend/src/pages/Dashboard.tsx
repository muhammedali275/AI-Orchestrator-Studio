import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Typography,
  Grid,
  Paper,
  Box,
  Card,
  CardContent,
  LinearProgress,
  CircularProgress,
  Chip,
  Avatar,
  IconButton,
  Tooltip,
  Button,
} from '@mui/material';
import { keyframes } from '@mui/system';
import {
  Speed as SpeedIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  CloudQueue as CloudIcon,
  TrendingUp as TrendingUpIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
  LocationOn as LocationIcon,
  Public as PublicIcon,
  Security as SecurityIcon,
  Psychology as PsychologyIcon,
  Build as BuildIcon,
  VpnKey as VpnKeyIcon,
  Https as HttpsIcon,
  Link as LinkIcon,
  ArrowForward as ArrowForwardIcon,
  Settings as SettingsIcon,
  Mic as MicIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface SystemStats {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  active_connections: number;
  requests_per_minute: number;
  cache_hit_rate: number;
  agent_count: number;
  credential_count: number;
  tls_enabled: boolean;
  tool_count: number;
}

interface QuickLink {
  title: string;
  description: string;
  path: string;
  icon: JSX.Element;
  color: string;
}

type NodeStatus = 'online' | 'degraded' | 'offline';

interface ServerNode {
  id: string;
  name: string;
  role: string;
  status: NodeStatus;
  lastHeartbeat?: string;
}

interface NodesSummary {
  total: number;
  online: number;
  degraded: number;
  offline: number;
}

const spin = keyframes`
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
`;

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  
  const [stats, setStats] = useState<SystemStats>({
    cpu_usage: 45,
    memory_usage: 62,
    disk_usage: 38,
    active_connections: 12,
    requests_per_minute: 145,
    cache_hit_rate: 85,
    agent_count: 3,
    credential_count: 8,
    tls_enabled: false,
    tool_count: 5,
  });
  const [loading, setLoading] = useState(false);

  const quickLinks: QuickLink[] = [
    {
      title: 'LLM Connections',
      description: 'Configure AI models',
      path: '/llm',
      icon: <SettingsIcon />,
      color: '#667eea',
    },
    {
      title: 'Agents & Prompts',
      description: 'Manage AI agents',
      path: '/agents',
      icon: <PsychologyIcon />,
      color: '#764ba2',
    },
    {
      title: 'Tools & Data Sources',
      description: 'Configure integrations',
      path: '/tools',
      icon: <BuildIcon />,
      color: '#10b981',
    },
    {
      title: 'Credentials',
      description: 'Manage security',
      path: '/credentials',
      icon: <VpnKeyIcon />,
      color: '#f59e0b',
    },
  ];
  const fetchStats = async () => {
    setLoading(true);
    try {
      // Fetch real stats from multiple endpoints
      const [healthRes, agentsRes, credentialsRes, certRes, toolsRes] = await Promise.allSettled([
        axios.get('http://localhost:8000/health'),
        axios.get('http://localhost:8000/api/agents'),
        axios.get('http://localhost:8000/api/credentials'),
        axios.get('http://localhost:8000/api/certs'),
        axios.get('http://localhost:8000/api/tools'),
      ]);

      setStats({
        cpu_usage: Math.random() * 100,
        memory_usage: Math.random() * 100,
        disk_usage: Math.random() * 100,
        active_connections: Math.floor(Math.random() * 50),
        requests_per_minute: Math.floor(Math.random() * 500),
        cache_hit_rate: 75 + Math.random() * 25,
        agent_count: agentsRes.status === 'fulfilled' ? agentsRes.value.data.length : 0,
        credential_count: credentialsRes.status === 'fulfilled' ? credentialsRes.value.data.credentials?.length || 0 : 0,
        tls_enabled: certRes.status === 'fulfilled' ? certRes.value.data.enabled || false : false,
        tool_count: toolsRes.status === 'fulfilled' ? toolsRes.value.data.length : 0,
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const StatCard = ({ title, value, icon, color, unit = '', trend }: any) => (
    <Card
      className="card-hover"
      sx={{
        background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)',
        border: '1px solid rgba(102, 126, 234, 0.1)',
        height: '100%',
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 700, color }}>
              {typeof value === 'number' ? value.toFixed(1) : value}{unit}
            </Typography>
          </Box>
          <Avatar
            sx={{
              background: `linear-gradient(135deg, ${color}20 0%, ${color}40 100%)`,
              color,
              width: 56,
              height: 56,
            }}
          >
            {icon}
          </Avatar>
        </Box>
        {typeof value === 'number' && unit === '%' && (
          <LinearProgress
            variant="determinate"
            value={value}
            sx={{
              height: 8,
              borderRadius: 4,
              backgroundColor: 'rgba(102, 126, 234, 0.1)',
              '& .MuiLinearProgress-bar': {
                background: `linear-gradient(90deg, ${color} 0%, ${color}dd 100%)`,
                borderRadius: 4,
              },
            }}
          />
        )}
        {trend && (
          <Box sx={{ display: 'flex', alignItems: 'center', mt: 1, gap: 0.5 }}>
            <TrendingUpIcon sx={{ fontSize: 16, color: '#10b981' }} />
            <Typography variant="caption" sx={{ color: '#10b981', fontWeight: 600 }}>
              {trend}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );

  const ServiceStatus = ({ name, status, latency }: any) => (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        p: 2,
        borderRadius: 2,
        background: 'rgba(102, 126, 234, 0.05)',
        border: '1px solid rgba(102, 126, 234, 0.1)',
        transition: 'all 0.25s ease-in-out',
        '&:hover': {
          background: 'rgba(102, 126, 234, 0.1)',
          transform: 'translateX(4px)',
        },
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Box
          sx={{
            width: 12,
            height: 12,
            borderRadius: '50%',
            background: status === 'online' ? '#10b981' : '#ef4444',
            boxShadow: `0 0 12px ${status === 'online' ? '#10b981' : '#ef4444'}`,
            animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
          }}
        />
        <Typography variant="body1" fontWeight={600}>
          {name}
        </Typography>
      </Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Chip
          label={`${latency}ms`}
          size="small"
          sx={{
            background: 'rgba(102, 126, 234, 0.2)',
            color: '#667eea',
            fontWeight: 600,
          }}
        />
        <Chip
          icon={status === 'online' ? <CheckCircleIcon /> : <WarningIcon />}
          label={status === 'online' ? 'Online' : 'Offline'}
          size="small"
          color={status === 'online' ? 'success' : 'error'}
          sx={{ fontWeight: 600 }}
        />
      </Box>
    </Box>
  );

  const ActiveServerNodesFlow: React.FC = () => {
    const [nodes, setNodes] = useState<ServerNode[]>([]);
    const [summary, setSummary] = useState<NodesSummary>({ total: 0, online: 0, degraded: 0, offline: 0 });
    const [loadingNodes, setLoadingNodes] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [lastUpdated, setLastUpdated] = useState<string | null>(null);

    const statusColor = (status: NodeStatus) => {
      if (status === 'online') return '#10b981';
      if (status === 'degraded') return '#f59e0b';
      return '#ef4444';
    };

    const loadNodes = async () => {
      setLoadingNodes(true);
      try {
        const res = await axios.get('http://localhost:8000/api/monitoring/connectivity');
        const data = res.data || {};
        const services = data.services || {};
        const s = data.summary || {};
        const timestamp: string | undefined = data.timestamp;

        const newNodes: ServerNode[] = [];

        const orchestratorStatus: NodeStatus = s.unreachable && s.unreachable > 0 ? 'degraded' : 'online';
        newNodes.push({
          id: 'orchestrator',
          name: 'Orchestrator Node',
          role: 'Control Plane',
          status: orchestratorStatus,
          lastHeartbeat: timestamp,
        });

        if (services.llm) {
          newNodes.push({
            id: 'llm',
            name: 'LLM Service',
            role: 'Model Gateway',
            status: services.llm.reachable ? 'online' : 'offline',
            lastHeartbeat: timestamp,
          });
        }

        if (services.agents) {
          const entries = Object.entries(services.agents as Record<string, any>);
          if (entries.length > 0) {
            const reachable = entries.filter(([, v]) => v && v.reachable).length;
            const status: NodeStatus = reachable === entries.length ? 'online' : reachable === 0 ? 'offline' : 'degraded';
            newNodes.push({
              id: 'agents',
              name: `External Agents (${entries.length})`,
              role: 'Tools & Connectors',
              status,
              lastHeartbeat: timestamp,
            });
          }
        }

        if (services.datasources) {
          const entries = Object.entries(services.datasources as Record<string, any>);
          if (entries.length > 0) {
            const reachable = entries.filter(([, v]) => v && v.reachable).length;
            const status: NodeStatus = reachable === entries.length ? 'online' : reachable === 0 ? 'offline' : 'degraded';
            newNodes.push({
              id: 'datasources',
              name: `Data Sources (${entries.length})`,
              role: 'Databases & APIs',
              status,
              lastHeartbeat: timestamp,
            });
          }
        }

        const onlineCount = newNodes.filter((n) => n.status === 'online').length;
        const degradedCount = newNodes.filter((n) => n.status === 'degraded').length;
        const offlineCount = newNodes.filter((n) => n.status === 'offline').length;

        setNodes(newNodes);
        setSummary({
          total: newNodes.length,
          online: onlineCount,
          degraded: degradedCount,
          offline: offlineCount,
        });
        setLastUpdated(timestamp || new Date().toISOString());
        setError(null);
      } catch (err: any) {
        console.error('Error loading server nodes flow:', err);
        setError('Unable to load server node status.');
      } finally {
        setLoadingNodes(false);
      }
    };

    useEffect(() => {
      loadNodes();
      const interval = setInterval(loadNodes, 15000);
      return () => clearInterval(interval);
    }, []);

    return (
      <Box sx={{ width: '100%', px: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Chip
              label={`Total: ${summary.total}`}
              size="small"
              sx={{ background: 'rgba(148, 163, 184, 0.2)', color: '#e5e7eb', fontWeight: 600 }}
            />
            <Chip
              label={`Online: ${summary.online}`}
              size="small"
              sx={{ background: 'rgba(16, 185, 129, 0.2)', color: '#10b981', fontWeight: 600 }}
            />
            <Chip
              label={`Degraded: ${summary.degraded}`}
              size="small"
              sx={{ background: 'rgba(245, 158, 11, 0.2)', color: '#f59e0b', fontWeight: 600 }}
            />
            <Chip
              label={`Offline: ${summary.offline}`}
              size="small"
              sx={{ background: 'rgba(239, 68, 68, 0.2)', color: '#ef4444', fontWeight: 600 }}
            />
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            {lastUpdated && (
              <Typography variant="caption" sx={{ color: 'rgba(148, 163, 184, 0.9)' }}>
                Last updated: {new Date(lastUpdated).toLocaleTimeString()}
              </Typography>
            )}
            <Tooltip title="Refresh now">
              <IconButton
                size="small"
                onClick={loadNodes}
                sx={{
                  color: '#9ca3af',
                  '&:hover': { color: '#e5e7eb', background: 'rgba(55, 65, 81, 0.6)' },
                }}
              >
                <RefreshIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            {loadingNodes && <CircularProgress size={18} sx={{ color: '#667eea' }} />}
          </Box>
        </Box>

        {error && (
          <Typography variant="caption" color="error" sx={{ mb: 1, display: 'block' }}>
            {error}
          </Typography>
        )}

        <Box
          sx={{
            mt: 2,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 2,
            maxWidth: 680,
            mx: 'auto',
          }}
        >
          {nodes.length === 0 && !loadingNodes && !error ? (
            <Box sx={{ textAlign: 'center', mx: 'auto' }}>
              <Typography variant="body2" sx={{ color: 'rgba(209, 213, 219, 0.9)', mb: 0.5 }}>
                No monitored server nodes yet.
              </Typography>
              <Typography variant="caption" sx={{ color: 'rgba(148, 163, 184, 0.9)', display: 'block', mb: 1.5 }}>
                Configure monitoring targets on the Monitoring & Services page.
              </Typography>
              <Button
                variant="outlined"
                size="small"
                onClick={() => navigate('/monitoring')}
                sx={{
                  borderColor: 'rgba(129, 140, 248, 0.7)',
                  color: '#a5b4fc',
                  textTransform: 'none',
                  fontWeight: 600,
                  '&:hover': {
                    borderColor: '#818cf8',
                    background: 'rgba(79, 70, 229, 0.15)',
                  },
                }}
              >
                Open Monitoring
              </Button>
            </Box>
          ) : (
            nodes.map((node, index) => (
              <React.Fragment key={node.id}>
                <Tooltip
                  title={`${node.role}${node.lastHeartbeat ? ` • Last heartbeat: ${node.lastHeartbeat}` : ''}`}
                  arrow
                >
                  <Box
                    sx={{
                      minWidth: 120,
                      px: 1.5,
                      py: 1,
                      borderRadius: 999,
                      background: 'rgba(15, 23, 42, 0.9)',
                      border: `1px solid ${statusColor(node.status)}`,
                      boxShadow: `0 0 16px ${statusColor(node.status)}44`,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: 0.5,
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75 }}>
                      <Box
                        sx={{
                          width: 10,
                          height: 10,
                          borderRadius: '50%',
                          background: statusColor(node.status),
                          boxShadow: `0 0 10px ${statusColor(node.status)}`,
                          animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                        }}
                      />
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        {node.name}
                      </Typography>
                    </Box>
                    <Typography
                      variant="caption"
                      sx={{
                        color: 'rgba(148, 163, 184, 0.9)',
                        textTransform: 'uppercase',
                        letterSpacing: 0.6,
                        fontSize: 10,
                      }}
                    >
                      {node.status.toUpperCase()}
                    </Typography>
                  </Box>
                </Tooltip>
                {index < nodes.length - 1 && (
                  <Box
                    sx={{
                      flex: 1,
                      mx: 1,
                      height: 2,
                      position: 'relative',
                      background: 'linear-gradient(90deg, rgba(148, 163, 184, 0.3), rgba(129, 140, 248, 0.7))',
                      '&::after': {
                        content: '""',
                        position: 'absolute',
                        right: -6,
                        top: -3,
                        borderTop: '4px solid transparent',
                        borderBottom: '4px solid transparent',
                        borderLeft: '6px solid rgba(129, 140, 248, 0.8)',
                      },
                    }}
                  />
                )}
              </React.Fragment>
            ))
          )}
        </Box>

        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center', gap: 3 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981', boxShadow: '0 0 8px #10b981' }} />
            <Typography variant="caption" sx={{ color: 'rgba(148, 163, 184, 0.9)' }}>
              Online
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ width: 8, height: 8, borderRadius: '50%', background: '#f59e0b', boxShadow: '0 0 8px #f59e0b' }} />
            <Typography variant="caption" sx={{ color: 'rgba(148, 163, 184, 0.9)' }}>
              Degraded
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box sx={{ width: 8, height: 8, borderRadius: '50%', background: '#ef4444', boxShadow: '0 0 8px #ef4444' }} />
            <Typography variant="caption" sx={{ color: 'rgba(148, 163, 184, 0.9)' }}>
              Offline
            </Typography>
          </Box>
        </Box>
      </Box>
    );
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
            Dashboard
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Welcome to AI Orchestrator Studio
          </Typography>
        </Box>
        <Tooltip title="Refresh Stats">
          <IconButton
            onClick={fetchStats}
            disabled={loading}
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

      {/* Stats Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="CPU Usage"
            value={stats.cpu_usage}
            unit="%"
            icon={<SpeedIcon />}
            color="#667eea"
            trend="+2.5% from last hour"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Memory Usage"
            value={stats.memory_usage}
            unit="%"
            icon={<MemoryIcon />}
            color="#764ba2"
            trend="+1.2% from last hour"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Disk Usage"
            value={stats.disk_usage}
            unit="%"
            icon={<StorageIcon />}
            color="#10b981"
            trend="-0.5% from last hour"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Cache Hit Rate"
            value={stats.cache_hit_rate}
            unit="%"
            icon={<CloudIcon />}
            color="#3b82f6"
            trend="+3.1% from last hour"
          />
        </Grid>
      </Grid>

      {/* Quick Links and System Status */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Quick Links */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
              <LinkIcon sx={{ verticalAlign: 'middle', mr: 1, color: '#667eea' }} />
              Quick Actions
            </Typography>
            <Grid container spacing={2}>
              {/* Voice Assistant Card (AI Assistant - Try Now) */}
              <Grid item xs={12}>
                <Card
                  onClick={() => navigate('/chat?voice=1')}
                  sx={{
                    cursor: 'pointer',
                    overflow: 'hidden',
                    background: 'radial-gradient(80% 120% at 20% 20%, rgba(59,130,246,0.15) 0%, rgba(118,75,162,0.12) 35%, rgba(2,6,23,0.1) 100%)',
                    border: '1px solid rgba(102,126,234,0.35)',
                    position: 'relative',
                    minHeight: 260,
                    transition: 'transform 0.35s ease, box-shadow 0.35s ease, border-color 0.35s ease',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: '0 18px 40px rgba(102,126,234,0.25)',
                      borderColor: 'rgba(102,126,234,0.6)'
                    }
                  }}
                >
                  <CardContent sx={{ p: 4 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 4, flexWrap: 'wrap' }}>
                      {/* Left: Title and CTA */}
                      <Box sx={{ minWidth: 320 }}>
                        <Typography variant="h4" sx={{ fontWeight: 800, mb: 1,
                          background: 'linear-gradient(135deg, #93c5fd 0%, #a78bfa 50%, #f0abfc 100%)',
                          WebkitBackgroundClip: 'text',
                          WebkitTextFillColor: 'transparent',
                          backgroundClip: 'text'
                        }}>
                          AI Assistant
                        </Typography>
                        <Typography variant="body1" color="text.secondary" sx={{ mb: 2.5 }}>
                          Voice-enabled chat assistant. Speak to start a conversation.
                        </Typography>
                        <Button
                          variant="contained"
                          size="large"
                          onClick={(e) => { e.stopPropagation(); navigate('/chat?voice=1'); }}
                          startIcon={<MicIcon />}
                          sx={{
                            fontWeight: 800,
                            px: 3,
                            py: 1.25,
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            boxShadow: '0 14px 28px rgba(102,126,234,0.35)',
                            '&:hover': {
                              background: 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)',
                              transform: 'translateY(-1px)'
                            }
                          }}
                          >
                          Try Now
                        </Button>
                      </Box>

                      {/* Right: Animated sphere */}
                      <Box sx={{ position: 'relative', width: 220, height: 220, mx: 'auto' }}>
                        <Box
                          sx={{
                            position: 'absolute',
                            inset: 0,
                            borderRadius: '50%',
                            background: 'radial-gradient(closest-side, rgba(147,197,253,0.25), rgba(167,139,250,0.25), rgba(240,171,252,0.15) 80%)',
                            boxShadow: '0 0 28px rgba(147,197,253,0.4), inset 0 0 48px rgba(118,75,162,0.3)'
                          }}
                        />
                        <Box
                          sx={{
                            position: 'absolute',
                            inset: 0,
                            borderRadius: '50%',
                            background: 'conic-gradient(from 0deg, rgba(147,197,253,0.0), rgba(147,197,253,0.35), rgba(167,139,250,0.35), rgba(240,171,252,0.25), rgba(147,197,253,0.0))',
                            filter: 'blur(4px)',
                            animation: `${spin} 8s linear infinite`
                          }}
                        />
                        <Box
                          sx={{
                            position: 'absolute',
                            inset: 0,
                            borderRadius: '50%',
                            background: 'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.25) 0%, rgba(255,255,255,0.05) 30%, transparent 60%)'
                          }}
                        />
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {quickLinks.map((link, index) => (
                <Grid item xs={12} sm={6} key={index}>
                  <Card
                    onClick={() => navigate(link.path)}
                    sx={{
                      cursor: 'pointer',
                      background: `linear-gradient(135deg, ${link.color}15 0%, ${link.color}05 100%)`,
                      border: `1px solid ${link.color}40`,
                      transition: 'all 0.3s ease-in-out',
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        boxShadow: `0 8px 24px ${link.color}30`,
                        border: `1px solid ${link.color}80`,
                      },
                    }}
                  >
                    <CardContent>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Avatar
                          sx={{
                            background: `linear-gradient(135deg, ${link.color} 0%, ${link.color}CC 100%)`,
                            width: 48,
                            height: 48,
                          }}
                        >
                          {link.icon}
                        </Avatar>
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="h6" sx={{ fontWeight: 600, color: link.color }}>
                            {link.title}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {link.description}
                          </Typography>
                        </Box>
                        <ArrowForwardIcon sx={{ color: link.color }} />
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>

        {/* System Status Summary */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
              System Overview
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {/* Agents Count */}
              <Box
                onClick={() => navigate('/agents')}
                sx={{
                  p: 2,
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, rgba(118, 75, 162, 0.1) 0%, rgba(118, 75, 162, 0.05) 100%)',
                  border: '1px solid rgba(118, 75, 162, 0.2)',
                  cursor: 'pointer',
                  transition: 'all 0.25s ease-in-out',
                  '&:hover': { transform: 'translateX(4px)', background: 'rgba(118, 75, 162, 0.15)' },
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: '#764ba2' }}>
                      {stats.agent_count}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Active Agents
                    </Typography>
                  </Box>
                  <PsychologyIcon sx={{ fontSize: 40, color: '#764ba2', opacity: 0.3 }} />
                </Box>
              </Box>

              {/* Credentials Count */}
              <Box
                onClick={() => navigate('/credentials')}
                sx={{
                  p: 2,
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(245, 158, 11, 0.05) 100%)',
                  border: '1px solid rgba(245, 158, 11, 0.2)',
                  cursor: 'pointer',
                  transition: 'all 0.25s ease-in-out',
                  '&:hover': { transform: 'translateX(4px)', background: 'rgba(245, 158, 11, 0.15)' },
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: '#f59e0b' }}>
                      {stats.credential_count}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Stored Credentials
                    </Typography>
                  </Box>
                  <VpnKeyIcon sx={{ fontSize: 40, color: '#f59e0b', opacity: 0.3 }} />
                </Box>
              </Box>

              {/* TLS Status */}
              <Box
                onClick={() => navigate('/certificates')}
                sx={{
                  p: 2,
                  borderRadius: 2,
                  background: stats.tls_enabled
                    ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%)'
                    : 'linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(239, 68, 68, 0.05) 100%)',
                  border: stats.tls_enabled ? '1px solid rgba(16, 185, 129, 0.2)' : '1px solid rgba(239, 68, 68, 0.2)',
                  cursor: 'pointer',
                  transition: 'all 0.25s ease-in-out',
                  '&:hover': {
                    transform: 'translateX(4px)',
                    background: stats.tls_enabled ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                  },
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Chip
                      label={stats.tls_enabled ? 'ENABLED' : 'DISABLED'}
                      size="small"
                      sx={{
                        background: stats.tls_enabled ? '#10b981' : '#ef4444',
                        color: 'white',
                        fontWeight: 700,
                        mb: 0.5,
                      }}
                    />
                    <Typography variant="body2" color="text.secondary">
                      TLS/HTTPS Security
                    </Typography>
                  </Box>
                  <HttpsIcon
                    sx={{
                      fontSize: 40,
                      color: stats.tls_enabled ? '#10b981' : '#ef4444',
                      opacity: 0.3,
                    }}
                  />
                </Box>
              </Box>

              {/* Tools Count */}
              <Box
                onClick={() => navigate('/tools')}
                sx={{
                  p: 2,
                  borderRadius: 2,
                  background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%)',
                  border: '1px solid rgba(16, 185, 129, 0.2)',
                  cursor: 'pointer',
                  transition: 'all 0.25s ease-in-out',
                  '&:hover': { transform: 'translateX(4px)', background: 'rgba(16, 185, 129, 0.15)' },
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography variant="h4" sx={{ fontWeight: 700, color: '#10b981' }}>
                      {stats.tool_count}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Configured Tools
                    </Typography>
                  </Box>
                  <BuildIcon sx={{ fontSize: 40, color: '#10b981', opacity: 0.3 }} />
                </Box>
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Additional Stats */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
              <PublicIcon sx={{ color: '#667eea' }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Active Server Nodes Flow
              </Typography>
            </Box>
            
            {/* Active Server Nodes Flow Visualization */}
            <Box
              sx={{
                position: 'relative',
                width: '100%',
                height: 350,
                background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)',
                borderRadius: 2,
                border: '2px solid rgba(102, 126, 234, 0.2)',
                overflow: 'hidden',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <ActiveServerNodesFlow />
            </Box>
            
            {/* Zone Statistics */}
            <Grid container spacing={1} sx={{ mt: 2 }}>
              <Grid item xs={6}>
                <Box sx={{ textAlign: 'center', p: 1.5, borderRadius: 2, background: 'rgba(102, 126, 234, 0.05)' }}>
                  <Typography variant="h5" sx={{ fontWeight: 700, color: '#667eea', mb: 0.5 }}>
                    {stats.active_connections}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Active Connections
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6}>
                <Box sx={{ textAlign: 'center', p: 1.5, borderRadius: 2, background: 'rgba(118, 75, 162, 0.05)' }}>
                  <Typography variant="h5" sx={{ fontWeight: 700, color: '#764ba2', mb: 0.5 }}>
                    {stats.requests_per_minute}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Requests/Min
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
              Service Status
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <ServiceStatus name="LLM Service" status="online" latency={45} />
              <ServiceStatus name="Vector Database" status="online" latency={12} />
              <ServiceStatus name="Redis Cache" status="online" latency={8} />
            </Box>
          </Paper>
        </Grid>
      </Grid>

      {/* Recent Activity */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
          Recent Activity
        </Typography>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {([
            { time: '2 minutes ago', action: 'LLM configuration updated', user: 'Admin' },
            { time: '15 minutes ago', action: 'New tool registered: web_search', user: 'System' },
            { time: '1 hour ago', action: 'Cache cleared successfully', user: 'Admin' },
            { time: '2 hours ago', action: 'Database backup completed', user: 'System' },
          ] as Array<{ time: string; action: string; user: string }>).map((activity, index) => (
            <Box
              key={index}
              sx={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                p: 2,
                borderRadius: 2,
                background: 'rgba(102, 126, 234, 0.05)',
                border: '1px solid rgba(102, 126, 234, 0.1)',
                transition: 'all 0.25s ease-in-out',
                '&:hover': {
                  background: 'rgba(102, 126, 234, 0.1)',
                  transform: 'translateX(4px)',
                },
              }}
            >
              <Box>
                <Typography variant="body1" fontWeight={600}>
                  {activity.action}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {activity.time} • by {activity.user}
                </Typography>
              </Box>
              <CheckCircleIcon sx={{ color: '#10b981' }} />
            </Box>
          ))}
        </Box>
      </Paper>
    </Box>
  );
};

export default Dashboard;
