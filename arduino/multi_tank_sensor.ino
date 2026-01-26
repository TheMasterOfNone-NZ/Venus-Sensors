/*
 * Arduino Mega Multi-Tank Sensor
 * Supports up to 4 tanks on A0-A3
 * WITH 15-SECOND ROLLING AVERAGE
 * 
 * Detection:
 * - Grounded (< 0.1V) = Not in use (disabled)
 * - Any other voltage = Connected sensor
 */

// ===== CALIBRATION - CHANGE THESE FOR YOUR SENSORS =====
const float TANK_EMPTY_VOLTAGE[4] = {0.5, 0.5, 0.5, 0.5};   // Voltage when tank is EMPTY
const float TANK_FULL_VOLTAGE[4] = {4.5, 4.5, 4.5, 4.5};    // Voltage when tank is FULL
// ======================================================

const float GROUNDED_VOLTAGE = 0.1;      // Below this = grounded (not in use)

const int TANK_PINS[4] = {A0, A1, A2, A3};
const unsigned long OUTPUT_INTERVAL = 15000;
const unsigned long SAMPLE_INTERVAL = 100;
const int NUM_SAMPLES = 150;

unsigned long lastOutputTime = 0;
unsigned long lastSampleTime = 0;

int samples[4][NUM_SAMPLES];
int sampleIndex = 0;
bool bufferFilled = false;

void setup() {
  Serial.begin(115200);
  Serial3.begin(9600);
  
  delay(2000);
  
  for (int t = 0; t < 4; t++) {
    pinMode(TANK_PINS[t], INPUT);
    int initialReading = analogRead(TANK_PINS[t]);
    for (int i = 0; i < NUM_SAMPLES; i++) {
      samples[t][i] = initialReading;
    }
  }
  
  Serial.println("========================================");
  Serial.println("Multi-Tank Sensor");
  Serial.println("Ground input to disable tank");
  Serial.println("========================================");
}

void loop() {
  unsigned long currentTime = millis();
  
  // Sample all tanks every 100ms
  if (currentTime - lastSampleTime >= SAMPLE_INTERVAL) {
    lastSampleTime = currentTime;
    
    for (int t = 0; t < 4; t++) {
      samples[t][sampleIndex] = analogRead(TANK_PINS[t]);
    }
    
    sampleIndex++;
    if (sampleIndex >= NUM_SAMPLES) {
      sampleIndex = 0;
      bufferFilled = true;
    }
  }
  
  // Output averaged data every 15 seconds
  if (currentTime - lastOutputTime >= OUTPUT_INTERVAL) {
    lastOutputTime = currentTime;
    
    for (int t = 0; t < 4; t++) {
      int count = bufferFilled ? NUM_SAMPLES : sampleIndex;
      if (count == 0) count = 1;
      
      // Calculate average
      long sum = 0;
      for (int i = 0; i < count; i++) {
        sum += samples[t][i];
      }
      
      int avgReading = sum / count;
      float voltage = (avgReading / 1023.0) * 5.0;
      
      if (voltage < GROUNDED_VOLTAGE) {
        // Grounded - not in use
        Serial3.print("TANK");
        Serial3.print(t);
        Serial3.println(":OFF");
        
        Serial.print("Tank ");
        Serial.print(t);
        Serial.println(" [OFF]");
      }
      else {
        // Valid sensor
        float percentage = ((voltage - TANK_EMPTY_VOLTAGE[t]) / (TANK_FULL_VOLTAGE[t] - TANK_EMPTY_VOLTAGE[t])) * 100.0;
        if (percentage < 0) percentage = 0;
        if (percentage > 100) percentage = 100;
        
        int level = (int)percentage;
        
        Serial3.print("TANK");
        Serial3.print(t);
        Serial3.print(":");
        Serial3.println(level);
        
        Serial.print("Tank ");
        Serial.print(t);
        Serial.print(": ");
        Serial.print(level);
        Serial.print("% | V: ");
        Serial.println(voltage, 2);
      }
    }
    Serial.println("---");
  }
}
