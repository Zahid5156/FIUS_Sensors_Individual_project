# src/hardware/sensor.py
# RedPitaya Sensor Interface

import time
import socket
import struct
import numpy as np
import paramiko
from threading import Thread

from config.settings import (
    REDPITAYA_HOST_IP,
    REDPITAYA_DATA_PORT,
    REDPITAYA_SSH_PORT,
    SIZE_OF_RAW_ADC,
    LED7_ON_COMMAND,
    LED7_OFF_COMMAND
)


class RedPitayaSensor:
    """RedPitaya sensor interface with corrected distance calculation and LED control"""
    
    def __init__(self):
        self.size_of_raw_adc = SIZE_OF_RAW_ADC
        self.buffer_size = (self.size_of_raw_adc + 17) * 4
        self.msg_from_client = "-i 1"
        self.hostIP = REDPITAYA_HOST_IP
        self.data_port = REDPITAYA_DATA_PORT
        self.ssh_port = REDPITAYA_SSH_PORT
        self.server_address_port = (self.hostIP, self.data_port)
        
        self.sensor_status_message = "Waiting to Connect with RedPitaya UDP Server!"
        print(self.sensor_status_message)
        
        self.udp_client_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        self.header_length = None
        self.total_data_blocks = None
        self.local_time_sync = None
        self.first_synced_time = None
        
    def give_ssh_command(self, command):
        """Execute SSH command on RedPitaya"""
        try:
            self.client.connect(self.hostIP, self.ssh_port, "root", "root")
            self.set_sensor_message(f"Connected to Redpitaya {self.hostIP}")
            
            stdin, stdout, stderr = self.client.exec_command(command)
            
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            self.set_sensor_message(f"Output: {output}")
            
            if error:
                self.set_sensor_message(f"Error: {error}")
                
            if output:
                return output
                
        finally:
            self.client.close()
            self.set_sensor_message("Connection closed")
    
    def _control_led7_async(self, turn_on):
        """Internal async LED control (runs in background thread)"""
        try:
            command = LED7_ON_COMMAND if turn_on else LED7_OFF_COMMAND
            self.give_ssh_command(command)
            status = "ON" if turn_on else "OFF"
            print(f"LED7 turned {status}")
        except Exception as e:
            print(f"Failed to control LED7: {e}")
    
    def control_led7(self, turn_on=True):
        """Control LED7 on RedPitaya - NON-BLOCKING (runs in background)"""
        # Run LED control in separate thread to avoid SSH delays
        thread = Thread(target=self._control_led7_async, args=(turn_on,), daemon=True)
        thread.start()
        return True
        
    def set_sensor_message(self, message):
        self.sensor_status_message = message
        
    def get_sensor_status_message(self):
        return self.sensor_status_message

    def send_msg_to_server(self):
        """Send message to UDP server"""
        bytes_to_send = str.encode(self.msg_from_client)
        self.udp_client_socket.sendto(bytes_to_send, self.server_address_port)
        
    def get_data_info_from_server(self):
        """Get initial data info from server"""
        self.msg_from_client = "-i 1"
        self.send_msg_to_server()
        packet = self.udp_client_socket.recv(self.buffer_size)
        self.sensor_status_message = f"Sensor Connected Successfully at {self.server_address_port}!"
        print(self.sensor_status_message)
        print(f"Total Received: {len(packet)} Bytes.")
        
        self.header_length = int(struct.unpack('@f', packet[:4])[0])
        self.total_data_blocks = int(struct.unpack('@f', packet[56:60])[0])
        synced_time = int(struct.unpack('@f', packet[20:24])[0])
        
        header_data = []
        for i in struct.iter_unpack('@f', packet[:self.header_length]):
            header_data.append(i[0])
        
        print(f"Length of Header: {len(header_data)}")
        
        self.local_time_sync = time.time() * 1000
        self.first_synced_time = synced_time
        
        return synced_time, header_data
 
    def get_data_from_server(self, start_time):
        """Get complete signal data from server with corrected distance calculation - OPTIMIZED"""
        ultrasonic_data = []
        header = None
        dmax_raw = None
        distance_cm = None
        
        for i in range(self.total_data_blocks):
            # REMOVED: time.sleep(1/1000) - unnecessary delay
            self.msg_from_client = "-a 1"
            self.send_msg_to_server()
            
            packet1 = self.udp_client_socket.recv(self.buffer_size)
            
            if i == 0:
                # Parse header only once (first block)
                header = list(struct.unpack(f'{self.header_length//4}f', packet1[:self.header_length]))
                
                # Extract dmax from header (bytes 40:44)
                dmax_raw = struct.unpack('@f', packet1[40:44])[0]
                
                # Distance correction: If dmax < 10, it's in meters; convert to cm
                if dmax_raw < 10:
                    distance_cm = int(dmax_raw * 100)
                else:
                    distance_cm = int(dmax_raw)
                
            current_data_block_number = int(struct.unpack('@f', packet1[60:64])[0])
            
            if i != current_data_block_number:
                print(f"Error: Expected block{i} but recieved block{current_data_block_number}")
                break
            
            # OPTIMIZED: Direct numpy conversion from bytes (much faster than list append)
            data_bytes = packet1[self.header_length:]
            block_data = np.frombuffer(data_bytes, dtype=np.int16)
            ultrasonic_data.append(block_data)
        
        if not ultrasonic_data or sum(len(block) for block in ultrasonic_data) != self.size_of_raw_adc * self.total_data_blocks:
            return None, None, None
        
        # OPTIMIZED: Direct numpy concatenation instead of pandas (10-100x faster)
        raw_array = np.concatenate(ultrasonic_data)
        header_array = np.array(header) if header else None
        
        return header_array, raw_array, distance_cm
