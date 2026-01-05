import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  useTheme,
} from '@mui/material';
import {
  Person as PersonIcon,
  SmartToy as BotIcon,
  ExpandMore as ExpandMoreIcon,
  Build as ToolIcon,
} from '@mui/icons-material';

interface Message {
  id: string;
  role: string;
  content: string;
  metadata?: any;
  created_at: string;
}

interface ChatMessageProps {
  message: Message;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        mb: 2,
      }}
    >
      <Box
        sx={{
          maxWidth: '75%',
          display: 'flex',
          flexDirection: 'column',
          gap: 1,
        }}
      >
        {/* Message Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 1 }}>
          {isUser ? (
            <PersonIcon sx={{ fontSize: 16, color: 'primary.main' }} />
          ) : isAssistant ? (
            <BotIcon sx={{ fontSize: 16, color: 'secondary.main' }} />
          ) : (
            <ToolIcon sx={{ fontSize: 16, color: 'warning.main' }} />
          )}
          <Typography variant="caption" color="text.secondary">
            {isUser ? 'You' : isAssistant ? 'Assistant' : 'Tool'}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            •
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {formatTime(message.created_at)}
          </Typography>
        </Box>

        {/* Message Content */}
        <Paper
          elevation={1}
          sx={{
            p: 2,
            backgroundColor: isUser
              ? (isDark ? 'rgba(102, 126, 234, 0.15)' : 'rgba(90, 103, 216, 0.1)')
              : (isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)'),
            borderRadius: 3,
            border: isUser
              ? (isDark ? '1px solid rgba(102, 126, 234, 0.3)' : '1px solid rgba(90, 103, 216, 0.3)')
              : (isDark ? '1px solid rgba(255, 255, 255, 0.1)' : '1px solid rgba(0, 0, 0, 0.1)'),
          }}
        >
          <Typography
            variant="body1"
            sx={{
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              '& p': { margin: 0 },
              '& pre': {
                backgroundColor: isDark ? 'rgba(0, 0, 0, 0.3)' : 'rgba(0, 0, 0, 0.05)',
                padding: 2,
                borderRadius: 1,
                overflow: 'auto',
              },
              '& code': {
                backgroundColor: isDark ? 'rgba(0, 0, 0, 0.3)' : 'rgba(0, 0, 0, 0.05)',
                padding: '2px 6px',
                borderRadius: 1,
                fontFamily: 'monospace',
              },
            }}
          >
            {message.content}
          </Typography>
        </Paper>

        {/* Metadata - Tool Calls, etc. */}
        {message.metadata && Object.keys(message.metadata).length > 0 && (
          <Box sx={{ px: 1 }}>
            {message.metadata.tools_used && message.metadata.tools_used.length > 0 && (
              <Accordion
                sx={{
                  backgroundColor: isDark ? 'rgba(255, 255, 255, 0.03)' : 'rgba(0, 0, 0, 0.02)',
                  boxShadow: 'none',
                  '&:before': { display: 'none' },
                }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ToolIcon sx={{ fontSize: 16, color: 'warning.main' }} />
                    <Typography variant="caption">
                      Tools Used ({message.metadata.tools_used.length})
                    </Typography>
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {message.metadata.tools_used.map((tool: string, index: number) => (
                      <Chip
                        key={index}
                        label={tool}
                        size="small"
                        color="warning"
                        variant="outlined"
                      />
                    ))}
                  </Box>
                </AccordionDetails>
              </Accordion>
            )}

            {message.metadata.model_used && (
              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                Model: {message.metadata.model_used}
              </Typography>
            )}

            {message.metadata.routing_profile && (
              <Chip
                label={message.metadata.routing_profile}
                size="small"
                variant="outlined"
                sx={{ mt: 0.5 }}
              />
            )}
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default ChatMessage;
