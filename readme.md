# CarMaker and Kuksa Client Integration

This project demonstrates how to integrate a CarMaker simulation with the Kuksa Data Broker to manage and monitor the status of a car simulation environment through an SSI (Self-Sovereign Identity) verification process. The demonstration specifically utilizes the G29 steering wheel setup, connected directly to the host PC where CarMaker is running, to allow control handover after SSI verification. Once verified, the cockpit interface is activated, and the user can take control of the vehicle in the simulation environment.

---

## Project Structure

- **`thread_ControlCarMaker`**: This thread handles the CarMaker connection and continuously reads vehicle data (e.g., speed, brake, and hazard light status) and user input through the G29 interface. The thread toggles user requests based on G29 input data, updating the `digitalAuto_UserRequest` variable, which initiates or halts the request process based on the previous state.

- **`thread_ConnectToDigitalAuto`**: This thread manages communication with the Kuksa Data Broker. It monitors the `digitalAuto_UserRequest` variable and triggers an SSI verification process when the user requests control. Once verified, it enables cockpit control. The cockpit is deactivated if the user later relinquishes control.

## Prerequisites

- **CarMaker Installation**: Ensure that CarMaker and the necessary libraries are installed and configured. You should also have access to the CarMaker API for Python.
- **Kuksa Client Library**: Install the Kuksa gRPC library (`kuksa-client`) to facilitate interaction with the Kuksa Data Broker.
- **Hardware**: The G29 steering wheel setup must be connected directly to the PC hosting CarMaker.

## Installation

1. **Install Dependencies**:
   Ensure that both CarMaker and Kuksa Data Broker Python libraries are installed:
   ```bash
   pip install pycarmaker
   pip install kuksa-client

Run the Script: Execute the main script using Python. Ensure that CarMaker and Kuksa Data Broker are configured to accept the connections:

python test.py

### Configuration

CarMaker Configuration: CarMaker IP and port are set as localhost and 16660, respectively.
Kuksa Data Broker Configuration: Kuksa Data Broker IP and port are set to 20.79.188.178 and 55555.
Global Variables: Key variables are defined to track vehicle states, control requests, and synchronization between threads:
digitalAuto_Hazard, digitalAuto_Brake, and digitalAuto_Speed monitor hazard, brake, and speed data from CarMaker.
digitalAuto_UserRequest is toggled by user input from the G29 steering wheel and initiates the request cycle.
request_activated and request_deactivated are flags to ensure requests are processed once per cycle.

### Key Process Flow
Reading Vehicle Data: The CarMaker thread continuously reads speed, brake, and hazard data. The digitalAuto_UserRequest variable is toggled based on user input, enabling or disabling cockpit control.

SSI Verification: Upon user request (digitalAuto_UserRequest == 1), the thread_ConnectToDigitalAuto initiates an SSI verification with the Kuksa Data Broker. Only after verification does cockpit control activate.

Control Handover: When verification completes, the cockpit becomes active, allowing the user to control the simulated car. If the user deactivates control, the cockpit disables, returning control to the original state.

### Usage Notes
Logs: The script outputs real-time status messages to track the request, verification, and control processes.
Thread Synchronization: A lock (data_lock) is used for synchronization to ensure data consistency across threads.
Error Handling
In the event of an error, the script will print the error details, allowing for quick troubleshooting and debugging.

Example Output
Upon running the script, you’ll see messages indicating the current status of vehicle data, request processing, verification status, and cockpit control state.

Known Issues
Ensure that the CarMaker and Kuksa Data Broker configurations are correct, as connection failures will prevent the script from executing as intended.
G29 setup issues may require reconfiguration on the host PC.

