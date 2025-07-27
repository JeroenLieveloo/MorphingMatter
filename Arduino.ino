#include <Wire.h>
#include <Servo.h>

const int NUM_SERVOS = 6;           // You can increase as needed
Servo servos[NUM_SERVOS];
int servoPins[NUM_SERVOS] = {3, 5, 6, 9, 10, 11};  // Physical pin numbers
byte address = 8;
int currMessageLength = 0;

void setup() {
  Serial.begin(9600);
  Wire.begin(address);
  Wire.onReceive(receiveEvent);
  pinMode(LED_BUILTIN, OUTPUT);

  for (int i = 0; i < NUM_SERVOS; i++) {
    servos[i].attach(servoPins[i]);
    servos[i].write(90);  // Set to neutral position
  }
}

void loop() {
  //   // turn the LED on (HIGH is the voltage level)
  //delay(1000);                       // wait for a second
  digitalWrite(LED_BUILTIN, LOW);    // turn the LED off by making the voltage LOW
  //delay(1000);                       // wait for a second
}

/*
  if (currMessageLength = 0){
    if (count > 2){
    desregard command
    set length
    }
  } else if(currMessageLength <= count){
  process message
  }
  */
void receiveEvent(int count) {
  digitalWrite(LED_BUILTIN, HIGH);
  
  Serial.print("Incoming byte count: ");
  Serial.println(count);
  
  if (count < 3 || (count - 1) % 2 != 0) {
    Serial.println("Invalid byte count. Ignoring.");
    return;
  }

  Wire.read();  // Discard command byte

  while (Wire.available() >= 2) {
    byte servoIndex = Wire.read();
    byte actuation = Wire.read();

    Serial.print("Servo ");
    Serial.print(servoIndex);
    Serial.print(" -> ");
    Serial.println(actuation);

    if (servoIndex < NUM_SERVOS) {
      int angle = map(actuation, 0, 255, 0, 180);
      servos[servoIndex].write(angle);
    }
  }
}

