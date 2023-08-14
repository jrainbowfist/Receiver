import receiver


# Input in the form of string 'COM1', 'COM2', etc
if __name__ == '__main__':
    com_port = input("Please enter the COM port for the receiver: \n")
    receiver.run_receiver(com_port)

