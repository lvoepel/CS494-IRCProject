import sys, re, os, socket, urllib, _thread, time, ast
from datetime import datetime
##########################################################################
# Server code. Will handle connecting clients to one another
##########################################################################

client_list = []
room_list = []

##########################################################################
# Classes used by server
##########################################################################

# Class for a room consisting of a name and a list of clients
class Room_class:
    def __init__ (self, room_name, client_list):
        self.name = room_name
        self.clients = client_list
    def add_client (self, client_id):
        self.clients.append(client_id)
    def remove_client(self, client_id):
        self.clients.remove(client_id)

# Class for a client consisting of the address and socket returned by server.accept()
# and a username and list of rooms added after connection
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

##########################################################################
# General functions for client/server communication
##########################################################################

# Disconnects a given client from the socket. Called when an exception occurs on listening
# loop
def disconnect_client(client):
    if(client.username):
        print(client.username, " was disconnected")
    else:
        print("Client:\n", client, " was disconnected")
    client_list.remove(client)
    for room in client.rooms:
        notify_exit(room, client)
    client.socket.close()

# send a message to a client in dictionary format
# takes in client receiving, room sent from, name of sender, and message
def send_message(client, room, user, message_type, message):
    # creating the dictionary with relevant info
    package = {"type": message_type,
               "room": room,
               "user": user,
               "msg": message}

    # try to send the message. The dictionary is changed to a string then encoded in
    # utf-8 for sending
    try:
        client.socket.send(str(package).encode("utf-8"))
    except Exception as e:
        print(e)

##########################################################################
# Functions for notifying other room members of room changes
##########################################################################
# notifies room that a client is leaving, removes client from its list, and removes room
# from client list
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

##########################################################################
# Main functions
##########################################################################

# joins a room if it exists, otherwise creates the room
# also notifies all room members that someone has entered
# takes in the requesting client and list of rooms to join
def join_room(this_client, selected_rooms):
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


    # Go through remaining list of rooms and create a new rooms with name and current client
    for room_name in selected_rooms:
        new_room = Room_class(room_name, [])
        room_list.append(new_room)
        notify_entrance(new_room, this_client)
        send_message(this_client, new_room.name, "", "notify", "Successfully Created: " + new_room.name)
    for room in room_list:
        print("Room Name: ", room.name, "\nClients: ", room.clients, "\n")

# takes in client and the rooms it wants to leave. If the client isn't in the room does nothing
def leave_room(this_client, selected_rooms):
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
def list_rooms(this_client):
    print("Listing room(s):")
    # Put all existing rooms into a string to return to user
    rooms = ""
    for room in room_list:
        rooms = rooms + room.name + "\n"
    if rooms:
        try:
            send_message(this_client, "", "", "notify", "List of rooms:\n" + rooms)
        except Exception as e:
            print(e)
            #disconnect_client(this_client)
    else:
        try:
            send_message(this_client, "", "", "notify", "No Rooms Found!")
        except Exception as e:
            print(e)
            #disconnect_client(this_client)

# Takes in requesting client and list of rooms and sends list of users in those rooms to client
def list_users(this_client, selected_rooms):
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
def message_room(this_client, selected_rooms, message):
    # Strip duplicate entries
    selected_rooms = list(dict.fromkeys(selected_rooms))

    for room in room_list:
        # If the user is in the room it's sending to and we find that room
        if room.name in selected_rooms and this_client in room.clients:
            for client in room.clients:
                if client != this_client:
                    try:
                        send_message(client, room.name, this_client.username, "room_msg", message)
                    except Exception as e:
                        print(e)
                        #disconnect_client(this_client)


def pm_user(this_client, users, message):
    # Strip duplicate entries
    users = list(dict.fromkeys(users))

    # message = time + this_client.username + " >> "+ message
    for client in client_list:
        if client.username in users:
            try:
                send_message(client, "", this_client.username, "pm", message)
                time.sleep(.1)
            except Exception as e:
                print(e)
                #disconnect_client(this_client)

# Registers a client with a name. If name doesn't work then we return an error and tell client to resend a name
def register_client(this_client, this_name):
    # check for if user somehow sent blank name
    if not this_name:
        send_message(this_client, "", "", "error", "Blank name")
    else:
        found = False
        for client in client_list:
            print("Username: ", client.username)
            if client.username == this_name:
                print("name exists")
                found = True
                break
        # if the name is in use, we send them a message to resend a name before connecting with them
        if found:
            send_message(this_client, "", "", "error", "Name in use" )

        # otherwise name is changed as needed
        else:
            print("name doesnt exist")
            this_client.username = this_name
            send_message(this_client, "", "", "notify", "Connected successfully")
            print("current clients: ")

            for client in client_list:
                print("Username: ", client.username, "\nAddress:", client.address, "\n\n")


##########################################################################
# Functions for client/server listening/setup
##########################################################################
# client handler function. Called on new thread when client connects

def new_client_connect(this_client, data):
    # First loop will involve client registering a username
    if not this_client.username:
        register_client(this_client, data['msg'])

    while 1:

        try:
            data = this_client.socket.recv(1024)
        except Exception as e:
            print(e)
            disconnect_client(this_client)
            return

        # check if data is valid before trying to decode it
        if data:
            data = data.decode("utf-8")
            print(data)
            data = ast.literal_eval(data)
            command = data['cmd']

            # check for registering first so that it won't try to run other commands
            # if username is invalid
            if not this_client.username:
                if command == "Reg":
                    print("registering in data loop")
                    register_client(this_client, data['msg'])

            # message a room
            elif(command == "Msg"):
                print("messaging rooms")
                message_room(this_client, data['list'], data['msg'])

            # Join room if it exists, otherwise creates room
            elif(command == "Join"):
                join_room(this_client, data['list'])

            # Private message user
            elif (command == "PM"):
                pm_user(this_client, data['list'], data['msg'])

            # Leave a room
            elif (command == "Exit"):
                leave_room(this_client, data['list'])

            # list rooms
            elif (command == "RList"):
                list_rooms(this_client)

            # list users in given room
            elif (command == "UList"):
                list_users(this_client, data['list'])
            print("operation finished")
            #send_message(this_client, "", "", "notify", this_client.username + " >>")
        else:
            print(this_client.username, " was disconnected")
            disconnect_client(this_client)
            # print("Client ", address ," has disconnected")
            # client_list.remove(this_client)
            for room in this_client.rooms:
                notify_exit(room, this_client)
            #notify_rooms(str(client[address]) + " has disconnected")
            break
        #clientSock.send(data)
    clientSock.close()

# Main
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
        try:
            data = clientSock.recv(1024)
            data = data.decode("utf-8")
            data = ast.literal_eval(data)

            # Add new client to list, will register in function
            new_client = Client_class(address, "", clientSock)
            client_list.append(new_client)
            _thread.start_new_thread(new_client_connect, (new_client,data,))
        except Exception as e:
            if new_client and new_client in client_list:
                disconnect_client(new_client)
            print(e)

