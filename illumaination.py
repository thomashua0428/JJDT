
import serial
import time

ILLUMINATION_PROMPT = "### ILLUMINATION info ###  \n"

def serial_init(port,baudrate=115200):
    try:
        ser = serial.Serial(port, 115200, timeout=1)
        if ser.is_open:
            print(ILLUMINATION_PROMPT + f"Serial port {port} opened successfully.")
            return ser
        else:
            print(ILLUMINATION_PROMPT + f"Failed to open serial port {port}.")
            return None
    except serial.SerialException as e:
        print(ILLUMINATION_PROMPT + f"Error opening serial port {port}: {e}")
        return None

serial_port = 'COM3'  # Replace with your serial port
ser = serial_init(serial_port)


def clear():
    if ser is None:
        print(ILLUMINATION_PROMPT + "Serial port is not initialized.")
        return
    else:
        tmp = "clear"
        ser.write(tmp.encode())

def show():
    if ser is None:
        print(ILLUMINATION_PROMPT + "Serial port is not initialized.")
        return
    else:
        tmp = "show"
        ser.write(tmp.encode())

def wait():
    time.sleep(0.4)

def illumination_at(x,y):

    if ser is None:
        print(ILLUMINATION_PROMPT + "Serial port is not initialized.")
        return
    else:
        x = int(x)
        y = int(y)
        if x <= 24 and y <= 24 and x >= 0 and y >= 0:

            # turn x and y into a single value
            value = x * 100 + y
            tmp = str(value).zfill(4)  # Ensure the value is 4 digits long, padded with zeros if necessary        
            # 发送单个字节
            ser.write(("lit"+tmp).encode())
            print(ILLUMINATION_PROMPT+f"Sent: {tmp}   ","x:", x, "y:", y)



def illumination_at_x(x):

    if ser is None:
        print(ILLUMINATION_PROMPT + "Serial port is not initialized.")
        return
    else:
        x = int(x)

        if x <= 252 and x >= 0:

            # turn x and y into a single value
            value = x 
            tmp = str(value).zfill(4)  # Ensure the value is 4 digits long, padded with zeros if necessary        
            # 发送单个字节
            ser.write(("lit"+tmp).encode())
            print(ILLUMINATION_PROMPT+f"Sent: {tmp}   ","x:", x)




if __name__ == "__main__":

    tmp = input("Please input cmd: ")

    import time

    while tmp != "exit":
        tmp = tmp.split()
        if(tmp[0] == 'send'):
    # 25092
            # check tmp[1] if is a number and range from 0 to 255
            if len(tmp) > 1 and tmp[1].isdigit():
                value = int(tmp[1])
                x = int( value )
                illumination_at_x(x)
            else:
                print("Please provide a valid number parameter.")
        elif tmp[0] == 'scan':
            if len(tmp) > 1 and tmp[1].isdigit():
                delay_time = int(tmp[1])
                if delay_time>0 and delay_time <= 1000:
                    # 发送单个字节
                    while(1):
                        for x in range(181,253):
                            illumination_at_x(x)
                            time.sleep(delay_time / 1000.0)
                else:
                    print("Value must be between 0 and 255.")
            else:
                print("Please provide a valid number parameter.")     
        else:
            print("Unknown command. Please type 'send' to send data or 'exit' to quit.")

        tmp = input("Please input cmd: ")



"""

2025-6-12

"""
# 照明角度不同，焦点位置会变
# 照明角度不同，不变焦点位置，物体变扁
# 改变照明角度后，如果重新对焦，物体还会扁吗？
# 只要照明在孔径角内，就不会变得很扁



# 光纤之所以会变扁，一部分原因是照明不完全是径向的
    # 径向照明 0402，0407没有什么变化



