import logging
from types import *
import time
import threading
from pycarmaker import CarMaker, Quantity  # CarMaker Library
from kuksa_client.grpc import VSSClient, Datapoint  # Kuksa Library

print("\r++++++++++++++++++++++++++++++++++++\r")
print("Welcome to Demon 3 in Windows Server\r")
print("+++++++++++++++++++++++++++++++++++++\r")

# Global variables
digitalAuto_Hazard = False
digitalAuto_Brake = False
digitalAuto_Speed = 0
digitalAuto_UserRequest = 0
last_userinput = 0  # To track the previous state of user input
last_written_userinput = None
data_lock = threading.Lock()  # Lock for synchronization

# Flags for tracking the request process
request_activated = False  # Tracks if digitalAuto_UserRequest == 1 has been processed
request_deactivated = False  # Tracks if digitalAuto_UserRequest == 0 has been processed after 1

def thread_ControlCarMaker():
    global digitalAuto_Hazard
    global digitalAuto_Brake
    global digitalAuto_Speed
    global digitalAuto_UserRequest
    global last_userinput
    global last_written_userinput

    carMaker_IP = "localhost"
    carMaker_Port = 16660

    cm = CarMaker(carMaker_IP, carMaker_Port)
    cm.connect()

    vehspd = Quantity("Car.v", Quantity.FLOAT)
    brake = Quantity("DM.Brake", Quantity.FLOAT)
    userinput = Quantity("UserOut_01", Quantity.FLOAT)
    hazard = Quantity("DM.Lights.Hazard", Quantity.FLOAT)

    cm.subscribe(vehspd)
    cm.subscribe(brake)
    cm.subscribe(hazard)
    cm.subscribe(userinput)

    print(cm.send("::Cockpit::Close\r"))
    print(cm.send("::Cockpit::Popup\r"))
    print(cm.send("StartSim\r"))
    print(cm.send("WaitForStatus running\r"))

    while True:
        cm.read()

        # Update vehicle data
        digitalAuto_Speed = vehspd.data * 3.6
        print("Vehicle speed: " + str(digitalAuto_Speed) + "(km/h)")

        current_userinput = userinput.data
        print("user req"+str(current_userinput))
        digitalAuto_Hazard = hazard.data
        print("Vehicle Hazard: " + str(digitalAuto_Hazard))

        # Brake condition
        digitalAuto_Brake = brake.data != 0.0
        print("Vehicle Brake: " + str(digitalAuto_Brake))

        # Toggle mechanism for user input (userinput.data == 1)
        if current_userinput == 1 and last_userinput == 0:
            digitalAuto_UserRequest = 1 if digitalAuto_UserRequest == 0 else 0
            print("Vehicle Userinput: " + str(digitalAuto_UserRequest))

        if digitalAuto_UserRequest != last_written_userinput:
            with open('userinput.txt', 'w') as f:
                f.write(str(digitalAuto_UserRequest))
            last_written_userinput = digitalAuto_UserRequest

        last_userinput = current_userinput  # Update the last user input
        time.sleep(1)

def thread_ConnectToDigitalAuto():
    global digitalAuto_Hazard
    global digitalAuto_Brake
    global digitalAuto_Speed
    global digitalAuto_UserRequest
    global request_activated
    global request_deactivated

    carMaker_IP = "localhost"
    carMaker_Port = 16660
    cm = CarMaker(carMaker_IP, carMaker_Port)
    cm.connect()

    kuksaDataBroker_IP = '20.79.188.178'
    kuksaDataBroker_Port = 55555
    switch = Quantity("UserOut_02", Quantity.FLOAT)
    cm.subscribe(switch)

    print("Initial switch value: " + str(switch))

    with VSSClient(kuksaDataBroker_IP, kuksaDataBroker_Port) as client:
        while True:
            with data_lock:
                current_user_request = digitalAuto_UserRequest
                print("current userinput is " +str(digitalAuto_UserRequest))
            # Execute only once when digitalAuto_UserRequest becomes 1
            client.set_current_values({'Vehicle.Body.Horn.IsActive':Datapoint(False),})
            if current_user_request == 1 and not request_activated:
                print("Waiting for cockpit activation...")
                client.set_current_values({'Vehicle.Body.Hood.IsOpen':Datapoint(True),})
                print("Digital Vehicle User input: True")
                # Subscribe and wait for horn to become active
                for updates in client.subscribe_current_values(['Vehicle.Body.Horn.IsActive']):
                    horn_active = updates['Vehicle.Body.Horn.IsActive'].value

                    if horn_active:
                        cm.DVA_write(switch, str(1))  # Activate switch when horn becomes active
                        print("cockpit is active, executing DVA write (switch=1)")
                        request_activated = True  # Set the flag to mark request as processed
                        request_deactivated = False  # Reset the deactivation flag for the next cycle
                        break  # Exit the loop to continue the main flow

            # Execute only when digitalAuto_UserRequest becomes 0 **after** being 1
            elif current_user_request == 0 and request_activated and not request_deactivated:
                print("Waiting for cockpit deactivation...")
                client.set_current_values({'Vehicle.Body.Hood.IsOpen':Datapoint(False),})
                print("Digital Vehicle User input: False")
                # Subscribe and wait for horn to become inactive
                for updates in client.subscribe_current_values(['Vehicle.Body.Horn.IsActive']):
                    horn_inactive = not updates['Vehicle.Body.Horn.IsActive'].value

                    if horn_inactive:
                        cm.DVA_write(switch, str(0))  # Deactivate switch when horn becomes inactive
                        print("cockpit is inactive, executing DVA write (switch=0)")
                        request_deactivated = True  # Set the flag to mark deactivation as processed
                        request_activated = False  # Reset the activation flag for the next cycle
                        break  # Exit the loop to continue the main flow

            # Update vehicle speed and brake status to the Kuksa client
            client.set_current_values({'Vehicle.Speed': Datapoint(float(digitalAuto_Speed))})
            print("Digital Vehicle Speed: " + str(digitalAuto_Speed))

            if digitalAuto_Brake:
                client.set_current_values({'Vehicle.Body.Lights.Brake.IsDefect': Datapoint(True)})
                print("Digital Brake: True")
            else:
                client.set_current_values({'Vehicle.Body.Lights.Brake.IsDefect': Datapoint(False)})
                print("Digital Brake: False")

            if str(digitalAuto_Hazard) == '1.0':
                client.set_current_values({'Vehicle.Body.Lights.Hazard.IsSignaling': Datapoint(True)})
                print("Digital Hazard: True")
            else:
                client.set_current_values({'Vehicle.Body.Lights.Hazard.IsSignaling': Datapoint(False)})
                print("Digital Hazard: False")

            time.sleep(1)

if __name__ == '__main__':
    try:
        # Declare threads
        CarMakerThread = threading.Thread(target=thread_ControlCarMaker)
        DigitalAutoThread = threading.Thread(target=thread_ConnectToDigitalAuto)

        # Start threads
        CarMakerThread.start()
        DigitalAutoThread.start()

        # Wait for threads to finish
        CarMakerThread.join()
        DigitalAutoThread.join()

        print("+++++++++++++++++++++++++++\r")
        print("Demonstration is finished\r")
        print("+++++++++++++++++++++++++++\r\n")

    except Exception as e:
        print(f"Something went wrong: {e}")
