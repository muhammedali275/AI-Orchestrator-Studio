import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

// Suppress Chrome extension errors (MetaMask, etc.) from polluting the error overlay
const originalError = console.error;
console.error = (...args: any[]) => {
  const message = args[0]?.toString() || '';
  
  // Suppress known Chrome extension errors
  if (
    message.includes('chrome-extension://') ||
    message.includes('MetaMask') ||
    message.includes('Failed to connect to MetaMask')
  ) {
    return; // Silently ignore
  }
  
  // Pass through all other errors
  originalError.apply(console, args);
};

// Global error handler to suppress extension errors
window.addEventListener('error', (event) => {
  const message = event.message || event.error?.message || '';
  const filename = event.filename || '';
  
  // Suppress Chrome extension errors
  if (
    filename.includes('chrome-extension://') ||
    message.includes('MetaMask') ||
    message.includes('Failed to connect to MetaMask') ||
    filename.includes('nkbihfbeogaeaoehlefnkodbefgpgknn')
  ) {
    event.preventDefault();
    event.stopPropagation();
    return true; // Prevent default error handling
  }
});

// Suppress unhandled promise rejections from extensions
window.addEventListener('unhandledrejection', (event) => {
  const message = event.reason?.message || event.reason?.toString() || '';
  
  if (
    message.includes('chrome-extension://') ||
    message.includes('MetaMask') ||
    message.includes('Failed to connect to MetaMask')
  ) {
    event.preventDefault();
    event.stopPropagation();
  }
});

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
