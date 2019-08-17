// pro mini
//#define controllerIn 12
//#define piIn 11
//#define select 2
//#define LED 13

// pro micro
#define controllerIn 14
#define piIn 16
#define select 2
#define LED 17   
#define start A0        

unsigned long duration;
unsigned long gap;
unsigned long buffer[8];
int index = 0;
void setup() {
  pinMode(controllerIn, INPUT_PULLUP);
  pinMode(piIn, INPUT_PULLUP);
  pinMode(select, OUTPUT);
  pinMode(LED, OUTPUT);
  pinMode(start, OUTPUT);
//  Serial.begin(19200);
//  Serial.println("siu");
  gap = pulseIn(controllerIn, LOW);
//  Serial.println(gap);
  delay(1000);
}

void loop() {
  duration = pulseIn(controllerIn, HIGH);
  buffer[index] = duration+gap;
  index++;
  if (duration > 3000){
    index = 0;
  }
  if (index>=8){
    index = 0;
//    Serial.print(buffer[0]);
//    Serial.print(",\t");
//    Serial.print(buffer[1]);
//    Serial.print(",\t");
//    Serial.print(buffer[2]);
//    Serial.print(",\t");
//    Serial.print(buffer[3]);
//    Serial.print(",\t");
//    Serial.print(buffer[4]);
//    Serial.print(",\t");
//    Serial.print(buffer[5]);
//    Serial.print(",\t");
//    Serial.print(buffer[6]);
//    Serial.print(",\t");
//    Serial.print(buffer[7]);
//    Serial.println(",\t");
    if (buffer[5]>1500){
      digitalWrite(select, 1);
      digitalWrite(LED, 1);
      digitalWrite(start, 1);
    }else{
      digitalWrite(select, 0);
      digitalWrite(LED, 0);
      digitalWrite(start, 0);
    }
  }
  // put your main code here, to run repeatedly:

}
