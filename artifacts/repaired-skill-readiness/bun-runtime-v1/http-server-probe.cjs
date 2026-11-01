'use strict';
const http = require('node:http');
const net = require('node:net');
const result = {
  bun_version: process.versions.bun || null,
  node_compat_version: process.versions.node,
  platform: process.platform,
  http_server_is_net_server: http.createServer() instanceof net.Server,
};
console.log(JSON.stringify(result));
