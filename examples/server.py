from time import sleep
from ulora_new import LoRa, ModemConfig, SPIConfig
from machine import Pin
import uasyncio as asyncio

# Initialize reset pin
#rst = Pin(5, Pin.OUT)
#rst.value(0)

# Lora Parameters
RFM95_RST = 27
RFM95_SPIBUS = SPIConfig.esp32_1
RFM95_CS = 15
RFM95_INT = 2
RF95_FREQ = 433.0
RF95_POW = 25
CLIENT_ADDRESS = 1000 # max 65K (2 Bytes)
SERVER_ADDRESS = 2000 # max 65K (2 Bytes)

# Create an event loop
loop = asyncio.get_event_loop()

# This is our callback function that runs when a message is received
async def on_recv(payload):
    print("From:", payload.header_from)
    print("Received:", payload.message)
    print("RSSI: {}; SNR: {}".format(payload.rssi, payload.snr))

# Initialize client radio
lora = LoRa(RFM95_SPIBUS, RFM95_INT, CLIENT_ADDRESS, RFM95_CS, 
            reset_pin=RFM95_RST, freq=RF95_FREQ, tx_power=RF95_POW, 
            acks=True)

# Set the callback
lora.on_recv = on_recv

# Asynchronous function to send a message
msg_counter = 0
async def send_message():
    global msg_counter
    try:
        message = f"Hello, LoRa Gateway! | Message Number: {msg_counter}"
        header_to = SERVER_ADDRESS
        print(f"Sending message {msg_counter}")
        
        # Set shorter timeouts for testing
        lora.retry_timeout = 1.0  # 1 second timeout
        lora.send_retries = 3     # 3 retries
        
        status = await lora.send_to_wait(message.encode(), header_to)
        
        if status:
            print(f"Message {msg_counter} sent successfully and ACK received")
            msg_counter += 1
        else:
            print(f"Message {msg_counter} failed after all retries")
    except Exception as e:
        print(f"Error sending message: {e}")

# Asynchronous function to handle receiving
async def receive_messages():
    while True:
        await lora.set_mode_rx()
        await asyncio.sleep(0.1)

# Main function to run the event loop
async def main():
    # Create the receiver task
    receiver_task = asyncio.create_task(receive_messages())
    
    try:
        while True:
            await send_message()
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        receiver_task.cancel()

# Run the main function
try:
    asyncio.run(main())
except Exception as e:
    print(f"Fatal error: {e}")
    # Cleanup
    lora.close()
