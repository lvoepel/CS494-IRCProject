import sys, re, os, socket, urllib, _thread, time, ast
from datetime import datetime
# Server code. Will handle connecting clients to one another

# classes used by the server
class Room_class:
    def __init__ (self, room_name, client_list):
        self.name = room_name
        self.clients = client_list
    def add_client (self, client_id):
        self.clients.append(client_id)
    def remove_client(self, client_id):
        self.clients.remove(client_id)

class Client_class:
    address = ""
    username = ""
    socket = ""
    rooms = []
    def __init__(self, addr, uname, clientSock):
        self.address = addr
        self.username = uname
        self.socket = clientSock

    def add_room(self, room):
        rooms.append(room)

# Disconnects a given client from the socket. Used as an exception when client is gone
def disconnect_client(client):
    client_list.remove(client)
    for room in client.rooms:
        notify_exit(room, client)
    client.socket.close()


# send a message to a client in special format
# takes in client receiving, room sent from, name of sender, and message
def send_message(client, room, user, message_type, message):
    if message_type != "notify" and message_type != "error":
        hour = datetime.now().hour
        if hour < 10:
            hour = "0" + str(hour)
        minute = datetime.now().minute
        if minute < 10:
            minute = "0" + str(minute)
        timestamp = "["+str(hour) +":"+ str(minute)+"] "
    else:
        timestamp = ""
    package = {"type": message_type,
               "room": room,
               "user": user,
               "time": timestamp,
               "msg": message}
    try:
        client.socket.send(str(package).encode("utf-8"))
        time.sleep(.1)
    except exception as e:
        print(e)
        #disconnect_client(client)

# notifies room that a client is leaving and removes client from its list
def notify_exit(room, this_client):
    if this_client in room.clients:
        room.clients.remove(this_client)
        this_client.rooms.remove(room)
        message = this_client.username + " has left the room"
        for client in room.clients:
            send_message(client, room.name, "", "room_msg", message)
    print(message)

# Adds a client to room and notifies all room members of client's entrance
def notify_entrance(room, this_client):
    room.clients.append(this_client)
    this_client.rooms.append(room)
    message = this_client.username + " has entered room " + room.name
    for client in room.clients:
        if client != this_client:
            send_message(client, room.name, "", "room_msg", message)
    print(message)

# joins a room if it exists, otherwise creates the room
# also notifies all room members that someone has entered
# takes in the requesting client and list of rooms to join
def join_room(this_client, data):
    selected_rooms = data['Rooms']
    # Strip duplicate entries
    selected_rooms = list(dict.fromkeys(selected_rooms))

    print("Creating room(s): ", selected_rooms)
    # go through existing rooms and compare to selected rooms
    for room in room_list:
        if room.name in selected_rooms:
            # If client isn't in room then add it to it, otherwise do nothing
            if this_client not in room.clients:
                notify_entrance(room, this_client)
                send_message(this_client, room.name, "", "notify", "Successfully Joined: " + room.name)
            #either way remove from list so that we don't try to create it
            selected_rooms.remove(room.name)
    send_message(this_client, "","", "fin", this_client.name + ">>")

    # Go through remaining list of rooms and create a new rooms with name and current client
    for room_name in selected_rooms:
        new_room = Room_class(room_name, [])
        room_list.append(new_room)
        notify_entrance(new_room, this_client)
        send_message(this_client, new_room.name, "", "notify", "Successfully Created: " + new_room.name)
    for room in room_list:
        print("Name: ", room.name, "\nClients: ", room.clients, "\n")

# takes in client and rooms client wants to leave. If the client isn't in the room does nothing
def leave_room(this_client, data):
    selected_rooms = data['Rooms']
    # Strip duplicate entries by mapping to a dictionary then back to a list
    selected_rooms = list(dict.fromkeys(selected_rooms))

    print("Leaving room(s): ", selected_rooms)
    # go through existing rooms and compare to selected rooms
    for room in room_list:
        if room.name in selected_rooms:
            if this_client in room.clients:
                notify_exit(room, this_client)
                if this_client not in room.clients:
                    send_message(this_client, "", "", "notify", "Successfully Left: " + room.name)

# takes in client and sends it the list of rooms on the server
def list_rooms(this_client, data):
    print("Listing room(s):")
    # Put all existing rooms into a string to return to user
    rooms = ""
    for room in room_list:
        rooms = rooms + room.name + "\n"
    if rooms:
        try:
            send_message(this_client, "", "", "notify", "List of rooms:\n" + rooms)
        except exception as e:
            print(e)
            #disconnect_client(this_client)
    else:
        try:
            send_message(this_client, "", "", "notify", "No Rooms Found!")
        except exception as e:
            print(e)
            #disconnect_client(this_client)

