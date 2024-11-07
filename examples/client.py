from time import sleep
from ulora_new import LoRa, ModemConfig, SPIConfig
import uasyncio as asyncio

# Lora Parameters
RFM95_RST = 27
RFM95_SPIBUS = SPIConfig.esp32_1
RFM95_CS = 32
RFM95_INT = 33
RF95_FREQ = 433.0
RF95_POW = 25
CLIENT_ADDRESS = 1000
SERVER_ADDRESS = 2000

# Callback function to handle received messages - NOT USED
async def on_recv(payload):
    print("========================================================")
    print(f"Received message: {payload.message.decode()}")
    print(f"From: {payload.header_from}, To: {payload.header_to}, ID: {payload.header_id}, Flags: {payload.header_flags}")
    print(f"RSSI: {payload.rssi}, SNR: {payload.snr}")

# Initialize radio with the async callback
lora = LoRa(RFM95_SPIBUS, RFM95_INT, SERVER_ADDRESS, RFM95_CS, 
            reset_pin=RFM95_RST, freq=RF95_FREQ, tx_power=RF95_POW, 
            acks=True)

# Set the callback function
lora.on_recv = on_recv
print("Lora Initialized.")

# Asynchronous function to continuously receive messages
async def receive_messages():
    while True:
        try:
            await lora.set_mode_rx()
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Error in receive_messages: {e}")
            await asyncio.sleep(1)

# Main function to run the event loop
async def main():
    print("Waiting for incoming messages...")
    receive_task = asyncio.create_task(receive_messages())
    
    try:
        while True:
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        receive_task.cancel()

# Run the main function
try:
    asyncio.run(main())
except Exception as e:
    print(f"Fatal error: {e}")
    lora.close()
