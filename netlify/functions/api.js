// Netlify serverless function to handle Flask app
const { createProxyMiddleware } = require('http-proxy-middleware');
const express = require('express');
const serverless = require('serverless-http');
const cors = require('cors');

// Create Express app
const app = express();

// Enable CORS
app.use(cors());

// Import Flask app
const { app: flaskApp } = require('../../backend/app');

// Use Flask app as middleware
app.use('/.netlify/functions/api', createProxyMiddleware({
  target: 'http://localhost:8000',
  changeOrigin: true,
  pathRewrite: {
    '^/.netlify/functions/api': ''
  }
}));

// Export handler for serverless
exports.handler = serverless(app);