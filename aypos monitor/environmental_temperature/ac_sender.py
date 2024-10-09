import serial
import time


arduino = serial.Serial(port='COM7', baudrate=9600, timeout=1)


def send_temperature(desired_temp):
    command = str(desired_temp).strip() + '\n'
    print(command)

    arduino.write(command.encode())
    time.sleep(0.1)


def listen_for_temperature():
    data = arduino.readline().decode('utf-8').strip()
    print(data)


def main_ac_sender(user_input: int):

    if user_input == "exit":
        print("Exiting...")

    elif user_input == "bottom":
        arduino.write("set_bottom_temperature\n".encode())

    else:
        try:

            desired_temp = int(user_input)
            if 18 <= desired_temp <= 30:
                send_temperature(desired_temp)

            else:
                print("Please enter a value between 18 and 30.")
        except ValueError:
            print("Invalid input. Please enter a valid number or 'bottom'.")


# main_ac_sender(30)
if __name__ == "__main__":
    # listen_for_temperature()
    main_ac_sender(22)
    # time.sleep(2)
