#include <Wire.h>
#include <Servo.h>

#define NUM_ACTUATORS 4 // Change to your number of actuators
const int actuatorPins[NUM_ACTUATORS] = {3, 5, 6, 9}; // Example pins

Servo actuators[NUM_ACTUATORS];
uint8_t actuatorValues[NUM_ACTUATORS]; // Values received from I2C (0-255)

void setup() {
  Wire.begin(0x08); // Set I2C address to match your Python code
  Wire.onReceive(receiveData);
  for (int i = 0; i < NUM_ACTUATORS; i++) {
    actuators[i].attach(actuatorPins[i]);
    actuators[i].write(0); // Initialize to 0 degrees
  }
}

void loop() {
  // Nothing needed here, everything handled in receiveData
}

void receiveData(int byteCount) {
  int i = 0;
  while (Wire.available() && i < NUM_ACTUATORS) {
    actuatorValues[i] = Wire.read(); // Read value (0-255)
    int angle = map(actuatorValues[i], 0, 255, 0, 90); // Map to 0..90 degrees
    actuators[i].write(angle);
    i++;
  }
}