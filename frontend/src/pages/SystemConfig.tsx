import React, { useState, useEffect } from 'react';
import {
  Typography,
  TextField,
  Button,
  Grid,
  Paper,
  Alert,
  Box,
  Tabs,
  Tab,
  Divider,
  IconButton,
  Tooltip,
  Chip,
  Card,
  CardContent,
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  Storage as StorageIcon,
  Cloud as CloudIcon,
  Security as SecurityIcon,
  Cable as CableIcon,
  CheckCircle as CheckIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const SystemConfig: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  // LLM Configuration
  const [llmConfig, setLlmConfig] = useState({
    server_ip: 'localhost',
    server_port: '11434',
    endpoint_path: '/v1/chat/completions',
    api_key: '',
    model: 'llama4-scout',
    timeout: '60',
  });

  // Database Configuration
  const [dbConfig, setDbConfig] = useState({
    postgres_host: 'localhost',
    postgres_port: '5432',
    postgres_db: 'orchestrator',
    postgres_user: 'postgres',
    postgres_password: '',
    redis_host: 'localhost',
    redis_port: '6379',
    redis_password: '',
  });

  // External Agents Configuration
  const [agentsConfig, setAgentsConfig] = useState({
    zain_agent_ip: 'localhost',
    zain_agent_port: '8001',
    zain_agent_path: '/execute',
    zain_agent_token: '',
    custom_agent_ip: '',
    custom_agent_port: '',
    custom_agent_path: '',
    custom_agent_token: '',
  });

  // Data Sources Configuration
  const [dataSourcesConfig, setDataSourcesConfig] = useState({
    cubejs_ip: 'localhost',
    cubejs_port: '4000',
    cubejs_token: '',
    api_endpoint: '',
    api_token: '',
  });

  // Monitoring Configuration
  const [monitoringConfig, setMonitoringConfig] = useState({
    prometheus_ip: '',
    prometheus_port: '9090',
    grafana_ip: '',
    grafana_port: '3000',
    alert_webhook: '',
  });

  // Application Configuration
  const [appConfig, setAppConfig] = useState({
    app_name: 'AI Orchestrator Studio',
    app_version: '1.0.0',
    api_host: '0.0.0.0',
    api_port: '8000',
    frontend_url: 'http://localhost:3000',
    cors_origins: 'http://localhost:3000,http://localhost:8000',
    log_level: 'INFO',
    debug: 'True',
  });

  useEffect(() => {
    loadAllConfigurations();
  }, []);

  const loadAllConfigurations = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/api/config/settings');
      const settings = response.data.settings;

      // Map settings to state
      setLlmConfig({
        server_ip: settings.llm_server_path?.replace('http://', '').replace('https://', '') || 'localhost',
        server_port: settings.llm_port || '11434',
        endpoint_path: settings.llm_endpoint || '/v1/chat/completions',
        api_key: settings.llm_api_key || '',
        model: settings.llm_model || 'llama4-scout',
        timeout: settings.llm_timeout || '60',
      });

      // Load other configs...
    } catch (error) {
      console.error('Error loading configurations:', error);
      setMessage('Error loading configurations');
    } finally {
      setLoading(false);
    }
  };

  const saveAllConfigurations = async () => {
    setLoading(true);
    try {
      // Build complete .env file content
      const envData = {
        // Application
        APP_NAME: appConfig.app_name,
        APP_VERSION: appConfig.app_version,
        API_HOST: appConfig.api_host,
        API_PORT: appConfig.api_port,
        DEBUG: appConfig.debug,
        LOG_LEVEL: appConfig.log_level,
        CORS_ORIGINS: appConfig.cors_origins,

        // LLM
        LLM_BASE_URL: `http://${llmConfig.server_ip}:${llmConfig.server_port}`,
        LLM_DEFAULT_MODEL: llmConfig.model,
        LLM_API_KEY: llmConfig.api_key,
        LLM_TIMEOUT: llmConfig.timeout,

        // Database
        POSTGRES_HOST: dbConfig.postgres_host,
        POSTGRES_PORT: dbConfig.postgres_port,
        POSTGRES_DB: dbConfig.postgres_db,
        POSTGRES_USER: dbConfig.postgres_user,
        POSTGRES_PASSWORD: dbConfig.postgres_password,
        REDIS_URL: `redis://${dbConfig.redis_host}:${dbConfig.redis_port}`,

        // External Agents
        EXTERNAL_AGENT_BASE_URL: `http://${agentsConfig.zain_agent_ip}:${agentsConfig.zain_agent_port}`,
        EXTERNAL_AGENT_AUTH_TOKEN: agentsConfig.zain_agent_token,

        // Data Sources
        DATASOURCE_BASE_URL: `http://${dataSourcesConfig.cubejs_ip}:${dataSourcesConfig.cubejs_port}`,
        DATASOURCE_AUTH_TOKEN: dataSourcesConfig.cubejs_token,
      };

      // Save to .env file
      await axios.post('http://localhost:8000/api/config/env', envData);

      // Save agents configuration
      const agentsData = {
        'zain-agent': {
          name: 'Zain Telecom Agent',
          url: `http://${agentsConfig.zain_agent_ip}:${agentsConfig.zain_agent_port}`,
          auth_token: agentsConfig.zain_agent_token,
          timeout_seconds: 60,
          enabled: true,
        },
      };

      if (agentsConfig.custom_agent_ip && agentsConfig.custom_agent_port) {
        (agentsData as any)['custom-agent'] = {
          name: 'Custom Agent',
          url: `http://${agentsConfig.custom_agent_ip}:${agentsConfig.custom_agent_port}`,
          auth_token: agentsConfig.custom_agent_token,
          timeout_seconds: 60,
          enabled: true,
        };
      }

      await axios.post('http://localhost:8000/api/config/agents', agentsData);

      // Save datasources configuration
      const datasourcesData = {
        'cubejs': {
          name: 'CubeJS Analytics',
          type: 'cubejs',
          url: `http://${dataSourcesConfig.cubejs_ip}:${dataSourcesConfig.cubejs_port}`,
          auth_token: dataSourcesConfig.cubejs_token,
          enabled: true,
        },
      };

      if (dataSourcesConfig.api_endpoint) {
        (datasourcesData as any)['custom-api'] = {
          name: 'Custom API',
          type: 'api',
          url: dataSourcesConfig.api_endpoint,
          auth_token: dataSourcesConfig.api_token,
          enabled: true,
        };
      }

      await axios.post('http://localhost:8000/api/config/datasources', datasourcesData);

      setMessage('✅ All configurations saved successfully! Backend will auto-reload in 2-3 seconds.');
      setTimeout(() => setMessage(''), 5000);
    } catch (error: any) {
      console.error('Error saving configurations:', error);
      setMessage(`❌ Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box className="fade-in">
      <Box sx={{ mb: 4 }}>
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
          System Configuration
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Configure all system components - IPs, ports, paths, and credentials
        </Typography>
      </Box>

      {message && (
        <Alert
          severity={message.includes('❌') ? 'error' : 'success'}
          sx={{ mb: 3 }}
          onClose={() => setMessage('')}
        >
          {message}
        </Alert>
      )}

      {/* Save All Button */}
      <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
        <Button
          variant="contained"
          size="large"
          startIcon={<SaveIcon />}
          onClick={saveAllConfigurations}
          disabled={loading}
          sx={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            px: 4,
          }}
        >
          Save All Configurations
        </Button>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={loadAllConfigurations}
          disabled={loading}
          sx={{
            borderColor: '#667eea',
            color: '#667eea',
          }}
        >
          Reload
        </Button>
        <Chip
          icon={<CheckIcon />}
          label="Auto-saves to .env and config files"
          color="success"
          sx={{ ml: 'auto' }}
        />
      </Box>

      {/* Configuration Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={(e, newValue) => setTabValue(newValue)}
          sx={{
            borderBottom: 1,
            borderColor: 'divider',
            '& .MuiTab-root': {
              fontWeight: 600,
            },
          }}
        >
          <Tab icon={<SettingsIcon />} label="Application" />
          <Tab icon={<CloudIcon />} label="LLM Server" />
          <Tab icon={<StorageIcon />} label="Databases" />
          <Tab icon={<CableIcon />} label="External Agents" />
          <Tab icon={<StorageIcon />} label="Data Sources" />
          <Tab icon={<SecurityIcon />} label="Monitoring" />
        </Tabs>

        {/* Tab 0: Application Configuration */}
        <TabPanel value={tabValue} index={0}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
            Application Settings
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                label="Application Name"
                fullWidth
                value={appConfig.app_name}
                onChange={(e) => setAppConfig({ ...appConfig, app_name: e.target.value })}
                helperText="Display name of the application"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Version"
                fullWidth
                value={appConfig.app_version}
                onChange={(e) => setAppConfig({ ...appConfig, app_version: e.target.value })}
                helperText="Application version"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="API Host"
                fullWidth
                value={appConfig.api_host}
                onChange={(e) => setAppConfig({ ...appConfig, api_host: e.target.value })}
                helperText="Backend API host (0.0.0.0 for all interfaces)"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="API Port"
                fullWidth
                type="number"
                value={appConfig.api_port}
                onChange={(e) => setAppConfig({ ...appConfig, api_port: e.target.value })}
                helperText="Backend API port"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Frontend URL"
                fullWidth
                value={appConfig.frontend_url}
                onChange={(e) => setAppConfig({ ...appConfig, frontend_url: e.target.value })}
                helperText="Frontend application URL"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="CORS Origins"
                fullWidth
                value={appConfig.cors_origins}
                onChange={(e) => setAppConfig({ ...appConfig, cors_origins: e.target.value })}
                helperText="Comma-separated list of allowed origins"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Log Level"
                fullWidth
                value={appConfig.log_level}
                onChange={(e) => setAppConfig({ ...appConfig, log_level: e.target.value })}
                helperText="DEBUG, INFO, WARNING, ERROR"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Debug Mode"
                fullWidth
                value={appConfig.debug}
                onChange={(e) => setAppConfig({ ...appConfig, debug: e.target.value })}
                helperText="True or False"
              />
            </Grid>
          </Grid>
        </TabPanel>

        {/* Tab 1: LLM Configuration */}
        <TabPanel value={tabValue} index={1}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
            LLM Server Configuration
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                label="Server IP / Hostname"
                fullWidth
                value={llmConfig.server_ip}
                onChange={(e) => setLlmConfig({ ...llmConfig, server_ip: e.target.value })}
                placeholder="localhost or 192.168.1.100"
                helperText="LLM server IP address or hostname"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Server Port"
                fullWidth
                type="number"
                value={llmConfig.server_port}
                onChange={(e) => setLlmConfig({ ...llmConfig, server_port: e.target.value })}
                placeholder="11434"
                helperText="LLM server port number"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Endpoint Path"
                fullWidth
                value={llmConfig.endpoint_path}
                onChange={(e) => setLlmConfig({ ...llmConfig, endpoint_path: e.target.value })}
                placeholder="/v1/chat/completions"
                helperText="API endpoint path"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="API Key / Auth Token"
                fullWidth
                type="password"
                value={llmConfig.api_key}
                onChange={(e) => setLlmConfig({ ...llmConfig, api_key: e.target.value })}
                placeholder="Optional - leave blank if not needed"
                helperText="Authentication token (if required)"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Model Name"
                fullWidth
                value={llmConfig.model}
                onChange={(e) => setLlmConfig({ ...llmConfig, model: e.target.value })}
                placeholder="llama4-scout"
                helperText="Default model to use"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Timeout (seconds)"
                fullWidth
                type="number"
                value={llmConfig.timeout}
                onChange={(e) => setLlmConfig({ ...llmConfig, timeout: e.target.value })}
                helperText="Request timeout"
              />
            </Grid>
            <Grid item xs={12}>
              <Card sx={{ background: 'rgba(102, 126, 234, 0.05)' }}>
                <CardContent>
                  <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                    Full LLM URL:
                  </Typography>
                  <Typography variant="body1" sx={{ fontFamily: 'monospace', color: '#667eea', fontWeight: 600 }}>
                    http://{llmConfig.server_ip}:{llmConfig.server_port}{llmConfig.endpoint_path}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        {/* Tab 2: Database Configuration */}
        <TabPanel value={tabValue} index={2}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
            Database Configuration
          </Typography>

          {/* PostgreSQL */}
          <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600, mt: 2, mb: 2 }}>
            PostgreSQL
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                label="PostgreSQL Host"
                fullWidth
                value={dbConfig.postgres_host}
                onChange={(e) => setDbConfig({ ...dbConfig, postgres_host: e.target.value })}
                placeholder="localhost or IP"
                helperText="PostgreSQL server address"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="PostgreSQL Port"
                fullWidth
                type="number"
                value={dbConfig.postgres_port}
                onChange={(e) => setDbConfig({ ...dbConfig, postgres_port: e.target.value })}
                placeholder="5432"
                helperText="PostgreSQL port"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                label="Database Name"
                fullWidth
                value={dbConfig.postgres_db}
                onChange={(e) => setDbConfig({ ...dbConfig, postgres_db: e.target.value })}
                placeholder="orchestrator"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                label="Username"
                fullWidth
                value={dbConfig.postgres_user}
                onChange={(e) => setDbConfig({ ...dbConfig, postgres_user: e.target.value })}
                placeholder="postgres"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                label="Password"
                fullWidth
                type="password"
                value={dbConfig.postgres_password}
                onChange={(e) => setDbConfig({ ...dbConfig, postgres_password: e.target.value })}
                placeholder="••••••••"
              />
            </Grid>
          </Grid>

          <Divider sx={{ my: 4 }} />

          {/* Redis */}
          <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
            Redis Cache
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                label="Redis Host"
                fullWidth
                value={dbConfig.redis_host}
                onChange={(e) => setDbConfig({ ...dbConfig, redis_host: e.target.value })}
                placeholder="localhost or IP"
                helperText="Redis server address"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Redis Port"
                fullWidth
                type="number"
                value={dbConfig.redis_port}
                onChange={(e) => setDbConfig({ ...dbConfig, redis_port: e.target.value })}
                placeholder="6379"
                helperText="Redis port"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Redis Password"
                fullWidth
                type="password"
                value={dbConfig.redis_password}
                onChange={(e) => setDbConfig({ ...dbConfig, redis_password: e.target.value })}
                placeholder="Optional"
                helperText="Leave blank if no password"
              />
            </Grid>
          </Grid>
        </TabPanel>

        {/* Tab 3: External Agents */}
        <TabPanel value={tabValue} index={3}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
            External Agents Configuration
          </Typography>

          {/* Zain Agent */}
          <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600, mt: 2, mb: 2 }}>
            Zain Telecom Agent
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <TextField
                label="Agent IP / Hostname"
                fullWidth
                value={agentsConfig.zain_agent_ip}
                onChange={(e) => setAgentsConfig({ ...agentsConfig, zain_agent_ip: e.target.value })}
                placeholder="localhost or IP"
                helperText="Zain agent server address"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                label="Agent Port"
                fullWidth
                type="number"
                value={agentsConfig.zain_agent_port}
                onChange={(e) => setAgentsConfig({ ...agentsConfig, zain_agent_port: e.target.value })}
                placeholder="8001"
                helperText="Agent port"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                label="Endpoint Path"
                fullWidth
                value={agentsConfig.zain_agent_path}
                onChange={(e) => setAgentsConfig({ ...agentsConfig, zain_agent_path: e.target.value })}
                placeholder="/execute"
                helperText="API endpoint"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Auth Token"
                fullWidth
                type="password"
                value={agentsConfig.zain_agent_token}
                onChange={(e) => setAgentsConfig({ ...agentsConfig, zain_agent_token: e.target.value })}
                placeholder="Optional"
                helperText="Authentication token"
              />
            </Grid>
            <Grid item xs={12}>
              <Card sx={{ background: 'rgba(102, 126, 234, 0.05)' }}>
                <CardContent>
                  <Typography variant="caption" color="text.secondary" gutterBottom display="block">
                    Full Agent URL:
                  </Typography>
                  <Typography variant="body1" sx={{ fontFamily: 'monospace', color: '#667eea', fontWeight: 600 }}>
                    http://{agentsConfig.zain_agent_ip}:{agentsConfig.zain_agent_port}{agentsConfig.zain_agent_path}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          <Divider sx={{ my: 4 }} />

          {/* Custom Agent */}
          <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
            Custom Agent (Optional)
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <TextField
                label="Agent IP / Hostname"
                fullWidth
                value={agentsConfig.custom_agent_ip}
                onChange={(e) => setAgentsConfig({ ...agentsConfig, custom_agent_ip: e.target.value })}
                placeholder="Optional"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                label="Agent Port"
                fullWidth
                type="number"
                value={agentsConfig.custom_agent_port}
                onChange={(e) => setAgentsConfig({ ...agentsConfig, custom_agent_port: e.target.value })}
                placeholder="Optional"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                label="Endpoint Path"
                fullWidth
                value={agentsConfig.custom_agent_path}
                onChange={(e) => setAgentsConfig({ ...agentsConfig, custom_agent_path: e.target.value })}
                placeholder="/api/execute"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="Auth Token"
                fullWidth
                type="password"
                value={agentsConfig.custom_agent_token}
                onChange={(e) => setAgentsConfig({ ...agentsConfig, custom_agent_token: e.target.value })}
                placeholder="Optional"
              />
            </Grid>
          </Grid>
        </TabPanel>

        {/* Tab 4: Data Sources */}
        <TabPanel value={tabValue} index={4}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
            Data Sources Configuration
          </Typography>

          {/* CubeJS */}
          <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600, mt: 2, mb: 2 }}>
            CubeJS Analytics
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                label="CubeJS IP / Hostname"
                fullWidth
                value={dataSourcesConfig.cubejs_ip}
                onChange={(e) => setDataSourcesConfig({ ...dataSourcesConfig, cubejs_ip: e.target.value })}
                placeholder="localhost or IP"
                helperText="CubeJS server address"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="CubeJS Port"
                fullWidth
                type="number"
                value={dataSourcesConfig.cubejs_port}
                onChange={(e) => setDataSourcesConfig({ ...dataSourcesConfig, cubejs_port: e.target.value })}
                placeholder="4000"
                helperText="CubeJS port"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="CubeJS Auth Token"
                fullWidth
                type="password"
                value={dataSourcesConfig.cubejs_token}
                onChange={(e) => setDataSourcesConfig({ ...dataSourcesConfig, cubejs_token: e.target.value })}
                placeholder="Optional"
                helperText="CubeJS authentication token"
              />
            </Grid>
          </Grid>

          <Divider sx={{ my: 4 }} />

          {/* Custom API */}
          <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
            Custom API Data Source (Optional)
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                label="API Endpoint URL"
                fullWidth
                value={dataSourcesConfig.api_endpoint}
                onChange={(e) => setDataSourcesConfig({ ...dataSourcesConfig, api_endpoint: e.target.value })}
                placeholder="http://api.example.com/data"
                helperText="Full URL to custom API"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                label="API Auth Token"
                fullWidth
                type="password"
                value={dataSourcesConfig.api_token}
                onChange={(e) => setDataSourcesConfig({ ...dataSourcesConfig, api_token: e.target.value })}
                placeholder="Optional"
                helperText="API authentication token"
              />
            </Grid>
          </Grid>
        </TabPanel>

        {/* Tab 5: Monitoring */}
        <TabPanel value={tabValue} index={5}>
          <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
            Monitoring & Alerting Configuration
          </Typography>

          {/* Prometheus */}
          <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600, mt: 2, mb: 2 }}>
            Prometheus (Optional)
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                label="Prometheus IP"
                fullWidth
                value={monitoringConfig.prometheus_ip}
                onChange={(e) => setMonitoringConfig({ ...monitoringConfig, prometheus_ip: e.target.value })}
                placeholder="localhost or IP"
                helperText="Prometheus server address"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Prometheus Port"
                fullWidth
                type="number"
                value={monitoringConfig.prometheus_port}
                onChange={(e) => setMonitoringConfig({ ...monitoringConfig, prometheus_port: e.target.value })}
                placeholder="9090"
              />
            </Grid>
          </Grid>

          <Divider sx={{ my: 4 }} />

          {/* Grafana */}
          <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
            Grafana (Optional)
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                label="Grafana IP"
                fullWidth
                value={monitoringConfig.grafana_ip}
                onChange={(e) => setMonitoringConfig({ ...monitoringConfig, grafana_ip: e.target.value })}
                placeholder="localhost or IP"
                helperText="Grafana server address"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Grafana Port"
                fullWidth
                type="number"
                value={monitoringConfig.grafana_port}
                onChange={(e) => setMonitoringConfig({ ...monitoringConfig, grafana_port: e.target.value })}
                placeholder="3000"
              />
            </Grid>
          </Grid>

          <Divider sx={{ my: 4 }} />

          {/* Alerts */}
          <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
            Alert Webhook
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                label="Webhook URL"
                fullWidth
                value={monitoringConfig.alert_webhook}
                onChange={(e) => setMonitoringConfig({ ...monitoringConfig, alert_webhook: e.target.value })}
                placeholder="https://hooks.slack.com/services/..."
                helperText="Webhook URL for alerts (Slack, Discord, etc.)"
              />
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default SystemConfig;
