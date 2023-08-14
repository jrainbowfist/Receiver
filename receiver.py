# Connects to receiver and grabs messages, then writes them to a database
# Assumes specific message format (See "decode_message()" for format)

import serial
from mysql.connector import MySQLConnection, Error
from textwrap import wrap
from read_config import read_config


# recv_string is a string of data to check; format should be a string of hex digits
# chcksm is the checksum to check; format should be a string with hex digits
def verify_checksum(recv_string, chcksm):
    hex_bytes = wrap(recv_string, 2)  # Divide the string into each byte (size = 2 characters)
    total_val = sum(int(i, 16) for i in hex_bytes)  # Sum of all bytes
    result = total_val % 256  # Checksum == sum % 256
    if chcksm[0] == '0':
        chcksm = chcksm[1:]
    if hex(result) == '0x' + chcksm:  # Convert result to hex and format chcksm into hex string
        return True  # Checksum verification successful
    else:
        print(f"{hex(result)} != {'0x' + chcksm}")
        return False  # Checksum verification failed


# Accepts full message except header, length, and checksum
def decode_message(input_string):
    originator_uid = input_string[:8]
    first_hop_uid = input_string[8:16]
    trace_count = input_string[16:18]
    hop_count = input_string[18:20]
    security_byte = input_string[20:22]
    PTI = input_string[22:24]
    alarm_flag = input_string[24:26]
    sup_flag = input_string[26:28]
    level = input_string[28:30]
    margin = input_string[30:32]
    return (originator_uid, first_hop_uid, trace_count, hop_count,
            security_byte, PTI, alarm_flag, sup_flag, level, margin)


# Input is in the form of a tuple with all necessary information
def write_to_database(input):
    query = """ INSERT INTO signal_test_one 
                VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())"""
    try:
        db_config = read_config()
        conn = MySQLConnection(**db_config)
        cursor = conn.cursor()
        cursor.execute(query, input)
        conn.commit()
    except Error as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


# Pass in the COM port to connect to receiver
# Messages received by receiver is assumed to be in format of Header, length of message, message, checksum
# Assumes valid headers are 72 and 1c
def run_receiver(com_port):
    s = serial.Serial(com_port, 9600)
    while True:
        res = s.read()  # Read first byte
        if res.hex() == "72" or res.hex() == "1c":  # If first byte is 0x72, process message received
            res_len = s.read().hex()
            res_2 = s.read(int("0x" + res_len, 16) - 1)  # -2 since first two bytes are read but +1 for the checksum
            if verify_checksum(f"{res.hex()}{res_len}{res_2.hex()[:-2]}", res_2.hex()[-2:]):
                print("Checksum verified")
            else:
                print("Checksum failed")
            print(f"{res.hex()}{res_len}{res_2.hex()}")
            if res.hex() == "72":
                write_to_database(decode_message(res_2.hex()[:-2]))
        else:
            print("Error: Unrecognized message format ")
            print(res.hex())
            break