# Takes in requesting client and list of rooms and sends list of users in those rooms to client
def list_users(this_client, data):
    selected_rooms = data['Rooms']
    # Strip duplicate entries by mapping to a dictionary then back to a list
    selected_rooms = list(dict.fromkeys(selected_rooms))

    print("Listing Users in room(s): ", selected_rooms)

    # go through existing rooms and compare to selected rooms
    for room in room_list:
        if room.name in selected_rooms:
            users = "Users in " + room.name + ":\n"
            for client in room.clients:
                users = users + client.username + "\n"
            send_message(this_client, "", "", "notify", users)
            # this_client.socket.send((users).encode("utf-8"))
            selected_rooms.remove(room.name)

    # message if rooms don't exist
    if len(selected_rooms) != 0:
        msg = "Could not find room(s):"
        for room_name in selected_rooms:
            msg = msg + room_name + "\n"
        send_message(this_client, "", "", "notify", msg)
        #this_client.socket.send((msg).encode("utf-8"))

# Takes in the client, message, and list of rooms to send to and sends to all clients of rooms
def message_room(this_client, data):
    message = data['msg']
    selected_rooms = data['Rooms']
    # Strip duplicate entries
    selected_rooms = list(dict.fromkeys(selected_rooms))

    for room in room_list:
        # If the user is in the room it's sending to and we find that room
        if room.name in selected_rooms and this_client in room.clients:
            for client in room.clients:
                if client != this_client:
                    try:
                        send_message(client, room.name, this_client.username, "room_msg", message)
                    except exception as e:
                        print(e)
                        #disconnect_client(this_client)


def pm_user(this_client, data):
    message = data['msg']
    users = data['Rooms']
    # Strip duplicate entries
    users = list(dict.fromkeys(users))

    # message = time + this_client.username + " >> "+ message
    for client in client_list:
        if client.username in users:
            try:
                send_message(client, "", this_client.username, "pm", message)
            except Exception as e:
                print(e)
                #disconnect_client(this_client)

# Registers a client with a name. If name doesn't work then we return an error and tell client to resend a name
def register_client(this_client, data):
    this_name = data['msg']

    # check for if user somehow sent blank name
    if not this_name:
        send_message(this_client, "", "", "error", "Blank name")
    else:
        found = False
        for client in client_list:
            if client.username == this_name:
                found = True
                break
        # if the name is in use, we send them a message to resend a name before connecting with them
        if found:
            send_message(this_client, "", "", "error", "Name in use" )

        # otherwise name is changed as needed
        else:
            this_client.username = this_name
            send_message(this_client, "", "", "notify", "Connected successfully")
            print("current clients: ")

            for client in client_list:
                print("Username: ", client.username, "\nAddress:", client.address, "\n\n")

# client handler function. Called on new thread when client connects

def new_client_connect(this_client, data):
    while 1:
        #if client hasn't registered yet
        if not this_client.username:
            register_client(this_client, data)
        # if the first time sending a message we need to register using current data
        try:
            data = this_client.socket.recv(1024)
        except exception as e:
            print(e)
            #disconnect_client(this_client)
            return

        #check if the data works and also if the user has successfully sent a username
        if data:
            print(data)
            data = data.decode("utf-8")
            print(data)
            data = ast.literal_eval(data)

            if (data['cmd'] == "Register"):
                register_client(this_client, data)

            elif(data['cmd'] == "Message"):
                print("messaging rooms")
                message_room(this_client, data)

            # Join room if it exists, otherwise creates room
            elif(data['cmd'] == "Join"):
                join_room(this_client, data)

            # Private message user
            elif (data['cmd'] == "PM"):
                pm_user(this_client, data)

            # Leave a room
            elif (data['cmd'] == "Leave Room"):
                leave_room(this_client, data)


            elif (data['cmd'] == "Create Room"):
                create_room(this_client, data)

            # list rooms
            elif (data['cmd'] == "List Rooms"):
                list_rooms(this_client, data)

            # list rooms in given room
            elif (data['cmd'] == "List Users"):
                list_users(this_client, data)

        else:
            disconnect_client(this_client)
            # print("Client ", address ," has disconnected")
            # client_list.remove(this_client)
            for room in this_client.rooms:
                notify_exit(room, this_client)
            #notify_rooms(str(client[address]) + " has disconnected")
            break
        #clientSock.send(data)
    clientSock.close()

client_list = []
room_list = []
room_names = []

if __name__ == '__main__':

    serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSock.bind(("localhost", 1234))
    print("Waiting for clients...")
    # Listen for connections with max queue of 5
    serverSock.listen(5)

    #listening loop
    while 1:
        (clientSock, address) = serverSock.accept()
        print("client connected with address: " + str(address))
        data = clientSock.recv(1024)
        data = data.decode("utf-8")
        data = ast.literal_eval(data)

        # Add new client to list, will register in function
        new_client = Client_class(address, "", clientSock)
        client_list.append(new_client)
        _thread.start_new_thread(new_client_connect, (new_client,data,))






exit(0)
