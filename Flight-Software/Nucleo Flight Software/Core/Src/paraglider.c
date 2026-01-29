#include "paraglider.h"
#include "servos.h"

void control_paraglider(Telemetry_t *telemetry){
    // Find angle we are off
    telemetry->target_latitude;
    telemetry->target_longitude;

    telemetry->heading;


    // Turn servos based on angle difference
    Set_Left_Servo_Angle(90);
    Set_Right_Servo_Angle(90);
}
