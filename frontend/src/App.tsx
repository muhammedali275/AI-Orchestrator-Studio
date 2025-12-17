import React, { useState, useMemo } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { IconButton, Tooltip, Box } from '@mui/material';
import { Brightness4, Brightness7 } from '@mui/icons-material';
import Dashboard from './pages/Dashboard';
import FileExplorer from './pages/FileExplorer';
import LLMConnections from './pages/LLMConnections';
import DBManagement from './pages/DBManagement';
import Upgrades from './pages/Upgrades';
import MemoryCache from './pages/MemoryCache';
import ToolsDataSources from './pages/ToolsDataSources';
import RoutersPlannersConfig from './pages/RoutersPlannersConfig';
import Topology from './pages/Topology';
import MonitoringServices from './pages/MonitoringServices';
import AdminPanel from './pages/AdminPanel';
import ChatStudio from './pages/ChatStudio';
import AgentsConfig from './pages/AgentsConfig';
import CredentialsSecurity from './pages/CredentialsSecurity';
import Certificates from './pages/Certificates';
import About from './pages/About';
import Sidebar from './components/Sidebar';

const getTheme = (mode: 'light' | 'dark') => createTheme({
  palette: {
    mode,
    primary: {
      main: mode === 'dark' ? '#667eea' : '#5a67d8',
      light: mode === 'dark' ? '#8b9ef5' : '#7c8aed',
      dark: mode === 'dark' ? '#4d5fd1' : '#4c51bf',
      contrastText: '#ffffff',
    },
    secondary: {
      main: mode === 'dark' ? '#764ba2' : '#6b46c1',
      light: mode === 'dark' ? '#9168b8' : '#8b5cf6',
      dark: mode === 'dark' ? '#5a3880' : '#553c9a',
      contrastText: '#ffffff',
    },
    background: {
      default: mode === 'dark' ? '#0f0f23' : '#f8fafc',
      paper: mode === 'dark' ? '#1a1a2e' : '#ffffff',
    },
    text: {
      primary: mode === 'dark' ? '#e4e4e7' : '#1e293b',
      secondary: mode === 'dark' ? '#a1a1aa' : '#64748b',
    },
    success: {
      main: mode === 'dark' ? '#10b981' : '#059669',
      light: mode === 'dark' ? '#34d399' : '#10b981',
      dark: mode === 'dark' ? '#059669' : '#047857',
    },
    warning: {
      main: mode === 'dark' ? '#f59e0b' : '#d97706',
      light: mode === 'dark' ? '#fbbf24' : '#f59e0b',
      dark: mode === 'dark' ? '#d97706' : '#b45309',
    },
    error: {
      main: mode === 'dark' ? '#ef4444' : '#dc2626',
      light: mode === 'dark' ? '#f87171' : '#ef4444',
      dark: mode === 'dark' ? '#dc2626' : '#b91c1c',
    },
    info: {
      main: mode === 'dark' ? '#3b82f6' : '#2563eb',
      light: mode === 'dark' ? '#60a5fa' : '#3b82f6',
      dark: mode === 'dark' ? '#2563eb' : '#1d4ed8',
    },
  },
  typography: {
    fontFamily: [
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    h1: {
      fontWeight: 700,
      fontSize: '2.5rem',
      letterSpacing: '-0.02em',
    },
    h2: {
      fontWeight: 700,
      fontSize: '2rem',
      letterSpacing: '-0.01em',
    },
    h3: {
      fontWeight: 600,
      fontSize: '1.75rem',
    },
    h4: {
      fontWeight: 600,
      fontSize: '1.5rem',
    },
    h5: {
      fontWeight: 600,
      fontSize: '1.25rem',
    },
    h6: {
      fontWeight: 600,
      fontSize: '1rem',
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          padding: '10px 24px',
          boxShadow: 'none',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          fontWeight: 600,
          '&:hover': {
            boxShadow: mode === 'dark' 
              ? '0 8px 16px rgba(102, 126, 234, 0.4), 0 0 20px rgba(102, 126, 234, 0.2)'
              : '0 8px 16px rgba(90, 103, 216, 0.3), 0 0 20px rgba(90, 103, 216, 0.15)',
            transform: 'translateY(-2px)',
          },
          '&:active': {
            transform: 'translateY(0)',
          },
        },
        contained: {
          background: mode === 'dark'
            ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
            : 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
          '&:hover': {
            background: mode === 'dark'
              ? 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)'
              : 'linear-gradient(135deg, #6b46c1 0%, #5a67d8 100%)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          backgroundColor: mode === 'dark' ? '#16213e' : '#ffffff',
          borderRadius: 16,
          border: mode === 'dark' 
            ? '1px solid rgba(255, 255, 255, 0.08)' 
            : '1px solid rgba(0, 0, 0, 0.08)',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          boxShadow: mode === 'dark'
            ? '0 4px 6px -1px rgba(0, 0, 0, 0.3)'
            : '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
        },
        elevation1: {
          boxShadow: mode === 'dark'
            ? '0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2)'
            : '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        },
        elevation2: {
          boxShadow: mode === 'dark'
            ? '0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -2px rgba(0, 0, 0, 0.3)'
            : '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          border: mode === 'dark' 
            ? '1px solid rgba(255, 255, 255, 0.08)' 
            : '1px solid rgba(0, 0, 0, 0.08)',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          overflow: 'hidden',
          '&:hover': {
            transform: 'translateY(-6px) scale(1.02)',
            boxShadow: mode === 'dark'
              ? '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2), 0 0 30px rgba(102, 126, 234, 0.4)'
              : '0 20px 25px -5px rgba(0, 0, 0, 0.15), 0 10px 10px -5px rgba(0, 0, 0, 0.08), 0 0 30px rgba(90, 103, 216, 0.3)',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 10,
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            backgroundColor: mode === 'dark' ? 'rgba(255, 255, 255, 0.03)' : 'rgba(0, 0, 0, 0.02)',
            '&:hover': {
              backgroundColor: mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.03)',
              '& .MuiOutlinedInput-notchedOutline': {
                borderColor: mode === 'dark' ? '#667eea' : '#5a67d8',
              },
            },
            '&.Mui-focused': {
              backgroundColor: mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.03)',
              '& .MuiOutlinedInput-notchedOutline': {
                borderColor: mode === 'dark' ? '#667eea' : '#5a67d8',
                borderWidth: 2,
                boxShadow: mode === 'dark'
                  ? '0 0 0 4px rgba(102, 126, 234, 0.15)'
                  : '0 0 0 4px rgba(90, 103, 216, 0.15)',
              },
            },
          },
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          margin: '4px 8px',
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            backgroundColor: mode === 'dark' 
              ? 'rgba(102, 126, 234, 0.15)' 
              : 'rgba(90, 103, 216, 0.1)',
            transform: 'translateX(6px)',
          },
          '&.Mui-selected': {
            backgroundColor: mode === 'dark' 
              ? 'rgba(102, 126, 234, 0.25)' 
              : 'rgba(90, 103, 216, 0.15)',
            borderLeft: mode === 'dark' ? '4px solid #667eea' : '4px solid #5a67d8',
            fontWeight: 600,
            '&:hover': {
              backgroundColor: mode === 'dark' 
                ? 'rgba(102, 126, 234, 0.3)' 
                : 'rgba(90, 103, 216, 0.2)',
            },
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          fontWeight: 600,
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            transform: 'scale(1.05)',
          },
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          border: '1px solid',
          fontWeight: 500,
        },
        standardSuccess: {
          backgroundColor: mode === 'dark' 
            ? 'rgba(16, 185, 129, 0.15)' 
            : 'rgba(16, 185, 129, 0.1)',
          borderColor: mode === 'dark' 
            ? 'rgba(16, 185, 129, 0.4)' 
            : 'rgba(16, 185, 129, 0.3)',
        },
        standardError: {
          backgroundColor: mode === 'dark' 
            ? 'rgba(239, 68, 68, 0.15)' 
            : 'rgba(239, 68, 68, 0.1)',
          borderColor: mode === 'dark' 
            ? 'rgba(239, 68, 68, 0.4)' 
            : 'rgba(239, 68, 68, 0.3)',
        },
        standardWarning: {
          backgroundColor: mode === 'dark' 
            ? 'rgba(245, 158, 11, 0.15)' 
            : 'rgba(245, 158, 11, 0.1)',
          borderColor: mode === 'dark' 
            ? 'rgba(245, 158, 11, 0.4)' 
            : 'rgba(245, 158, 11, 0.3)',
        },
        standardInfo: {
          backgroundColor: mode === 'dark' 
            ? 'rgba(59, 130, 246, 0.15)' 
            : 'rgba(59, 130, 246, 0.1)',
          borderColor: mode === 'dark' 
            ? 'rgba(59, 130, 246, 0.4)' 
            : 'rgba(59, 130, 246, 0.3)',
        },
      },
    },
  },
});

