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
def send_message(client, room, sender, message):
    hour = datetime.now().hour
    if hour < 10:
        hour = "0" + str(hour)
    minute = datetime.now().minute
    if minute < 10:
        minute = "0" + str(minute)
    time = "["+str(hour) +":"+ str(minute)+"] "
    package = {"room": room,
               "time": time,
               "sender": "",
               "msg": message}
    try:
        client.socket.send(str(package).encode("utf-8"))
    except:
        disconnect_client(client)

# notifies room that a client is leaving and removes client from its list
def notify_exit(room, this_client):
    if this_client in room.clients:
        room.clients.remove(this_client)
        this_client.rooms.remove(room)
        message = this_client.username + " has left the room"
        for client in room.clients:
            send_message(client, room.name, "", message)
    print(message)

# Adds a client to room and notifies all room members of client's entrance
def notify_entrance(room, this_client):
    room.clients.append(this_client)
    this_client.rooms.append(room)
    message = this_client.username + " has entered room " + room.name
    for client in room.clients:
        if client != this_client:
            send_message(client, room.name, "", message)
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
                send_message(this_client, room.name, "", "Successfully Joined: " + room.name)
            #either way remove from list so that we don't try to create it
            selected_rooms.remove(room.name)

    # Go through remaining list of rooms and create a new rooms with name and current client
    for room_name in selected_rooms:
        new_room = Room_class(room_name, [])
        notify_entrance(new_room, this_client)
        send_message(this_client, new_room.name, "", "Successfully Created: " + new_room.name)
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
                    send_message(this_client, "", "", "Successfully Left: " + room.name)

# takes in client and sends it the list of rooms on the server
def list_rooms(this_client, data):
    print("Listing room(s):")
    # Put all existing rooms into a string to return to user
    rooms = ""
    for room in room_list:
        rooms = rooms + room.name + "\n"
    if rooms:
        try:
            send_message(this_client, "", "", "List of rooms:\n" + rooms)
        except:
            disconnect_client(this_client)
    else:
        try:
            send_message(this_client, "", "", "No Rooms Found!")
        except:
            disconnect_client(this_client)

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
            send_message(this_client, "", "", users)
            # this_client.socket.send((users).encode("utf-8"))
            selected_rooms.remove(room.name)

    # message if rooms don't exist
    if selected_rooms.len() != 0:
        msg = "Could not find room(s):"
        for room_name in selected_rooms:
            msg = msg + room_name + "\n"
        send_message(this_client, "", "", msg)
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
                        send_message(client, room.name, this_client.username, message)
                    except:
                        disconnect_client(this_client)


def pm_user(this_client, data):
    message = data['msg']
    users = data['Rooms']
    # Strip duplicate entries
    users = list(dict.fromkeys(users))

    time = getTime()
    # message = time + this_client.username + " >> "+ message
    for client in client_list:
        if client.username in users:
            try:
                send_message(client, "", this_client.username, message)
            except Exception as e:
                print(e)
                disconnect_client(this_client)

# client handler function. Called on new thread when client connects

def new_client_connect(this_client):
    while 1:
        data = this_client.socket.recv(1024)
        if(data):
            print(data)
            data = data.decode("utf-8")
            print(data)
            data = ast.literal_eval(data)
            #dictionary = dict(data)
            if(data['cmd'] == "Message"):
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
            print("Client ", address ," has disconnected")
            client_list.remove(this_client)
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

        print("data before callback:", data)
        # Make sure this is actually a register command
        if(data['cmd'] == "Register"):
            found = False
            for client in client_list:
                if client.username == data['msg']:
                    found = True
                    break
            # if the name is in use, we don't register the client and return an empty
            if found:
                package = {"room": "",
                           "time": "",
                           "sender": "",
                           "msg": ""}
                clientSock.send(str(package).encode("utf-8"))
            else:
                new_client = Client_class(address, data['msg'], clientSock)
                client_list.append(new_client)
                print("current clients: ")

                for client in client_list:
                    print("Username: ", client.username, "\nAddress:", client.address,"\n\n")
                send_message(new_client, "", "", "Connected successfully")
                _thread.start_new_thread(new_client_connect, (new_client,))
exit(0)
