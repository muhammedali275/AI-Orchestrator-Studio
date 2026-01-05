import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Divider,
  Box,
  Typography,
  useTheme,
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import ChatIcon from '@mui/icons-material/Chat';
import SettingsIcon from '@mui/icons-material/Settings';
import BuildIcon from '@mui/icons-material/Build';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart';
import MemoryIcon from '@mui/icons-material/Memory';
import SecurityIcon from '@mui/icons-material/Security';
import HttpsIcon from '@mui/icons-material/Https';
import PsychologyIcon from '@mui/icons-material/Psychology';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import RouterIcon from '@mui/icons-material/Router';
import InfoIcon from '@mui/icons-material/Info';
import SystemUpdateIcon from '@mui/icons-material/SystemUpdate';

const drawerWidth = 280;

interface MenuItem {
  text: string;
  path: string;
  icon: React.ReactElement;
  badge?: string;
}

// Updated menu items according to requirements
const menuItems: MenuItem[] = [
  { text: 'Dashboard', path: '/', icon: <DashboardIcon /> },
  { text: 'LLM Connections', path: '/llm', icon: <SettingsIcon /> },
  { text: 'Agents & System Prompts', path: '/agents', icon: <PsychologyIcon /> },
  { text: 'Tools & Data Sources', path: '/tools', icon: <BuildIcon /> },
  { text: 'Routers & Planners', path: '/routers-planners', icon: <RouterIcon /> },
  { text: 'Orchestration Flow', path: '/topology', icon: <AccountTreeIcon /> },
  { text: 'Credentials & Security', path: '/credentials', icon: <SecurityIcon /> },
  { text: 'Certificates (HTTPS)', path: '/certificates', icon: <HttpsIcon /> },
  { text: 'Monitoring & Services', path: '/monitoring', icon: <MonitorHeartIcon /> },
  { text: 'Caching & Memory', path: '/memory', icon: <MemoryIcon /> },
  { text: 'Upgrades & Dependencies', path: '/upgrades', icon: <SystemUpdateIcon /> },
  { text: 'Internal Chat Test', path: '/chat', icon: <ChatIcon /> },
  { text: 'About', path: '/about', icon: <InfoIcon /> },
];

const adminMenuItem: MenuItem = {
  text: 'Admin Panel',
  path: '/admin',
  icon: <AdminPanelSettingsIcon />,
  badge: 'Admin',
};

