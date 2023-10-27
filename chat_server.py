import socket
import struct
import pickle
import threading
import time

# Cấu hình socket bên server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# AF_INET: IPv4
# SOCK_STREAM: TCP
server_socket.bind(('localhost', 12345)) # Cấu hình IP, Port của Server
server_socket.listen(4) # Tối đa 4 kết nối

clients_connected = {} # Chứa thông tin tên và ID của các Client kết nối tới Server
clients_data = {} # Chứa tên, ảnh, đuôi ảnh của Client
count = 1

# Lắng nghe yêu cầu kết nối của Client
def connection_requests():
    global count
    while True:
        print("Waiting for connection...")
        client_socket, address = server_socket.accept()
        # client_socket: Socket đại diện cho kết nối giữa Server và Client
        # address: 1 tuple chứa IP và Port của Client đã kết nối
        print(f"Connections from {address} has been established")
        
        print(len(clients_connected))
        
        # Tối đa 4 người dùng
        if len(clients_connected) == 4:
            client_socket.sendall('not_allowed'.encode())
            client_socket.close()
            continue
        else:
            client_socket.sendall('allowed'.encode())
        
        # Nhận tên người dùng   
        try:
            client_name = client_socket.recv(1024).decode('utf-8')
        except:
            print(f"{address} disconnected")
            client_socket.close()
            continue
        
        print(f"{address} identified itself as {client_name}")

        # Lưu tên, id người dùng
        clients_connected[client_socket] = (client_name, count)
        
        # Nhận ảnh người dùng
        # Nhận kích thước ảnh
        image_size_bytes = client_socket.recv(1024)
        image_size_int = struct.unpack('i', image_size_bytes)[0] # Giải nén kích thước ảnh ra dạng int

        client_socket.sendall('received'.encode()) # Gửi thông báo đã nhận kích thước ảnh tới Client
        image_extension = client_socket.recv(1024).decode('utf-8') # Nhận đuôi ảnh

        # Lưu dữ liệu ảnh dạng byte khi kích thước ảnh vượt quá 1 Mb
        b = b'' # Lưu dữ liệu ảnh
        # Đọc từng Mb một lần
        while True:
            image_bytes = client_socket.recv(1024)
            b += image_bytes
            if len(b) == image_size_int:
                break
        
        # Lưu dữ liệu Client    
        clients_data[count] = (client_name, b, image_extension)
        
        # Gửi danh sách dữ liệu người dùng tới client đã connect
        clients_data_bytes = pickle.dumps(clients_data) # Chuyển đối tượng thành chuỗi bytes
        # NOTE: Làm tương tự như khi chuyển ảnh
        clients_data_length = struct.pack('i', len(clients_data_bytes)) # Lưu kích thước đối tượng

        client_socket.sendall(clients_data_length) # Gửi kích thước danh sách
        time.sleep(0.5) # Delay để Client kịp nhận tin
        client_socket.sendall(clients_data_bytes) # Gửi danh sách
        
        # Nếu phía Client đã nhận được danh sách
        if client_socket.recv(1024).decode() == 'data_received':
            # Gửi ID tới Client
            client_socket.sendall(struct.pack('i', count))
            # Gửi thông báo tới các Client khác khi có 1 Client mới kết nối tới Server
            for client in clients_connected:
                if client != client_socket:
                    time.sleep(0.5)
                    client.sendall('notification'.encode())
                    time.sleep(0.5)
                    # Gửi các thông tin của Client mới đăng nhập
                    data = pickle.dumps(
                        {'message': f"{clients_connected[client_socket][0]} joined the chat", 'extension': image_extension,
                         'image_bytes': b, 'name': clients_connected[client_socket][0], 'n_type': 'joined', 'id': count})
                    
                    data_length_bytes = struct.pack('i', len(data))
                    client.sendall(data_length_bytes)
                    time.sleep(0.5)
                    client.sendall(data)
                    
        count += 1
        # Tạo đa luồng nhận tin nhắn từ Client
        t = threading.Thread(target=receive_data, args=(client_socket,))
        t.start()

# Nhận thông tin từ Client
def receive_data(client_socket):
    while True:
        try: # Nhận tin nhắn từ Client
            data_bytes = client_socket.recv(1024)
        except: # Khi 1 Client ngắt kết nối
            print(f"{clients_connected[client_socket][0]} disconnected")

            # Thông báo tới các Client khác
            for client in clients_connected:
                if client != client_socket:
                    time.sleep(0.5)
                    client.sendall('notification'.encode())
                    time.sleep(0.5)
                    data = pickle.dumps({'message': f"{clients_connected[client_socket][0]} left the chat",
                                         'id': clients_connected[client_socket][1], 'n_type': 'left'})
                    
                    data_length_bytes = struct.pack('i', len(data))
                    client.sendall(data_length_bytes)
                    time.sleep(0.5)
                    client.sendall(data)

            # Xóa Client đó ra khỏi danh sách kết nối
            del clients_data[clients_connected[client_socket][1]]
            del clients_connected[client_socket]
            client_socket.close()
            break
        
        # Gửi tin nhắn của Client đó tới Client khác
        for client in clients_connected:
            if client != client_socket:
                time.sleep(0.5)
                client.sendall('message'.encode())
                time.sleep(0.5)
                client.sendall(data_bytes)

connection_requests()