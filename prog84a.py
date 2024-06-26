from machine import Pin
from time import sleep, sleep_ms, sleep_us, ticks_ms


##############################
HEX_FILE = "main.hex"       # name of hex file in filesystem
CODE_START_ADDR = 0         # code region goes from 0x000 to 0x3ff
CODE_END_ADDR = 0x3ff       # code region goes from 0x000 to 0x3ff
CONFIG_START_ADDR = 0x2000  # config region goes from 0x2000 to 0x2007
CONFIG_END_ADDR = 0x2007    # config region goes from 0x2000 to 0x2007

PGD_PIN = 10                # Programming pin: PGD
PGC_PIN = 11                # Programming pin: PGC
VPP_PIN = 12                # Programming pin enable: VPP

# ICSP commands:
# http://ww1.microchip.com/downloads/en/devicedoc/39588a.pdf
CMD_LOAD_CONFIG = 0
CMD_LOAD_DATA = 2
CMD_READ_DATA = 4
CMD_INC_ADDR = 6
CMD_BEGIN_PROG = 8
CMD_BULK_ERASE = 9
##############################

PGD = Pin(PGD_PIN, Pin.OUT)
PGC = Pin(PGC_PIN, Pin.OUT)
VPP = Pin(VPP_PIN, Pin.OUT)

# 100ns required
# 13 cycles @ 125MHz = 104ns
@micropython.asm_thumb
def tsethold():
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()
    nop()


def enter_prog():
    PGD.value(0)
    PGC.value(0)
    VPP.value(0)
    sleep_ms(100)
    VPP.value(1)
    sleep_ms(10)


def command(x):
    # Send 6 bit command, LSB first:
    # Target latches bit at falling edge of PGC
    x = x & 0x3f
    for _ in range(6):
        b = x & 1
        x = x >> 1

        # Shift out b:
        PGC.value(1)
        PGD.value(b)
        # tset1:
        tsethold()
        PGC.value(0)
        # thold1:
        tsethold()
    
    # tdly1:
    sleep_us(1)


def write_data(x):
    # Write 16 bits of data, LSB first:
    # This is 0, then 14 bits of data, then 0
    # Target latches bit at falling edge of PGC
    x = (x & 0x3fff) << 1
    for i in range(16):
        b = x & 1
        x = x >> 1
        
        # Shift out b:
        PGC.value(1)
        PGD.value(b)
        # tset1:
        tsethold()
        PGC.value(0)
        # thold1:
        tsethold()
        

def read_data():
    # Read 16 bits of data, LSB first:
    # This is 0, then 14 bits of data, then 0
    # Target sets bit at rising edge of PGC
    x = 0
    PGD.init(PGD.IN, Pin.PULL_DOWN)
    for _ in range(16):
        PGC.value(1)
        # tset1:
        tsethold()
        PGC.value(0)
        b = PGD.value()
        # thold1:
        tsethold()

        # Shift in b:
        x = x >> 1 | (b << 15)
    PGD.init(PGD.OUT)
    return x >> 1
##############################
def bulk_erase():
    enter_prog()  # Reset PC
    command(CMD_LOAD_DATA)
    write_data(0x3fff)
    command(CMD_BULK_ERASE)
    command(CMD_BEGIN_PROG)
    sleep_ms(10)

def blank_check():
    enter_prog()  # Reset PC
    for addr in range(CODE_START_ADDR, CODE_END_ADDR+1):
        command(CMD_READ_DATA)
        d = read_data()
        if d != 0x3fff:
            print(f"{d:04x} @ {addr:04x}")
            return False
        command(CMD_INC_ADDR)
    return True

def program():
    enter_prog()  # Reset PC
    current_word_addr = CODE_START_ADDR
    current_config_addr = 0
    with open(HEX_FILE) as f:
        line = f.readline() # Read in hex file line by line
        while line:
            line = line.strip()
            startchar = line[0]
            if startchar != start_code:
                return False
#                 raise Exception("Start code is not valid!")

            num_bytes = int(line[1:3], 16)
            num_words = int(num_bytes / 2)
            if num_words * 2 != num_bytes:
                return False
