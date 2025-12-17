import React from 'react';
import { Box, Paper, Typography, Divider, Chip } from '@mui/material';
import { Info as InfoIcon } from '@mui/icons-material';

const APP_VERSION = (process.env as any)?.REACT_APP_VERSION || 'dev';

const About: React.FC = () => {
  return (
    <Box className="fade-in">
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', alignItems: 'center', gap: 2 }}>
        <InfoIcon sx={{ fontSize: 40, color: 'primary.main' }} />
        <Box>
          <Typography
            variant="h3"
            sx={{
              fontWeight: 700,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
              mb: 0.5,
            }}
          >
            About
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Application Information
          </Typography>
        </Box>
      </Box>

      {/* Main Content */}
      <Paper
        sx={{
          p: 4,
          background: (theme) =>
            theme.palette.mode === 'dark'
              ? 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)'
              : 'linear-gradient(135deg, rgba(90, 103, 216, 0.03) 0%, rgba(107, 70, 193, 0.03) 100%)',
          border: (theme) =>
            theme.palette.mode === 'dark'
              ? '1px solid rgba(102, 126, 234, 0.2)'
              : '1px solid rgba(0, 0, 0, 0.08)',
        }}
      >
        {/* App Name & Version */}
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
            AI Orchestrator Studio
          </Typography>
          <Chip
            label={`Version ${APP_VERSION}`}
            color="primary"
            variant="outlined"
            sx={{ fontWeight: 600 }}
          />
        </Box>

        <Divider sx={{ my: 3 }} />

        {/* App Definition */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
            What is AI Orchestrator Studio?
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            AI Orchestrator Studio is an enterprise-grade AI orchestration platform designed to
            seamlessly integrate Large Language Models (LLMs), tools, and data sources. It enables
            organizations to build powerful, intelligent workflows with advanced routing, planning,
            validation, and grounding capabilities.
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            The platform leverages LangGraph for state machine orchestration, LangChain for modular
            tool integration, and supports multiple LLM providers including Ollama and OpenAI-compatible
            servers. With built-in caching (Redis, Qdrant/FAISS), query validation gates, and
            observability tools, it ensures fast, reliable, and governed AI-powered applications.
          </Typography>
        </Box>

        <Divider sx={{ my: 3 }} />

        {/* Key Features */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
            Key Features
          </Typography>
          <Box component="ul" sx={{ pl: 3 }}>
            <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              <strong>Intelligent Routing:</strong> Rule-based and semantic routing for analytics, documents, and chat.
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              <strong>Multi-Layer Caching:</strong> Exact (Redis), semantic (Qdrant/FAISS), and result caching for instant responses.
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              <strong>Query Validation:</strong> Hard gates for metric validation, PII blocking, and data governance.
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              <strong>Grounded Answers:</strong> LLM-generated explanations backed by real data with evidence tracking.
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              <strong>Streaming Responses:</strong> Server-Sent Events (SSE) for real-time token delivery.
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              <strong>Conversation Memory:</strong> Persistent chat history with database-backed state management.
            </Typography>
            <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              <strong>Observability:</strong> Full latency breakdown, cache hit/miss tracking, and SLA monitoring.
            </Typography>
          </Box>
        </Box>

        <Divider sx={{ my: 3 }} />

        {/* Copyright */}
        <Box sx={{ textAlign: 'center', mt: 4 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            © 2025 Muhammed Ali
          </Typography>
          <Typography variant="caption" color="text.secondary">
            All rights reserved. This software is proprietary and confidential.
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
};

export default About;
