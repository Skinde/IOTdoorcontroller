import pyfirmata
import time
import plate_validation
board = pyfirmata.Arduino('COM3')  # Cambia por el puerto correspondiente

PWM_pin = 3
frequency_of_motor = 200
rows = [4,5,6,7]
columns = [8,9,10,11]
spin_one_side = 12
spin_other_side = 13
row_offset = 4
column_offset = 8

keyboard_characters = [['1','2','3','A'],['4','5','6','B'],['7','8','9','C'],['*','0','#','D']]
# Start an iterator to avoid buffer overflow for input pins
it = pyfirmata.util.Iterator(board)
it.start()

current_input = ""
password = "007A"
max_password_length = 4

def check_password():
    global password, current_input
    if current_input == password:
        current_input = ""
        return True
    return False

def check_password_length():
    global max_password_length, current_input
    if len(current_input) > max_password_length:
        current_input = ""
        return True
    return False

def update_input(next_character):
    global current_input
    current_input = current_input + next_character
    if check_password():
        return True
    if check_password_length():
        return False
    return None

def open_sesame():

    board.digital[spin_one_side].write(1)
    time.sleep(1)
    board.digital[spin_one_side].write(0)

    time.sleep(5)

    

    board.digital[spin_other_side].write(1)
    time.sleep(1)
    board.digital[spin_other_side].write(0)
    
    

def setup():

    pwm = board.get_pin("d:" + str(PWM_pin) + ":p")
    pwm.write(1)


    board.digital[spin_one_side].mode = pyfirmata.OUTPUT
    board.digital[spin_other_side].mode = pyfirmata.OUTPUT
    board.get_pin("d:" + str(spin_one_side) + ":o")
    board.get_pin("d:" + str(spin_other_side) + ":o")


    print("estoy en el setup")
    for pin in rows:
        board.digital[pin].mode = pyfirmata.OUTPUT
        board.get_pin("d:" + str(pin) + ":o")
    
    for pin in columns:
        board.digital[pin].mode = pyfirmata.INPUT
        board.get_pin("d:" + str(pin) + ":i")

    for row in rows:
        board.digital[row].write(1)

setup()

def read_keyboard():

    for column in columns:
        if board.digital[column].read():
            time.sleep(0.05)
            #A key has been pressed but what row?
            for row in rows:
                board.digital[row].write(0)
                time.sleep(0.02)
                if not board.digital[column].read():
                    #This row was pressed
                    board.digital[row].write(1)
                    return [row,column]
                board.digital[row].write(1)
    return None

def handle_keyboard():
    ans = read_keyboard()
    if ans is not None:
        return keyboard_characters[ans[0] - row_offset][ans[1] - column_offset]
    return None


while True:
    open_door_bool = None
    if plate_validation.plate_validation():
        print("insert password")
        while open_door_bool is None:
            ans = handle_keyboard()
            if ans is not None:
                open_door_bool = update_input(ans)
                print(current_input)
                if open_door_bool is not None:
                    if open_door_bool:
                        open_sesame()
                        print("Openning door")
                    else:
                        print("Wrong password")
            time.sleep(1)