#                 raise Exception("Data not on a 2-byte boundary!")

            start_byte_h = int(line[3:5], 16)
            start_byte_l = int(line[5:7], 16)
            start_word_addr = int(((start_byte_h * 256) + start_byte_l)/2)

            data_type = int(line[7:9], 16)
            if data_type not in allowed_data_types:
                return False
#                 raise Exception(f"Data type {data_type} not supported!")

            idx = 9
            data_byte_sum = 0
            for i in range(num_words):
                data_byte_sum += int(line[idx+2:idx+4], 16) + int(line[idx:idx+2], 16)
                data_16_chr = line[idx+2:idx+4] + line[idx:idx+2]
                data_16 = int(data_16_chr, 16)
                idx += 4

                addr = start_word_addr + i
                if addr >= CODE_START_ADDR and addr <= CODE_END_ADDR:
                    # Code space
                    num_increments = addr - current_word_addr
                    if num_increments < 0:
                        return False
#                         raise Exception("Memory map is not monotonically increasing!")
                    if num_increments > 0:
                        # Skip ahead to the right code location:
                        for _ in range(num_increments):
                            command(CMD_INC_ADDR)
                            current_word_addr += 1
#                         print(f"Write 0x{data_16:04x} @ 0x{current_word_addr:04x}")

                    # Program one word:
                    command(CMD_LOAD_DATA)
                    write_data(data_16)
                    command(CMD_BEGIN_PROG)
                    sleep_ms(8)
                    command(CMD_INC_ADDR)
                    current_word_addr += 1
                elif addr >= CONFIG_START_ADDR and addr <= CONFIG_END_ADDR:
                    # Config space
                    if current_config_addr == 0:
                        # If first time writing a config word, set PC to config space:
                        command(CMD_LOAD_CONFIG)
                        write_data(0)  # required dummy write
                        current_config_addr = CONFIG_START_ADDR

                    num_increments = addr - current_config_addr
                    if num_increments < 0:
                        return False
#                         raise Exception("Config map is not monotonically increasing!")
                    if num_increments > 0:
                        # Skip ahead to the right config location:
                        for _ in range(num_increments):
                            command(CMD_INC_ADDR)
                            current_config_addr += 1
#                         print(f"Write 0x{data_16:04x} @ 0x{current_config_addr:04x}")

                    # Program one word:
                    command(CMD_LOAD_DATA)
                    write_data(data_16)
                    command(CMD_BEGIN_PROG)
                    sleep_ms(8)
                    command(CMD_INC_ADDR)
                    current_config_addr += 1
                else:
                    return False
#                     raise Exception(f"Addr {addr} beyond code and config spaces!")

            # Compute checksum.
            # Backwards since exception is raised after programming, but it's fine for here.
            checksum = int(line[idx:idx+2], 16)
            checksum_computed = num_bytes + start_byte_h + start_byte_l + data_type + data_byte_sum
            checksum_computed = 256 - (checksum_computed % 256)

            if checksum != checksum_computed:
                return False
#                 raise Exception(f"Checksum {checksum} does not match computed: {checksum_computed}")

            # Read next line:
            line = f.readline()
    return True
############################################################

PGD.value(0)
PGC.value(0)
VPP.value(0)
print(f"Hex file to flash: {HEX_FILE}")

found = True

start_code = ':'
allowed_data_types = [0, 1]  # data, EOF
if found:
    # Steps:
    # 1. Bulk erase part and wait at least 30ms
    # 2. Read all code words and ensure chip is blank
    # 3. Write flash words and program
    # 4. Done - no verification done here

    print(f"[3] Bulk erase ... ", end='')
    t0 = ticks_ms()
    
    # Step 1:
    bulk_erase()
    
    # Step 2:
    blank = blank_check()
    tblank = (ticks_ms() - t0)/1000
    status = "completed" if blank else "failed"
    print(f"{status} in {tblank:.2f}s")

    # Step 3:
    if blank:
        print(f"[4] Programming ... ", end='')
        t0 = ticks_ms()
        p = program()
        tprog = (ticks_ms() - t0)/1000
        status = "completed" if p else "failed"
        print(f"{status} in {tprog:.2f} seconds")

VPP.value(0)
PGD.value(0)
PGC.value(0)

# Step 4:
print(f"Done")
