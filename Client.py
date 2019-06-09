import socket, _thread, time, ast
#from ui_chat import UI_chat

# Client code. Will send info to server
registered = False

# Function run on separate thread to receive messages from server
def get_messages(clientSock):
    global registered

    while 1:
        message = ""
        #print("get message")
        try:
            from_server = clientSock.recv(4096)
            from_server = from_server.decode("utf-8")
            from_server = ast.literal_eval(from_server)
        except Exception as e:
            print("Connection to server lost")
            print(e)
            return

        if from_server["type"] != "error" and not registered:
            registered = True

        if from_server["type"] != "notify" and from_server["type"] != "error":
            # if the message isn't a general notification, we append the time to it
            hour = datetime.now().hour
            if hour < 10:
                hour = "0" + str(hour)
            minute = datetime.now().minute
            if minute < 10:
                minute = "0" + str(minute)
            timestamp = "[" + str(hour) + ":" + str(minute) + "] "
            message = timestamp + from_server["room"] + from_server["user"] + ">>"

        message = message + from_server["msg"]
        print(message)

# loop where user input is collected
def main_loop(host_name, port_num):
    global registered
    clientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        clientSock.connect((host_name, port_num))
    except Exception as e:
        print("Could not connect to server")
        print(e)
        return(-1)
    try:

        # Open a new thread to wait for messages relayed by server
        _thread.start_new_thread(get_messages, (clientSock,))

        # Loop for trying to register name with server, register will be tru if it worked
        while not registered:
            uname = input(str("Input username: "))
            data = {'cmd': 'Reg',
                    'msg': uname,
                    'list': None}
            # print(registered)
            try:
                # clientSock.setblocking(0)
                clientSock.send(str(data).encode("utf-8"))
            except Exception as e:
                print("Connection failed!")
                print(e)
                exit()
            time.sleep(0.1)
        # in main loop get user inputs
        while 1:
            proceed = True
            print("\nAvailable commands:"
                  "\n1)Create/Join Room(s): Joins specified rooms. Creates them if non-existant"
                  "\n2)Message Room(s): Send message to specified room"
                  "\n3)List all Rooms"
                  "\n4)List users in Room"
                  "\n5)Leave Room(s)"
                  "\n6)PM User: Sends a message to a single user/usergroup"
                  "\n7)Quit\n")
            # time.sleep(0.5)
            cmd = input()
            if cmd == "1":
                # join(clientSock, data)
                data['cmd'] = "Join"
            elif cmd == "2":
                # message(clientSock)
                data['cmd'] = "Msg"
            elif cmd == "3":
                # list_rooms(clientSock)
                data['cmd'] = "RList"
            elif cmd == "4":
                # list_users(clientSock)
                data['cmd'] = "UList"
            elif cmd == "5":
                # leave_rooms(clientSock)
                data['cmd'] = "Exit"
            elif cmd == "6":
                data['cmd'] = "PM"
                user_list = []
                looping = True
                while (looping):
                    users = input("Add username or press enter with no input to proceed:")
                    if users:
                        user_list.append(users)
                    else:
                        looping = False
                data['list'] = user_list
                # private_message(clientSock)
            elif cmd == "7":
                clientSock.close()
                registered = False
                return
                # quit_irc(clientSock)
            else:
                print("unknown input")
                proceed = False
            if proceed:
                if (cmd in "1245"):
                    room_list = []
                    looping = True
                    while (looping):
                        rooms = input("Add room name or press enter with no input to proceed:")
                        if rooms:
                            room_list.append(rooms)
                        else:
                            looping = False
                    data['list'] = room_list
                if (cmd in "26"):
                    looping = True
                    msg = input("Message:")
                    data['msg'] = msg
                clientSock.send(str(data).encode("utf-8"))
    except:
        try:
            clientSock.close()
        except Exception as e:
            print(e)
        return()

# main
if __name__ == '__main__':
    host_name = "localhost"
    port_num = 1234
    while 1:
        try:
            main_loop(host_name, int(port_num))
        except:
            break
        proceed = False
        while not proceed:
            user_input = input("Reconnect?(Y/n)")
            if user_input:
                user_input = user_input.upper()
                if user_input == "Y":
                    proceed = True
                elif user_input == "N":
                    exit()
                else:
                    print("Invalid input, please use Y/n answer")

    exit()

