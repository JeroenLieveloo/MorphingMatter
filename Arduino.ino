#include <Wire.h>
#include <Servo.h>

const int NUM_SERVOS = 6;           // You can increase as needed
Servo servos[NUM_SERVOS];
int servoPins[NUM_SERVOS] = {3, 5, 6, 9, 10, 11};  // Physical pin numbers
byte address = 0x08;

void setup() {
  Wire.begin(address);  // Start I²C as slave at address 0x08
  Wire.onReceive(receiveData);

  for (int i = 0; i < NUM_SERVOS; i++) {
    servos[i].attach(servoPins[i]);
    servos[i].write(90);  // Set to neutral position
  }
}

void loop() {
  // Nothing to do here — all handled in receiveData()
}

void receiveData(int byteCount) {
  while (Wire.available() >= 2) {
    byte servoIndex = Wire.read();     // First byte = which servo
    byte actuation = Wire.read();      // Second byte = 0–255

    if (servoIndex < NUM_SERVOS) {
      int angle = map(actuation, 0, 255, 0, 180);  // Scale value
      servos[servoIndex].write(angle);
    }
  }
}
