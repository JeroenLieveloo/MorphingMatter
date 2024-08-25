const host = 'localhost'; //192.168.4.1';
let scale = 0.3;
let canvasSize = 200;
const delay = 100;


const socket = new WebSocket('ws://'+host+':8080');
const cursorPositionDiv = document.getElementById('cursorPosition');
const svgContainer = document.getElementById('svgContainer');
let isSending = false;
let actuators;
let lastTime = 0;
let isPaused = false;

function getPressureColor(pressure){
  return 'rgba(' + pressure*200 + ', 152, 219, 0.5)'
}

function getActuationSize(actuation){
  return 10+30*actuation;
}

function togglePause(){
  isPaused = !isPaused;
  setHold(isPaused);
}

function setRelease(release){
  console.log('Setting release to:', release);
  socket.send(JSON.stringify({release: release}));
}

function setScale(input){
  scale = input;
  drawActuators()
}

function setMode(mode){
  console.log('Setting mode to:', mode);
  socket.send(JSON.stringify({mode: mode}));
}

function setSpeed(speed){
  console.log('Setting speed to:', speed);
  socket.send(JSON.stringify({speed: speed}));
}

function setStrength(strength){
  console.log('Setting strength to:', strength);
  socket.send(JSON.stringify({strength: strength}));
}

function setSize(size){
  console.log('Setting size to:', size);
  socket.send(JSON.stringify({size: size}));
}

function setHold(hold){
  console.log('Setting hold to:', hold);
  socket.send(JSON.stringify({hold: hold}));
}

function setMaxSpeed(maxSpeed){
  console.log('Setting maxSpeed to:', maxSpeed);
  socket.send(JSON.stringify({max_speed: maxSpeed}));
}

function timeElapsed(deltaTime){
  const currTime = new Date().getTime();
  if(currTime >= lastTime + deltaTime){
    lastTime = currTime
    return true;
  } else {
    return false;
  }
}

function drawActuators() {
  svgContainer.innerHTML = ''; // Clear the SVG container
  actuators.forEach(actuator => {
    const svgElement = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    svgElement.setAttribute('cx', actuator.x * 100 * scale + canvasSize/2); // Adjust scaling and positioning as needed
    svgElement.setAttribute('cy', actuator.y * 100 * scale + canvasSize/2); // Adjust scaling and positioning as needed
    svgElement.setAttribute('r', getActuationSize(actuator.actuation) * scale); // Radius of the circle
    svgElement.setAttribute('fill', getPressureColor(actuator.actuation)); // Default color
    svgElement.dataset.pin = actuator.pin;
    svgContainer.appendChild(svgElement);
  });
}

function setCursor(x, y){
  if (!isSending && timeElapsed(delay)) {
    isSending = true;
    requestAnimationFrame(() => { 
      const rect = svgContainer.getBoundingClientRect();
      const relativeX = (x - rect.left) / rect.width;
      const relativeY = (y- rect.top) / rect.height;
      const position = { x: relativeX * 2 - 1, y: relativeY * 2 - 1 };
      if (Math.abs(position.x) < 1 && Math.abs(position.y) < 1) {
        position.x /= scale;
        position.y /= scale;
        socket.send(JSON.stringify(position));
        cursorPositionDiv.textContent = `Cursor Position: (${position.x.toFixed(2)}, ${position.y.toFixed(2)})`;
      }
      isSending = false;
    });
  }
}

function toggleMenu(){
  const menu = document.getElementById("settings-menu");
  menu.disabled = !menu.disabled;
}

socket.onopen = function() {
  console.log('Connected to the WebSocket server');
  cursorPositionDiv.textContent = `Connected!`;
  
  document.addEventListener('mousemove', function(event) {
    setCursor(event.clientX, event.clientY);
  });

  document.addEventListener('touchmove', function(event) {
    setCursor(event.touches[0].clientX, event.touches[0].clientY);
  });

  document.addEventListener("keydown", function(event){
    if(event.code == 'Space'){
      togglePause();
    }
    if(event.code == 'KeyR'){
      setRelease(true);
    }
  });

  document.addEventListener("keyup", function(event){
    if(event.code == 'KeyR'){
      setRelease(false);
    }
  });

};

socket.onmessage = function(event) {
  try {
    actuators = JSON.parse(event.data);
    //console.log('Received actuators:', actuators);
    drawActuators(actuators);
  } catch (error) {
    console.error('Error parsing JSON:', error);
  }
};

socket.onclose = function() {
  console.log('Disconnected from the WebSocket server');
};

socket.onerror = function(error) {
  console.error('WebSocket error:', error);
};
