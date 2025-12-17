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
                Deployment Location - Kuwait
              </Typography>
            </Box>
            
            {/* Kuwait Map */}
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
              {/* Kuwait Map SVG - More Accurate Design */}
              <svg
                viewBox="0 0 500 400"
                style={{ width: '100%', height: '100%' }}
              >
                {/* Background - Sea (Persian Gulf) */}
                <rect x="0" y="0" width="500" height="400" fill="rgba(59, 130, 246, 0.08)" />
                
                {/* Kuwait Country Outline - More Accurate Shape */}
                <path
                  d="M 80 120 L 100 100 L 130 90 L 160 85 L 190 80 L 220 78 L 250 80 L 280 85 L 310 95 L 340 110 L 360 130 L 375 155 L 380 180 L 378 205 L 370 230 L 355 255 L 335 275 L 310 290 L 280 300 L 250 305 L 220 308 L 190 305 L 160 298 L 135 285 L 115 268 L 100 248 L 88 225 L 82 200 L 80 175 L 82 150 L 85 135 Z"
                  fill="rgba(245, 240, 230, 0.95)"
                  stroke="#d4a574"
                  strokeWidth="2.5"
                  style={{
                    filter: 'drop-shadow(0 4px 12px rgba(102, 126, 234, 0.25))',
                  }}
                />
                
                {/* Coastline Detail - Kuwait Bay */}
                <path
                  d="M 280 85 Q 300 100 310 120 Q 315 140 320 160 L 330 180 Q 335 200 330 220 L 320 240"
                  fill="none"
                  stroke="rgba(59, 130, 246, 0.3)"
                  strokeWidth="3"
                />
                
                {/* Bubiyan Island */}
                <ellipse
                  cx="340"
                  cy="100"
                  rx="25"
                  ry="18"
                  fill="rgba(245, 240, 230, 0.9)"
                  stroke="#d4a574"
                  strokeWidth="1.5"
                />
                <text x="340" y="95" textAnchor="middle" fill="#8b7355" fontSize="9" fontWeight="500">
                  Bubiyan
                </text>
                <text x="340" y="107" textAnchor="middle" fill="#8b7355" fontSize="8">
                  Island
                </text>
                
                {/* Major Cities and Locations */}
                
                {/* Kuwait City - Capital (Primary Data Center) */}
                <circle
                  cx="280"
                  cy="180"
                  r="10"
                  fill="#667eea"
                  stroke="#ffffff"
                  strokeWidth="2"
                  style={{
                    filter: 'drop-shadow(0 0 12px #667eea)',
                    animation: 'pulse 2s ease-in-out infinite',
                  }}
                />
                <text
                  x="280"
                  y="205"
                  textAnchor="middle"
                  fill="#667eea"
                  fontSize="13"
                  fontWeight="700"
                >
                  Kuwait City
                </text>
                <text
                  x="280"
                  y="217"
                  textAnchor="middle"
                  fill="#667eea"
                  fontSize="9"
                  opacity="0.8"
                >
                  مدينة الكويت
                </text>
                
                {/* Jahra */}
                <circle cx="220" cy="140" r="6" fill="#f59e0b" stroke="#ffffff" strokeWidth="1.5" />
                <text x="220" y="130" textAnchor="middle" fill="#f59e0b" fontSize="11" fontWeight="600">
                  Jahra
                </text>
                
                {/* Hawalli */}
                <circle cx="295" cy="195" r="6" fill="#764ba2" stroke="#ffffff" strokeWidth="1.5" />
                <text x="295" y="210" textAnchor="middle" fill="#764ba2" fontSize="11" fontWeight="600">
                  Hawalli
                </text>
                
                {/* Farwaniya */}
                <circle cx="250" cy="185" r="6" fill="#10b981" stroke="#ffffff" strokeWidth="1.5" />
                <text x="250" y="175" textAnchor="middle" fill="#10b981" fontSize="11" fontWeight="600">
                  Farwaniya
                </text>
                
                {/* Ahmadi */}
                <circle cx="285" cy="240" r="6" fill="#3b82f6" stroke="#ffffff" strokeWidth="1.5" />
                <text x="285" y="255" textAnchor="middle" fill="#3b82f6" fontSize="11" fontWeight="600">
                  Ahmadi
                </text>
                
                {/* Sabah Al-Ahmad */}
                <circle cx="310" cy="260" r="5" fill="#ec4899" stroke="#ffffff" strokeWidth="1.5" />
                <text x="310" y="273" textAnchor="middle" fill="#ec4899" fontSize="10" fontWeight="500">
                  Sabah Al-Ahmad
                </text>
                
                {/* Al Wafrah */}
                <circle cx="260" cy="270" r="5" fill="#8b5cf6" stroke="#ffffff" strokeWidth="1.5" />
                <text x="260" y="283" textAnchor="middle" fill="#8b5cf6" fontSize="10" fontWeight="500">
                  Al Wafrah
                </text>
                
                {/* Ar Ruqi */}
                <circle cx="140" cy="220" r="5" fill="#f97316" stroke="#ffffff" strokeWidth="1.5" />
                <text x="140" y="233" textAnchor="middle" fill="#f97316" fontSize="10" fontWeight="500">
                  Ar Ruqi
                </text>
                
                {/* Al Khiran */}
                <circle cx="340" cy="280" r="5" fill="#06b6d4" stroke="#ffffff" strokeWidth="1.5" />
                <text x="340" y="293" textAnchor="middle" fill="#06b6d4" fontSize="10" fontWeight="500">
                  Al Khiran
                </text>
                
                {/* Abdali */}
                <circle cx="200" cy="95" r="5" fill="#84cc16" stroke="#ffffff" strokeWidth="1.5" />
                <text x="200" y="88" textAnchor="middle" fill="#84cc16" fontSize="10" fontWeight="500">
                  Abdali
                </text>
                
                {/* Major Roads */}
                <line x1="220" y1="140" x2="280" y2="180" stroke="rgba(212, 165, 116, 0.4)" strokeWidth="2" strokeDasharray="4,4" />
                <line x1="280" y1="180" x2="295" y2="195" stroke="rgba(212, 165, 116, 0.4)" strokeWidth="2" strokeDasharray="4,4" />
                <line x1="280" y1="180" x2="285" y2="240" stroke="rgba(212, 165, 116, 0.4)" strokeWidth="2" strokeDasharray="4,4" />
                
                {/* Highway Numbers */}
                <rect x="245" y="155" width="25" height="15" fill="#ffffff" stroke="#667eea" strokeWidth="1" rx="3" />
                <text x="257.5" y="165" textAnchor="middle" fill="#667eea" fontSize="10" fontWeight="700">
                  80
                </text>
                
                <rect x="295" y="220" width="25" height="15" fill="#ffffff" stroke="#667eea" strokeWidth="1" rx="3" />
                <text x="307.5" y="230" textAnchor="middle" fill="#667eea" fontSize="10" fontWeight="700">
                  40
                </text>
                
                {/* Border Lines */}
                <line x1="80" y1="120" x2="200" y2="95" stroke="#d4a574" strokeWidth="2" strokeDasharray="8,4" opacity="0.6" />
                <line x1="140" y1="220" x2="160" y2="298" stroke="#d4a574" strokeWidth="2" strokeDasharray="8,4" opacity="0.6" />
                
                {/* Compass Rose */}
                <g transform="translate(430, 50)">
                  <circle cx="0" cy="0" r="25" fill="rgba(102, 126, 234, 0.1)" stroke="#667eea" strokeWidth="1.5" />
                  <polygon points="0,-18 3,0 0,18 -3,0" fill="#667eea" />
                  <text x="0" y="-23" textAnchor="middle" fill="#667eea" fontSize="12" fontWeight="700">N</text>
                </g>
                
                {/* Scale Bar */}
                <g transform="translate(50, 350)">
                  <line x1="0" y1="0" x2="80" y2="0" stroke="#667eea" strokeWidth="2" />
                  <line x1="0" y1="-5" x2="0" y2="5" stroke="#667eea" strokeWidth="2" />
                  <line x1="80" y1="-5" x2="80" y2="5" stroke="#667eea" strokeWidth="2" />
                  <text x="40" y="15" textAnchor="middle" fill="#667eea" fontSize="10" fontWeight="600">
                    50 km
                  </text>
                </g>
                
                {/* Coordinates */}
                <text x="420" y="200" fill="rgba(102, 126, 234, 0.6)" fontSize="11" fontWeight="500">
                  29.3°N
                </text>
                <text x="240" y="380" fill="rgba(102, 126, 234, 0.6)" fontSize="11" fontWeight="500">
                  47.9°E
                </text>
                
                {/* Country Label */}
                <text x="180" y="200" textAnchor="middle" fill="#d4a574" fontSize="28" fontWeight="700" opacity="0.3">
                  Kuwait
                </text>
              </svg>
              
              {/* Enhanced Legend */}
              <Box
                sx={{
                  position: 'absolute',
                  bottom: 15,
                  left: 15,
                  background: 'rgba(0, 0, 0, 0.85)',
                  backdropFilter: 'blur(12px)',
                  borderRadius: 2,
                  p: 1.5,
                  border: '1px solid rgba(102, 126, 234, 0.3)',
                }}
              >
                <Typography variant="caption" sx={{ color: 'white', display: 'block', mb: 1, fontWeight: 700 }}>
                  <LocationIcon sx={{ fontSize: 14, verticalAlign: 'middle', mr: 0.5 }} />
                  Deployment Zones
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                  <Typography variant="caption" sx={{ color: '#667eea', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Box sx={{ width: 8, height: 8, borderRadius: '50%', background: '#667eea', boxShadow: '0 0 8px #667eea' }} />
                    Primary Data Center
                  </Typography>
                  <Typography variant="caption" sx={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <Box sx={{ width: 6, height: 6, borderRadius: '50%', background: '#10b981' }} />
                    Active Zones: 9
                  </Typography>
                </Box>
              </Box>
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
