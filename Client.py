import sys, re, os, socket, urllib, _thread, time,  ast
from datetime import datetime
#from ui_chat import UI_chat

# Client code. Will send info to server

# classes used by the server
class Room:
    def __init__ (self, room_name, client_list):
        self.name = room_name
        self.clients = client_list
    def add_client (self, client_id):
        self.clients.append(client_id)
    def remove_client(self, client_id):
        self.clients.remove(client_id)


def send_data(clientSock, command, data):
    clientSock.send(str(data).encode("utf-8"))
'''
def join(clientSock):
    
def message(clientSock):
    
def list_rooms(clientSock):
    
def list_users(clientSock):
    
def leave_rooms(clientSock):
    
def private_message(clientSock):
    
def quit_irc(clientSock):
'''
registered = False

# Function run on separate thread to receive messages from server
def get_messages(clientSock):
    global registered

    while 1:
        message = ""
        #print("get message")
        from_server = clientSock.recv(4096)
        from_server = from_server.decode("utf-8")
        from_server = ast.literal_eval(from_server)

        if from_server["type"] != "error" and not registered:
            registered = True

        # print(registered)
        if from_server["type"] != "notify":
            message = from_server["room"] + from_server['time'] + from_server["user"] + ">>"
        message = message + from_server["msg"]
        print(message)


if __name__ == '__main__':
    # set up socket and get username from user
    clientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSock.connect(("localhost", 1234))

    # Open a new thread to wait for messages relayed by server
    _thread.start_new_thread(get_messages, (clientSock,))

    # Loop for trying to register name with server, register will be tru if it worked
    while not registered:
        print(registered)
        uname = input(str("Input username: "))
        data = {'cmd' : 'Register',  'msg': uname, 'Rooms':None}
        # print(registered)
        try:
            #clientSock.setblocking(0)
            clientSock.send(str(data).encode("utf-8"))
        except Exception as e:
            print("Connection failed!")
            print(e)
            exit()
        time.sleep(0.2)

    # in main loop get user inputs
    while 1:
        proceed = True
        print("Available commands:"
              "\n1)Create/Join Room(s): Joins specified rooms. Creates them if non-existant"
              "\n2)Message Room(s): Send message to specified room"
              "\n3)List all Rooms"
              "\n4)List users in Room"
              "\n5)Leave Room(s)"
              "\n6)PM User: Sends a message to a single user/usergroup"
              "\n7)Quit\n")
        #time.sleep(0.5)
        cmd = input()
        if cmd == "1":
            #join(clientSock, data)
            data['cmd'] = "Join"
        elif cmd == "2":
            #message(clientSock)
            data['cmd'] = "Message"
        elif cmd == "3":
            #list_rooms(clientSock)
            data['cmd'] = "List Rooms"
        elif cmd == "4":
            #list_users(clientSock)
            data['cmd'] = "List Users"
        elif cmd == "5":
            #leave_rooms(clientSock)
            data['cmd'] = "Leave Room"
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
            data['Rooms'] = user_list
            #private_message(clientSock)
        elif cmd == "7":
            exit()
            #quit_irc(clientSock)
        else:
            print("unknown input")
            proceed = False
        if proceed:
            if(cmd in "1245"):
                room_list = []
                looping = True
                while(looping):
                    rooms = input("Add room name or press enter with no input to proceed:")
                    if rooms:
                        room_list.append(rooms)
                    else:
                        looping = False
                data['Rooms'] = room_list
            if(cmd in "26"):
                looping = True
                msg = input("Message:")
                data['msg'] = msg
            clientSock.send(str(data).encode("utf-8"))
        # time = "["+str(datetime.now().hour) +":"+ str(datetime.now().minute)+"] "
        # message = time + message
    # print(clientSock.recv(20))
    clientSock.close(0)
    exit()
    exit(0)