function App() {
  const [mode, setMode] = useState<'light' | 'dark'>('dark');

  const theme = useMemo(() => getTheme(mode), [mode]);

  const toggleColorMode = () => {
    setMode((prevMode) => (prevMode === 'light' ? 'dark' : 'light'));
  };

  // Update document title
  React.useEffect(() => {
    document.title = 'AI Orchestrator Studio';
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <div style={{ display: 'flex', minHeight: '100vh' }}>
          <Sidebar />
          <main style={{ 
            flexGrow: 1, 
            padding: '24px',
            background: mode === 'dark'
              ? 'linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #0f0f23 100%)'
              : 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #f8fafc 100%)',
            minHeight: '100vh',
            position: 'relative',
          }}>
            {/* Theme Toggle Button */}
            <Box
              sx={{
                position: 'fixed',
                top: 20,
                right: 20,
                zIndex: 1000,
              }}
            >
              <Tooltip title={`Switch to ${mode === 'dark' ? 'light' : 'dark'} mode`}>
                <IconButton
                  onClick={toggleColorMode}
                  sx={{
                    background: mode === 'dark'
                      ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                      : 'linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%)',
                    color: 'white',
                    boxShadow: mode === 'dark'
                      ? '0 4px 12px rgba(102, 126, 234, 0.4)'
                      : '0 4px 12px rgba(90, 103, 216, 0.3)',
                    '&:hover': {
                      background: mode === 'dark'
                        ? 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)'
                        : 'linear-gradient(135deg, #6b46c1 0%, #5a67d8 100%)',
                      transform: 'rotate(180deg) scale(1.1)',
                      boxShadow: mode === 'dark'
                        ? '0 6px 16px rgba(102, 126, 234, 0.5)'
                        : '0 6px 16px rgba(90, 103, 216, 0.4)',
                    },
                    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                  }}
                >
                  {mode === 'dark' ? <Brightness7 /> : <Brightness4 />}
                </IconButton>
              </Tooltip>
            </Box>

            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/llm" element={<LLMConnections />} />
              <Route path="/agents" element={<AgentsConfig />} />
              <Route path="/tools" element={<ToolsDataSources />} />
              <Route path="/routers-planners" element={<RoutersPlannersConfig />} />
              <Route path="/topology" element={<Topology />} />
              <Route path="/credentials" element={<CredentialsSecurity />} />
              <Route path="/certificates" element={<Certificates />} />
              <Route path="/monitoring" element={<MonitoringServices />} />
              <Route path="/chat" element={<ChatStudio />} />
              <Route path="/files" element={<FileExplorer />} />
              <Route path="/memory" element={<MemoryCache />} />
              <Route path="/db" element={<DBManagement />} />
              <Route path="/upgrades" element={<Upgrades />} />
              <Route path="/admin" element={<AdminPanel />} />
              <Route path="/about" element={<About />} />
            </Routes>
          </main>
        </div>
      </Router>
    </ThemeProvider>
  );
}

export default App;