const Sidebar: React.FC = () => {
  const location = useLocation();
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
          background: isDark
            ? 'linear-gradient(180deg, #1a1a2e 0%, #16213e 100%)'
            : 'linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)',
          borderRight: isDark
            ? '1px solid rgba(102, 126, 234, 0.1)'
            : '1px solid rgba(0, 0, 0, 0.08)',
          boxShadow: isDark
            ? '4px 0 24px rgba(0, 0, 0, 0.3)'
            : '4px 0 24px rgba(0, 0, 0, 0.08)',
        },
      }}
    >
      {/* Logo Section */}
      <Box
        sx={{
          p: 3,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          background: isDark
            ? 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)'
            : 'linear-gradient(135deg, rgba(90, 103, 216, 0.08) 0%, rgba(107, 70, 193, 0.08) 100%)',
          borderBottom: isDark
            ? '1px solid rgba(102, 126, 234, 0.2)'
            : '1px solid rgba(0, 0, 0, 0.08)',
        }}
      >
        {/* Glassmorphism Logo Container */}
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            padding: '16px 20px',
            mb: 2,
            borderRadius: '16px',
            background: isDark
              ? 'linear-gradient(135deg, rgba(26, 32, 44, 0.7) 0%, rgba(45, 55, 72, 0.7) 100%)'
              : 'linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(247, 250, 252, 0.9) 100%)',
            backdropFilter: 'blur(10px)',
            WebkitBackdropFilter: 'blur(10px)',
            border: isDark
              ? '1px solid rgba(255, 255, 255, 0.1)'
              : '1px solid rgba(226, 232, 240, 0.8)',
            boxShadow: isDark
              ? '0 8px 32px rgba(0, 0, 0, 0.2), 0 0 16px rgba(102, 126, 234, 0.2)'
              : '0 8px 32px rgba(226, 232, 240, 0.5), 0 0 16px rgba(90, 103, 216, 0.1)',
            position: 'relative',
            overflow: 'hidden',
            transition: 'all 0.3s ease-in-out',
            '&:hover': {
              transform: 'translateY(-2px)',
              boxShadow: isDark
                ? '0 12px 40px rgba(0, 0, 0, 0.3), 0 0 20px rgba(102, 126, 234, 0.4)'
                : '0 12px 40px rgba(226, 232, 240, 0.6), 0 0 20px rgba(90, 103, 216, 0.2)',
            },
            '&::before': {
              content: '""',
              position: 'absolute',
              top: '-50%',
              left: '-50%',
              width: '200%',
              height: '200%',
              background: isDark
                ? 'radial-gradient(circle, rgba(102, 126, 234, 0.1) 0%, transparent 70%)'
                : 'radial-gradient(circle, rgba(90, 103, 216, 0.05) 0%, transparent 70%)',
              opacity: 0.5,
              transform: 'rotate(30deg)',
            },
          }}
        >
          <Typography
            variant="h5"
            sx={{
              fontWeight: 700,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              letterSpacing: '0.5px',
              filter: isDark ? 'brightness(1.2) drop-shadow(0 0 8px rgba(102, 126, 234, 0.4))' : 'drop-shadow(0 0 8px rgba(90, 103, 216, 0.3))',
              transition: 'all 0.3s ease-in-out',
              zIndex: 2,
              position: 'relative',
              '&:hover': {
                transform: 'scale(1.03)',
                filter: isDark ? 'brightness(1.2) drop-shadow(0 0 12px rgba(102, 126, 234, 0.6))' : 'brightness(1.1) drop-shadow(0 0 12px rgba(90, 103, 216, 0.5))',
              },
            }}
          >
            AI Orchestrator
          </Typography>
        </Box>
        <Typography
          variant="body2"
          sx={{
            color: 'text.secondary',
            textAlign: 'center',
            mb: 0.5,
            fontSize: '0.85rem',
            opacity: 0.7,
          }}
        >
          Studio
        </Typography>
        <Typography
          variant="caption"
          sx={{
            color: 'text.secondary',
            textAlign: 'center',
            fontWeight: 500,
            letterSpacing: '0.5px',
          }}
        >
          Intelligent Workflow Management
        </Typography>
      </Box>

      <Divider sx={{ borderColor: isDark ? 'rgba(102, 126, 234, 0.1)' : 'rgba(0, 0, 0, 0.08)' }} />

      {/* Main Menu */}
      <List sx={{ px: 1, py: 2 }}>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
            <ListItemButton
              component={Link}
              to={item.path}
              selected={location.pathname === item.path}
              sx={{
                borderRadius: 2,
                mx: 1,
                transition: 'all 0.25s ease-in-out',
                '&:hover': {
                  backgroundColor: isDark
                    ? 'rgba(102, 126, 234, 0.15)'
                    : 'rgba(90, 103, 216, 0.1)',
                  transform: 'translateX(4px)',
                  '& .MuiListItemIcon-root': {
                    color: isDark ? '#667eea' : '#5a67d8',
                    transform: 'scale(1.1)',
                  },
                },
                '&.Mui-selected': {
                  backgroundColor: isDark
                    ? 'rgba(102, 126, 234, 0.2)'
                    : 'rgba(90, 103, 216, 0.15)',
                  borderLeft: isDark ? '3px solid #667eea' : '3px solid #5a67d8',
                  '&:hover': {
                    backgroundColor: isDark
                      ? 'rgba(102, 126, 234, 0.25)'
                      : 'rgba(90, 103, 216, 0.2)',
                  },
                  '& .MuiListItemIcon-root': {
                    color: isDark ? '#667eea' : '#5a67d8',
                  },
                  '& .MuiListItemText-primary': {
                    color: isDark ? '#667eea' : '#5a67d8',
                    fontWeight: 600,
                  },
                },
              }}
            >
              <ListItemIcon
                sx={{
                  color: location.pathname === item.path
                    ? (isDark ? '#667eea' : '#5a67d8')
                    : 'text.secondary',
                  minWidth: 40,
                  transition: 'all 0.25s ease-in-out',
                }}
              >
                {item.icon}
              </ListItemIcon>
              <ListItemText
                primary={item.text}
                primaryTypographyProps={{
                  fontSize: '0.95rem',
                  fontWeight: location.pathname === item.path ? 600 : 500,
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Divider sx={{ borderColor: isDark ? 'rgba(102, 126, 234, 0.1)' : 'rgba(0, 0, 0, 0.08)', my: 1 }} />

      {/* Admin Section */}
      <List sx={{ px: 1, py: 1 }}>
        <ListItem disablePadding>
          <ListItemButton
            component={Link}
            to={adminMenuItem.path}
            selected={location.pathname === adminMenuItem.path}
            sx={{
              borderRadius: 2,
              mx: 1,
              background: location.pathname === adminMenuItem.path
                ? (isDark
                  ? 'linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.2) 100%)'
                  : 'linear-gradient(135deg, rgba(220, 38, 38, 0.15) 0%, rgba(185, 28, 28, 0.15) 100%)')
                : (isDark ? 'rgba(239, 68, 68, 0.05)' : 'rgba(220, 38, 38, 0.05)'),
              border: isDark
                ? '1px solid rgba(239, 68, 68, 0.2)'
                : '1px solid rgba(220, 38, 38, 0.2)',
              transition: 'all 0.25s ease-in-out',
              '&:hover': {
                background: isDark
                  ? 'linear-gradient(135deg, rgba(239, 68, 68, 0.25) 0%, rgba(220, 38, 38, 0.25) 100%)'
                  : 'linear-gradient(135deg, rgba(220, 38, 38, 0.2) 0%, rgba(185, 28, 28, 0.2) 100%)',
                transform: 'translateX(4px)',
                borderColor: isDark ? 'rgba(239, 68, 68, 0.4)' : 'rgba(220, 38, 38, 0.4)',
                '& .MuiListItemIcon-root': {
                  color: isDark ? '#ef4444' : '#dc2626',
                  transform: 'scale(1.1) rotate(10deg)',
                },
              },
              '&.Mui-selected': {
                background: isDark
                  ? 'linear-gradient(135deg, rgba(239, 68, 68, 0.3) 0%, rgba(220, 38, 38, 0.3) 100%)'
                  : 'linear-gradient(135deg, rgba(220, 38, 38, 0.25) 0%, rgba(185, 28, 28, 0.25) 100%)',
                borderLeft: isDark ? '3px solid #ef4444' : '3px solid #dc2626',
                '& .MuiListItemIcon-root': {
                  color: isDark ? '#ef4444' : '#dc2626',
                },
                '& .MuiListItemText-primary': {
                  color: isDark ? '#ef4444' : '#dc2626',
                  fontWeight: 600,
                },
              },
            }}
          >
            <ListItemIcon
              sx={{
                color: location.pathname === adminMenuItem.path
                  ? (isDark ? '#ef4444' : '#dc2626')
                  : (isDark ? '#f87171' : '#ef4444'),
                minWidth: 40,
                transition: 'all 0.25s ease-in-out',
              }}
            >
              {adminMenuItem.icon}
            </ListItemIcon>
            <ListItemText
              primary={adminMenuItem.text}
              primaryTypographyProps={{
                fontSize: '0.95rem',
                fontWeight: location.pathname === adminMenuItem.path ? 600 : 500,
              }}
            />
            {adminMenuItem.badge && (
              <Box
                sx={{
                  px: 1,
                  py: 0.5,
                  borderRadius: 1,
                  background: isDark
                    ? 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
                    : 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)',
                  fontSize: '0.7rem',
                  fontWeight: 700,
                  color: 'white',
                  boxShadow: isDark
                    ? '0 0 10px rgba(239, 68, 68, 0.4)'
                    : '0 0 10px rgba(220, 38, 38, 0.4)',
                }}
              >
                {adminMenuItem.badge}
              </Box>
            )}
          </ListItemButton>
        </ListItem>
      </List>

      {/* Footer */}
      <Box
        sx={{
          mt: 'auto',
          p: 2,
          borderTop: isDark
            ? '1px solid rgba(102, 126, 234, 0.1)'
            : '1px solid rgba(0, 0, 0, 0.08)',
          background: isDark
            ? 'rgba(102, 126, 234, 0.05)'
            : 'rgba(90, 103, 216, 0.05)',
        }}
      >
        <Typography
          variant="caption"
          sx={{
            display: 'block',
            textAlign: 'center',
            color: 'text.secondary',
            mb: 0.5,
          }}
        >
          v{(process.env as any)?.REACT_APP_VERSION || 'dev'}
        </Typography>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 0.5,
          }}
        >
          <Box
            sx={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: '#10b981',
              boxShadow: '0 0 8px #10b981',
              animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            }}
          />
          <Typography variant="caption" sx={{ color: '#10b981', fontWeight: 600 }}>
            System Online
          </Typography>
        </Box>
      </Box>
    </Drawer>
  );
};

export default Sidebar;
