const express = require('express');
const WebSocket = require('ws');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const port = 8080;

// Serve static files from the 'public' directory
app.use(express.static(path.join(__dirname, 'public')));

// Serve the index.html file
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});


const host = 'localhost';// '192.168.4.1';

// Create the WebSocket server
//const server = app.listen(port, '192.168.4.1', () => {
const server = app.listen(port, host, () => {
  console.log(`Server is listening on http://${host}:${port}`);
});

const wss = new WebSocket.Server({ server });

// Spawn a persistent Python process
const pythonProcess = spawn('python', ['process.py']);
console.log('spawned a python')

pythonProcess.stderr.on('data', (data) => {
  console.error(`Python error: ${data}`);
});

pythonProcess.on('close', (code) => {
  console.log(`Python process exited with code ${code}`);
});

// Buffer for storing Python script output
let pythonOutputBuffer = '';

// Listen for data from the Python process
pythonProcess.stdout.on('data', (data) => {
  //console.log("received data from python")
  pythonOutputBuffer += data.toString();
  // Check if the data is complete (assumes the output is a complete JSON string)
  try{
    const jsonData = JSON.parse(pythonOutputBuffer);
    // Send the data to all connected clients
    wss.clients.forEach((client) => {
      if (client.readyState === WebSocket.OPEN) {
        client.send(JSON.stringify(jsonData));
      }
    });
  } catch(err){
    console.error("Error while sending data to client: ", err.message, ". Received: ", pythonOutputBuffer);
  }

    // Clear the buffer
    pythonOutputBuffer = '';
  
});

wss.on('connection', function connection(ws) {
  ws.on('message', function incoming(message) {
    try {
      const data = JSON.parse(message);

      // Pass the data to the Python process
      pythonProcess.stdin.write(JSON.stringify(data) + '\n');

      // Echo the data back to the client for confirmation or further handling
      //ws.send(JSON.stringify({ status: 'received', ...data }));
    } catch (err) {
        console.error('Error processing message:', err);
    }
  });
  console.log('Client connected');
  ws.send('connected');
});

wss.on('close', function close() {
  pythonProcess.kill(); // Clean up the Python process when the server closes
});
