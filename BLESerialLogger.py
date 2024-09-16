import struct
import csv
import time
from bleak import BleakClient, BleakScanner
import asyncio
import nest_asyncio

nest_asyncio.apply()

CHARACTERISTIC_DATAB_UUID = "31410000-0011-2358-c000-0000beef0001"
CHARACTERISTIC_DATAC_UUID = "31410000-0011-2358-C000-0000beef0002"
CHARACTERISTIC_DATAD_UUID = "31410000-0011-2358-C000-0000beef0003"
CHARACTERISTIC_DATAA_UUID = "31410000-0011-2358-C000-0000beef1001"

# To store parsed data
dataA_list = []
dataB_list = []
dataC_list = []
dataD_list = []
time_list = []

sampling_frequency = 100  # 25 Hz * 4 channels
time_interval = 1 / sampling_frequency
sample_count = 0
save_interval = 10  # Save data every 10 seconds

def parse_packet(packet):
    """
    Parse the packet and extract 20-bit data from BLE notification.
    """
    # Handle signed 20-bit values (2's complement)
    if len(packet) == 3:
        # Combine the 3 bytes into a 24-bit unsigned integer
        data = (packet[0] << 16) | (packet[1] << 8) | packet[2]
        # print(f"Data: {data}")
        return data
    return None

def save_data():
    """
    Save data to a CSV file when the button is clicked.
    """
    with open('ble_data_output.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Data A', 'Data B', 'Data C', 'Data D'])
        for i in range(len(dataA_list)):
            writer.writerow([dataA_list[i], dataB_list[i], dataC_list[i], dataD_list[i]])
    print("Data saved to ble_data_output.csv")

async def fetch_characteristics(client):
    """
    Fetch data from characteristics and update the lists.
    """
    global sample_count

    # Read data from each characteristic
    dataA = await client.read_gatt_char(CHARACTERISTIC_DATAA_UUID)
    dataB = await client.read_gatt_char(CHARACTERISTIC_DATAB_UUID)
    dataC = await client.read_gatt_char(CHARACTERISTIC_DATAC_UUID)
    dataD = await client.read_gatt_char(CHARACTERISTIC_DATAD_UUID)

    # Parse the data
    parsed_dataA = parse_packet(dataA)
    parsed_dataB = parse_packet(dataB)
    parsed_dataC = parse_packet(dataC)
    parsed_dataD = parse_packet(dataD)

    if parsed_dataA is not None and parsed_dataB is not None and parsed_dataC is not None and parsed_dataD is not None:
        dataA_list.append(parsed_dataA)
        dataB_list.append(parsed_dataB)
        dataC_list.append(parsed_dataC)
        dataD_list.append(parsed_dataD)

async def main():
    """
    Main function to scan and connect to the BLE device, and start receiving notifications.
    """
    target_name = "EvansSpO2"  # Device name to search for

    print("Scanning for BLE devices...")
    devices = await BleakScanner.discover()
    
    for device in devices:
        print(f"Found device: {device.name} ({device.address})")
        if device.name == target_name:
            target_device = device
            break
        
    if target_device is None:
        print(f"Device with name {target_name} not found.")
        return 
       
 
    async with BleakClient(target_device.address, timeout=10.0, connection_interval=0.01) as client:
        print(f"Connected to {device.name}")
        
        # Discover services and characteristics
        services = await client.get_services()
        characteristics = {}
        for service in services:
            for char in service.characteristics:
                characteristics[char.uuid] = char
                # Check if the characteristics are available
                
        # Print discovered services and characteristics
        print("Discovered characteristics:")
        for uuid, char in characteristics.items():
            print(f"Characteristic UUID: {uuid}, Handle: {char.handle}")
            
        dataA_char = CHARACTERISTIC_DATAA_UUID
        dataB_char = CHARACTERISTIC_DATAB_UUID
        dataC_char = CHARACTERISTIC_DATAC_UUID
        dataD_char = CHARACTERISTIC_DATAD_UUID
        
        if not all([dataA_char, dataB_char, dataC_char, dataD_char]):
            print("One or more required characteristics not found.")
            return
        
        # Fetch and update data periodically
        last_save_time = time.time()
        last_fetch_time = time.time()
        while True:
            current_fetch_time = time.time()
            fetch_period = current_fetch_time - last_fetch_time
            print(f"P: {fetch_period:.3f} s")

            await fetch_characteristics(client)
            current_time = time.time()
            if current_time - last_save_time > save_interval:
                save_data()
                last_save_time = current_time

            last_fetch_time = current_fetch_time
            await asyncio.sleep(time_interval)  # Wait for the next sample

# Run the main function
asyncio.run(main())
