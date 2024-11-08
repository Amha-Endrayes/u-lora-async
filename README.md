# u-lora-async

This is work is based on the raspi-lora port by [martynwheeler](https://github.com/martynwheeler/u-lora) and adds asyncio support for the library.
It has been tested on ESP32 with MicroPython v1.23

## Wiring

The pinout for the RFM95 module can be found on page 10 of the documentation (https://cdn.sparkfun.com/assets/learn_tutorials/8/0/4/RFM95_96_97_98W.pdf).  The pin numbers below are for the RFM95 - look at your microcontroller docs for the pins to connect to them.

Power (the RFM95 module requires 3.3V from your microcontroller):  
+ connect 3.3V to pin 13  
+ connect GND to pin 1, 8, or 10 on the RFM95 module

For SPI communication:  
+ MISO to pin 2 (MISO)  
+ MOSI to pin 3 (MOSI)  
+ SCK to pin 4 (SCK)  
+ CS to pin 5 (NSS)  
    
Other pins:  
+ Use a GPIO output to pin 6 (RESET) for resetting the RFM95  
+ Use a GPIO input to pin 14 (D) to trigger that a message has been received  

## Configuration
**INITIALIZATION**
```
LoRa(spi_channel, interrupt, this_address, cs_pin, reset_pin=None, freq=868, tx_power=14,
    modem_config=ModemConfig.Bw125Cr45Sf128, acks=True, crypto=None)
```

  **`spi_channel`**: SPI channel, check SPIConfig for preconfigured names, e.g. SPIConfig.rp2_0 for RPi pico channel 0   
    **`interrupt`**: GPIO pin to use for the interrupt  
 **`this_address`**: The address number (0-65025) your device will use when sending and receiving packets.  
       **`cs_pin`**: chip select pin from microcontroller  
   **`reset_pin`** : the GPIO used to reset the RFM9x if connected  
         **`freq`**: Frequency used by your LoRa radio. Defaults to 868Mhz  
     **`tx_power`**: Transmission power level from 5 to 23. Keep this as low as possible. Defaults to 14  
 **`modem_config`**: Modem configuration. See RadioHead docs. Default to Bw125Cr45Sf128.  
  **`receive_all`**: Receive messages regardless of the destination address  
         **`acks`**: If True, send an acknowledgment packet when a message is received and wait for an acknowledgment when transmitting a message. This is equivalent to using RadioHead's RHReliableDatagram  
       **`crypto`**: An instance of PyCryptodome Cipher.AES (not tested) - should be able to use ucrypto

### SPICONFIG
Preconfigured SPI bus pins for tested devices, just add into the class for other devices
```
class SPIConfig():
    # spi pin defs for various boards (channel, sck, mosi, miso)
    rp2_0 = (0, 6, 7, 4)
    rp2_1 = (1, 10, 11, 8)
    esp8286_1 = (1, 14, 13, 12)
    esp32_1 = (1, 14, 13, 12)
    esp32_2 = (2, 18, 23, 19)
```

### ModemConfig
Preconfigured modem settings taken from Radiohead docs, I will try and add the ability to fine tune these in future.
```
    Bw125Cr45Sf128 = (0x72, 0x74, 0x04) #< Bw = 125 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on. Default medium range
    Bw500Cr45Sf128 = (0x92, 0x74, 0x04) #< Bw = 500 kHz, Cr = 4/5, Sf = 128chips/symbol, CRC on. Fast+short range
    Bw31_25Cr48Sf512 = (0x48, 0x94, 0x04) #< Bw = 31.25 kHz, Cr = 4/8, Sf = 512chips/symbol, CRC on. Slow+long range
    Bw125Cr48Sf4096 = (0x78, 0xc4, 0x0c) #/< Bw = 125 kHz, Cr = 4/8, Sf = 4096chips/symbol, low data rate, CRC on. Slow+long range
    Bw125Cr45Sf2048 = (0x72, 0xb4, 0x04) #< Bw = 125 kHz, Cr = 4/5, Sf = 2048chips/symbol, CRC on. Slow+long range
```

## Examples
There are two examples to test sending and receiving data in the examples folder

### Server mode:

Copy the file server.py to your main.py and copy it across together with the library ulora.py to your microcontroller
```
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
SERVER_ADDRESS = 2000 # << This Device. MAX: 65K (2 Bytes)

# Callback function to handle received messages
async def on_recv(payload):
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
```



### Client mode:
Copy the file server.py to your main.py and copy it across together with the library ulora.py to your microcontroller

```
from time import sleep
from ulora import LoRa, ModemConfig, SPIConfig
from machine import Pin
import uasyncio as asyncio

# Lora Parameters
RFM95_RST = 27
RFM95_SPIBUS = SPIConfig.esp32_1
RFM95_CS = 15
RFM95_INT = 2
RF95_FREQ = 433.0
RF95_POW = 25
CLIENT_ADDRESS = 1000 # << This Device. MAX: 65K (2 Bytes)
SERVER_ADDRESS = 2000

# Create an event loop
loop = asyncio.get_event_loop()

# Initialize client radio
lora = LoRa(RFM95_SPIBUS, RFM95_INT, CLIENT_ADDRESS, RFM95_CS, 
            reset_pin=RFM95_RST, freq=RF95_FREQ, tx_power=RF95_POW, 
            acks=True)

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
```
