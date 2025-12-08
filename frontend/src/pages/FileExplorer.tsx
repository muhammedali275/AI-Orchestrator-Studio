import React, { useState, useEffect } from 'react';
import {
  Typography,
  Box,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Chip,
} from '@mui/material';
import {
  Folder as FolderIcon,
  InsertDriveFile as FileIcon,
  Home as HomeIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Close as CloseIcon,
  ChevronRight as ChevronRightIcon,
  Code as CodeIcon,
  Description as DescriptionIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import axios from 'axios';

interface FileNode {
  name: string;
  type: 'file' | 'directory';
  path: string;
  children?: FileNode[];
  extension?: string;
}

const FileExplorer: React.FC = () => {
  const [fileTree, setFileTree] = useState<FileNode[]>([]);
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set(['orchestrator/app']));
  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null);
  const [fileContent, setFileContent] = useState('');
  const [open, setOpen] = useState(false);

  useEffect(() => {
    loadFileStructure();
  }, []);

  const loadFileStructure = async () => {
    try {
      // Try to fetch actual file structure from backend
      const response = await axios.get('http://localhost:8000/api/files/list?path=orchestrator');
      const files = response.data.files;
      
      // Build tree structure from flat file list
      const tree = buildTreeFromFiles(files, 'orchestrator');
      setFileTree(tree);
    } catch (error) {
      console.error('Error loading file structure:', error);
      // Fallback to static structure
      loadStaticStructure();
    }
  };

  const buildTreeFromFiles = (files: any[], basePath: string): FileNode[] => {
    const tree: FileNode[] = [];
    const pathMap = new Map<string, FileNode>();

    // Sort files to ensure directories come before their contents
    files.sort((a: any, b: any) => {
      const aDepth = a.path.split('/').length;
      const bDepth = b.path.split('/').length;
      return aDepth - bDepth;
    });

    files.forEach((file: any) => {
      const fullPath = `${basePath}/${file.path}`;
      const parts = file.path.split('/');
      const name = parts[parts.length - 1];
      const extension = name.includes('.') ? name.split('.').pop() : undefined;

      const node: FileNode = {
        name,
        type: file.type,
        path: fullPath,
        extension,
        children: file.type === 'directory' ? [] : undefined,
      };

      pathMap.set(fullPath, node);

      if (parts.length === 1) {
        // Top level
        tree.push(node);
      } else {
        // Find parent
        const parentPath = `${basePath}/${parts.slice(0, -1).join('/')}`;
        const parent = pathMap.get(parentPath);
        if (parent && parent.children) {
          parent.children.push(node);
        }
      }
    });

    return tree;
  };

  const loadStaticStructure = () => {
    // Fallback static structure for orchestrator
    const structure: FileNode[] = [
      {
        name: 'app',
        type: 'directory',
        path: 'orchestrator/app',
        children: [
          { name: '__init__.py', type: 'file', path: 'orchestrator/app/__init__.py', extension: 'py' },
          { name: 'main.py', type: 'file', path: 'orchestrator/app/main.py', extension: 'py' },
          { name: 'graph.py', type: 'file', path: 'orchestrator/app/graph.py', extension: 'py' },
          { name: 'config.py', type: 'file', path: 'orchestrator/app/config.py', extension: 'py' },
          {
            name: 'api',
            type: 'directory',
            path: 'orchestrator/app/api',
            children: [
              { name: '__init__.py', type: 'file', path: 'orchestrator/app/api/__init__.py', extension: 'py' },
              { name: 'chat.py', type: 'file', path: 'orchestrator/app/api/chat.py', extension: 'py' },
            ],
          },
          {
            name: 'clients',
            type: 'directory',
            path: 'orchestrator/app/clients',
            children: [
              { name: '__init__.py', type: 'file', path: 'orchestrator/app/clients/__init__.py', extension: 'py' },
              { name: 'llm_client.py', type: 'file', path: 'orchestrator/app/clients/llm_client.py', extension: 'py' },
              { name: 'external_agent_client.py', type: 'file', path: 'orchestrator/app/clients/external_agent_client.py', extension: 'py' },
              { name: 'datasource_client.py', type: 'file', path: 'orchestrator/app/clients/datasource_client.py', extension: 'py' },
            ],
          },
          {
            name: 'memory',
            type: 'directory',
            path: 'orchestrator/app/memory',
            children: [
              { name: '__init__.py', type: 'file', path: 'orchestrator/app/memory/__init__.py', extension: 'py' },
              { name: 'conversation_memory.py', type: 'file', path: 'orchestrator/app/memory/conversation_memory.py', extension: 'py' },
              { name: 'cache.py', type: 'file', path: 'orchestrator/app/memory/cache.py', extension: 'py' },
              { name: 'state_store.py', type: 'file', path: 'orchestrator/app/memory/state_store.py', extension: 'py' },
            ],
          },
          {
            name: 'tools',
            type: 'directory',
            path: 'orchestrator/app/tools',
            children: [
              { name: '__init__.py', type: 'file', path: 'orchestrator/app/tools/__init__.py', extension: 'py' },
              { name: 'base.py', type: 'file', path: 'orchestrator/app/tools/base.py', extension: 'py' },
              { name: 'http_tool.py', type: 'file', path: 'orchestrator/app/tools/http_tool.py', extension: 'py' },
              { name: 'web_search_tool.py', type: 'file', path: 'orchestrator/app/tools/web_search_tool.py', extension: 'py' },
              { name: 'code_executor_tool.py', type: 'file', path: 'orchestrator/app/tools/code_executor_tool.py', extension: 'py' },
              { name: 'registry.py', type: 'file', path: 'orchestrator/app/tools/registry.py', extension: 'py' },
            ],
          },
          {
            name: 'reasoning',
            type: 'directory',
            path: 'orchestrator/app/reasoning',
            children: [
              { name: '__init__.py', type: 'file', path: 'orchestrator/app/reasoning/__init__.py', extension: 'py' },
              { name: 'router_prompt.py', type: 'file', path: 'orchestrator/app/reasoning/router_prompt.py', extension: 'py' },
              { name: 'planner.py', type: 'file', path: 'orchestrator/app/reasoning/planner.py', extension: 'py' },
            ],
          },
        ],
      },
      {
        name: 'requirements.txt',
        type: 'file',
        path: 'orchestrator/requirements.txt',
        extension: 'txt',
      },
      {
        name: '.env.example',
        type: 'file',
        path: 'orchestrator/.env.example',
        extension: 'example',
      },
      {
        name: 'README.md',
        type: 'file',
        path: 'orchestrator/README.md',
        extension: 'md',
      },
    ];

    setFileTree(structure);
  };

  const toggleFolder = (path: string) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(path)) {
      newExpanded.delete(path);
    } else {
      newExpanded.add(path);
    }
    setExpandedFolders(newExpanded);
  };

  const handleFileClick = async (file: FileNode) => {
    if (file.type === 'file') {
      setSelectedFile(file);
      try {
        // Remove 'orchestrator/' prefix for API call since backend expects relative path
        const apiPath = file.path.replace('orchestrator/', '');
        const response = await axios.get(`http://localhost:8000/api/files/content?path=${apiPath}`);
        setFileContent(response.data.content);
        setOpen(true);
      } catch (error) {
        console.error('Error fetching file content:', error);
        setFileContent(`# ${file.name}\n\n// Error loading file content. Please check if the backend is running.`);
        setOpen(true);
      }
    } else {
      toggleFolder(file.path);
    }
  };

  const handleSave = async () => {
    if (selectedFile) {
      try {
        // Remove 'orchestrator/' prefix for API call
        const apiPath = selectedFile.path.replace('orchestrator/', '');
        await axios.put(`http://localhost:8000/api/files/content?path=${apiPath}`, {
          content: fileContent,
        });
        setOpen(false);
        alert('File saved successfully!');
      } catch (error) {
        console.error('Error saving file:', error);
        alert('Error saving file. Please check if the backend is running.');
      }
    }
  };

  const handleClose = () => {
    setOpen(false);
    setSelectedFile(null);
    setFileContent('');
  };

  const getFileIcon = (node: FileNode) => {
    if (node.type === 'directory') {
      return <FolderIcon sx={{ color: '#667eea' }} />;
    }
    
    switch (node.extension) {
      case 'py':
        return <CodeIcon sx={{ color: '#3b82f6' }} />;
      case 'yaml':
      case 'yml':
        return <SettingsIcon sx={{ color: '#f59e0b' }} />;
      case 'env':
      case 'example':
        return <SettingsIcon sx={{ color: '#10b981' }} />;
      case 'md':
      case 'txt':
        return <DescriptionIcon sx={{ color: '#8b5cf6' }} />;
      default:
        return <FileIcon sx={{ color: '#a1a1aa' }} />;
    }
  };

  const renderTree = (nodes: FileNode[], level: number = 0) => {
    return nodes.map((node) => {
      const isExpanded = expandedFolders.has(node.path);
      const hasChildren = node.children && node.children.length > 0;

      return (
        <Box key={node.path}>
          <Box
            onClick={() => handleFileClick(node)}
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              py: 0.75,
              px: 2,
              pl: 2 + level * 2,
              cursor: 'pointer',
              borderRadius: 1,
              transition: 'all 0.2s ease-in-out',
              '&:hover': {
                background: 'rgba(102, 126, 234, 0.1)',
                transform: 'translateX(4px)',
              },
            }}
          >
            {node.type === 'directory' && (
              <IconButton
                size="small"
                sx={{
                  p: 0,
                  transition: 'transform 0.2s ease-in-out',
                  transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)',
                }}
              >
                <ChevronRightIcon fontSize="small" />
              </IconButton>
            )}
            {getFileIcon(node)}
            <Typography
              variant="body2"
              sx={{
                fontWeight: node.type === 'directory' ? 600 : 400,
                color: node.type === 'directory' ? '#667eea' : 'text.primary',
              }}
            >
              {node.name}
            </Typography>
            {node.extension && (
              <Chip
                label={node.extension}
                size="small"
                sx={{
                  height: 18,
                  fontSize: '0.7rem',
                  ml: 'auto',
                  background: 'rgba(102, 126, 234, 0.1)',
                  color: '#667eea',
                }}
              />
            )}
          </Box>
          {node.type === 'directory' && isExpanded && hasChildren && (
            <Box>{renderTree(node.children!, level + 1)}</Box>
          )}
        </Box>
      );
    });
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
          File Explorer
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Browse and edit orchestrator files
        </Typography>
      </Box>

      <Paper
        sx={{
          p: 3,
          minHeight: '600px',
          background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.02) 0%, rgba(118, 75, 162, 0.02) 100%)',
        }}
      >
        <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
          <HomeIcon sx={{ color: '#667eea' }} />
          <Typography variant="body2" color="text.secondary">
            /orchestrator
          </Typography>
        </Box>

        <Box>{renderTree(fileTree)}</Box>
      </Paper>

      {/* File Editor Dialog */}
      <Dialog open={open} onClose={handleClose} maxWidth="lg" fullWidth>
        <DialogTitle
          sx={{
            background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
            display: 'flex',
            alignItems: 'center',
            gap: 1,
          }}
        >
          <EditIcon sx={{ color: '#667eea' }} />
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            {selectedFile?.name}
          </Typography>
          <Chip
            label={selectedFile?.extension || 'file'}
            size="small"
            sx={{
              background: 'rgba(102, 126, 234, 0.2)',
              color: '#667eea',
              fontWeight: 600,
            }}
          />
        </DialogTitle>
        <DialogContent sx={{ mt: 2 }}>
          <TextField
            multiline
            fullWidth
            rows={25}
            value={fileContent}
            onChange={(e) => setFileContent(e.target.value)}
            variant="outlined"
            sx={{
              '& .MuiOutlinedInput-root': {
                fontFamily: 'monospace',
                fontSize: '0.9rem',
                lineHeight: 1.6,
              },
            }}
          />
        </DialogContent>
        <DialogActions sx={{ p: 2, gap: 1 }}>
          <Button onClick={handleClose} startIcon={<CloseIcon />}>
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            variant="contained"
            startIcon={<SaveIcon />}
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            }}
          >
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FileExplorer;
