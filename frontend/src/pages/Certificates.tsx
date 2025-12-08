import React, { useState, useEffect } from 'react';
import {
  Typography,
  Paper,
  Box,
  Button,
  Grid,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  Alert,
  Chip,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Https as HttpsIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Upload as UploadIcon,
  Security as SecurityIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface CertificateInfo {
  tls_enabled: boolean;
  cert_path: string | null;
  key_path: string | null;
  cert_exists: boolean;
  key_exists: boolean;
}

const Certificates: React.FC = () => {
  const [certInfo, setCertInfo] = useState<CertificateInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [certFile, setCertFile] = useState<File | null>(null);
  const [keyFile, setKeyFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [toggling, setToggling] = useState(false);

  useEffect(() => {
    fetchCertificateInfo();
  }, []);

  const fetchCertificateInfo = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:8000/api/certs');
      setCertInfo(response.data);
    } catch (error) {
      console.error('Error fetching certificate info:', error);
      setMessage('Error loading certificate information');
    } finally {
      setLoading(false);
    }
  };

  const handleCertFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setCertFile(event.target.files[0]);
    }
  };

  const handleKeyFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setKeyFile(event.target.files[0]);
    }
  };

  const handleUploadCertificates = async () => {
    if (!certFile || !keyFile) {
      setMessage('Please select both certificate and key files');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('cert_file', certFile);
    formData.append('key_file', keyFile);

    try {
      const response = await axios.post('http://localhost:8000/api/certs/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setMessage('Certificates uploaded successfully!');
      setCertFile(null);
      setKeyFile(null);
      fetchCertificateInfo();
      setTimeout(() => setMessage(''), 3000);
    } catch (error: any) {
      setMessage(`Error uploading certificates: ${error.response?.data?.detail || error.message}`);
    } finally {
      setUploading(false);
    }
  };

  const handleToggleTLS = async (enable: boolean) => {
    setToggling(true);
    try {
      const endpoint = enable ? '/api/certs/enable' : '/api/certs/disable';
      await axios.post(`http://localhost:8000${endpoint}`);
      setMessage(`TLS ${enable ? 'enabled' : 'disabled'} successfully!`);
      fetchCertificateInfo();
      setTimeout(() => setMessage(''), 3000);
    } catch (error: any) {
      setMessage(`Error: ${error.response?.data?.detail || error.message}`);
    } finally {
      setToggling(false);
    }
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
            Certificates (HTTPS)
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage TLS/SSL certificates for secure HTTPS connections
          </Typography>
        </Box>
        <Tooltip title="Refresh Status">
          <IconButton
            onClick={fetchCertificateInfo}
            disabled={loading}
            sx={{
              background: 'rgba(102, 126, 234, 0.1)',
              '&:hover': { background: 'rgba(102, 126, 234, 0.2)' },
            }}
          >
            <RefreshIcon />
          </IconButton>
        </Tooltip>
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

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3}>
          {/* Current Status */}
          <Grid item xs={12} md={6}>
            <Card
              sx={{
                background: certInfo?.tls_enabled
                  ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%)'
                  : 'linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%)',
                border: certInfo?.tls_enabled
                  ? '1px solid rgba(16, 185, 129, 0.3)'
                  : '1px solid rgba(239, 68, 68, 0.3)',
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                  <HttpsIcon
                    sx={{
                      fontSize: 48,
                      color: certInfo?.tls_enabled ? '#10b981' : '#ef4444',
                    }}
                  />
                  <Box>
                    <Typography variant="h5" sx={{ fontWeight: 700 }}>
                      TLS Status
                    </Typography>
                    <Chip
                      icon={certInfo?.tls_enabled ? <CheckCircleIcon /> : <ErrorIcon />}
                      label={certInfo?.tls_enabled ? 'Enabled' : 'Disabled'}
                      color={certInfo?.tls_enabled ? 'success' : 'error'}
                      sx={{ mt: 1, fontWeight: 600 }}
                    />
                  </Box>
                </Box>

                <Divider sx={{ my: 2 }} />

                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
                    Certificate Status
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                    {certInfo?.cert_exists ? (
                      <CheckCircleIcon sx={{ color: '#10b981', fontSize: 20 }} />
                    ) : (
                      <ErrorIcon sx={{ color: '#ef4444', fontSize: 20 }} />
                    )}
                    <Typography variant="body2">
                      Certificate: {certInfo?.cert_exists ? 'Installed' : 'Not Found'}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {certInfo?.key_exists ? (
                      <CheckCircleIcon sx={{ color: '#10b981', fontSize: 20 }} />
                    ) : (
                      <ErrorIcon sx={{ color: '#ef4444', fontSize: 20 }} />
                    )}
                    <Typography variant="body2">
                      Private Key: {certInfo?.key_exists ? 'Installed' : 'Not Found'}
                    </Typography>
                  </Box>
                </Box>

                {certInfo?.cert_path && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Certificate Path:
                    </Typography>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                      {certInfo.cert_path}
                    </Typography>
                  </Box>
                )}

                {certInfo?.key_path && (
                  <Box sx={{ mt: 1 }}>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Key Path:
                    </Typography>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                      {certInfo.key_path}
                    </Typography>
                  </Box>
                )}

                <Box sx={{ mt: 3 }}>
                  {certInfo?.cert_exists && certInfo?.key_exists ? (
                    <Button
                      variant="contained"
                      fullWidth
                      onClick={() => handleToggleTLS(!certInfo.tls_enabled)}
                      disabled={toggling}
                      startIcon={toggling ? <CircularProgress size={20} /> : <HttpsIcon />}
                      sx={{
                        background: certInfo.tls_enabled
                          ? 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
                          : 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                      }}
                    >
                      {certInfo.tls_enabled ? 'Disable TLS' : 'Enable TLS'}
                    </Button>
                  ) : (
                    <Alert severity="warning" icon={<WarningIcon />}>
                      Upload certificates to enable TLS
                    </Alert>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Upload Certificates */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
                Upload Certificates
              </Typography>

              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
                  Certificate File (certificate.pem)
                </Typography>
                <Box
                  sx={{
                    border: '2px dashed rgba(102, 126, 234, 0.3)',
                    borderRadius: 2,
                    p: 3,
                    textAlign: 'center',
                    background: 'rgba(102, 126, 234, 0.05)',
                    cursor: 'pointer',
                    transition: 'all 0.3s',
                    '&:hover': {
                      borderColor: '#667eea',
                      background: 'rgba(102, 126, 234, 0.1)',
                    },
                  }}
                  onClick={() => document.getElementById('cert-file-input')?.click()}
                >
                  <input
                    id="cert-file-input"
                    type="file"
                    accept=".pem,.crt,.cer"
                    onChange={handleCertFileChange}
                    style={{ display: 'none' }}
                  />
                  <UploadIcon sx={{ fontSize: 48, color: '#667eea', mb: 1 }} />
                  <Typography variant="body2" color="text.secondary">
                    {certFile ? certFile.name : 'Click to select certificate file'}
                  </Typography>
                </Box>
              </Box>

              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
                  Private Key File (private_key.pem)
                </Typography>
                <Box
                  sx={{
                    border: '2px dashed rgba(118, 75, 162, 0.3)',
                    borderRadius: 2,
                    p: 3,
                    textAlign: 'center',
                    background: 'rgba(118, 75, 162, 0.05)',
                    cursor: 'pointer',
                    transition: 'all 0.3s',
                    '&:hover': {
                      borderColor: '#764ba2',
                      background: 'rgba(118, 75, 162, 0.1)',
                    },
                  }}
                  onClick={() => document.getElementById('key-file-input')?.click()}
                >
                  <input
                    id="key-file-input"
                    type="file"
                    accept=".pem,.key"
                    onChange={handleKeyFileChange}
                    style={{ display: 'none' }}
                  />
                  <SecurityIcon sx={{ fontSize: 48, color: '#764ba2', mb: 1 }} />
                  <Typography variant="body2" color="text.secondary">
                    {keyFile ? keyFile.name : 'Click to select private key file'}
                  </Typography>
                </Box>
              </Box>

              <Button
                variant="contained"
                fullWidth
                onClick={handleUploadCertificates}
                disabled={!certFile || !keyFile || uploading}
                startIcon={uploading ? <CircularProgress size={20} /> : <UploadIcon />}
                sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
              >
                {uploading ? 'Uploading...' : 'Upload Certificates'}
              </Button>
            </Paper>
          </Grid>

          {/* Security Best Practices */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <InfoIcon sx={{ color: '#3b82f6', fontSize: 32 }} />
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Security Best Practices
                </Typography>
              </Box>

              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <List dense>
                    <ListItem>
                      <ListItemIcon>
                        <CheckCircleIcon sx={{ color: '#10b981' }} />
                      </ListItemIcon>
                      <ListItemText
                        primary="Use Strong Encryption"
                        secondary="Ensure certificates use at least 2048-bit RSA or 256-bit ECC"
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <CheckCircleIcon sx={{ color: '#10b981' }} />
                      </ListItemIcon>
                      <ListItemText
                        primary="Keep Private Keys Secure"
                        secondary="Never share or commit private keys to version control"
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <CheckCircleIcon sx={{ color: '#10b981' }} />
                      </ListItemIcon>
                      <ListItemText
                        primary="Regular Renewal"
                        secondary="Renew certificates before expiration (typically 90 days)"
                      />
                    </ListItem>
                  </List>
                </Grid>
                <Grid item xs={12} md={6}>
                  <List dense>
                    <ListItem>
                      <ListItemIcon>
                        <CheckCircleIcon sx={{ color: '#10b981' }} />
                      </ListItemIcon>
                      <ListItemText
                        primary="Use Trusted CAs"
                        secondary="Obtain certificates from trusted Certificate Authorities"
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <CheckCircleIcon sx={{ color: '#10b981' }} />
                      </ListItemIcon>
                      <ListItemText
                        primary="Monitor Expiration"
                        secondary="Set up alerts for certificate expiration dates"
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <CheckCircleIcon sx={{ color: '#10b981' }} />
                      </ListItemIcon>
                      <ListItemText
                        primary="Test After Upload"
                        secondary="Verify HTTPS is working correctly after enabling TLS"
                      />
                    </ListItem>
                  </List>
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          {/* Certificate Generation Guide */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3, background: 'rgba(102, 126, 234, 0.05)' }}>
              <Typography variant="h6" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
                Generate Self-Signed Certificate (Development Only)
              </Typography>
              <Alert severity="warning" sx={{ mb: 2 }}>
                Self-signed certificates should only be used for development. Use certificates from trusted CAs in production.
              </Alert>
              <Box
                sx={{
                  p: 2,
                  background: '#1e1e1e',
                  borderRadius: 2,
                  fontFamily: 'monospace',
                  fontSize: '0.85rem',
                  color: '#d4d4d4',
                  overflow: 'auto',
                }}
              >
                <Typography component="pre" sx={{ m: 0, color: '#d4d4d4' }}>
{`# Generate private key
openssl genrsa -out private_key.pem 2048

# Generate certificate signing request
openssl req -new -key private_key.pem -out certificate.csr

# Generate self-signed certificate (valid for 365 days)
openssl x509 -req -days 365 -in certificate.csr \\
  -signkey private_key.pem -out certificate.pem`}
                </Typography>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default Certificates;
