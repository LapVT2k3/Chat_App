import socket
import struct
import pickle
import threading
import time

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('127.0.0.1', 9999))
server_socket.listen(4)

clients_connected = {}
clients_data = {}
count = 1


def connection_requests():
    global count
    while True:
        print("Waiting for connection...")
        client_socket, address = server_socket.accept()
        print(f"Connections from {address} has been established")
        
        print(len(clients_connected))
        
        if len(clients_connected) == 4:
            client_socket.sendall('not_allowed'.encode())
            client_socket.close()
            continue
        else:
            client_socket.sendall('allowed'.encode())
            
        try:
            client_name = client_socket.recv(1024).decode('utf-8')
        except:
            print(f"{address} disconnected")
            client_socket.close()
            continue

        print(f"{address} identified itself as {client_name}")

        clients_connected[client_socket] = (client_name, count)
        
        # Nhận ảnh người dùng
        image_size_bytes = client_socket.recv(1024)
        image_size_int = struct.unpack('i', image_size_bytes)[0]

        client_socket.sendall('received'.encode())
        image_extension = client_socket.recv(1024).decode()

        # Lưu dữ liệu ảnh dạng byte khi kích thước ảnh vượt quá 1 byte
        b = b''
        while True:
            image_bytes = client_socket.recv(1024)
            b += image_bytes
            if len(b) == image_size_int:
                break
            
        clients_data[count] = (client_name, b, image_extension)
        
        # Gửi danh sách dữ liệu người dùng tới client đã connect
        clients_data_bytes = pickle.dumps(clients_data)
        clients_data_length = struct.pack('i', len(clients_data_bytes))

        client_socket.sendall(clients_data_length)
        client_socket.sendall(clients_data_bytes)
        
        # Gửi thông báo tới các client khác khi có 1 client kết nối tới server
        if client_socket.recv(1024).decode() == 'image_received':
            
            client_socket.sendall(struct.pack('i', count))

            for client in clients_connected:
                if client != client_socket:
                    client.sendall('notification'.encode())
                    data = pickle.dumps(
                        {'message': f"{clients_connected[client_socket][0]} joined the chat", 'extension': image_extension,
                         'image_bytes': b, 'name': clients_connected[client_socket][0], 'n_type': 'joined', 'id': count})
                    data_length_bytes = struct.pack('i', len(data))
                    client.sendall(data_length_bytes)
                    time.sleep(0.1)
                    client.sendall(data)
                    
        count += 1
        t = threading.Thread(target=receive_data, args=(client_socket,))
        t.start()


def receive_data(client_socket):
    while True:
        try:
            data_bytes = client_socket.recv(1024)
        except:
            print(f"{clients_connected[client_socket][0]} disconnected")

            for client in clients_connected:
                if client != client_socket:
                    client.sendall('notification'.encode())
                    
                    data = pickle.dumps({'message': f"{clients_connected[client_socket][0]} left the chat",
                                         'id': clients_connected[client_socket][1], 'n_type': 'left'})
                    
                    data_length_bytes = struct.pack('i', len(data))
                    client.sendall(data_length_bytes)
                    time.sleep(0.1)
                    client.sendall(data)

            del clients_data[clients_connected[client_socket][1]]
            del clients_connected[client_socket]
            client_socket.close()
            break

        for client in clients_connected:
            if client != client_socket:
                client.sendall('message'.encode())
                client.sendall(data_bytes)

connection_requests()