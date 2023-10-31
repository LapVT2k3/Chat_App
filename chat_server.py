import os
import socket
import struct
import pickle
import threading
import time
import pyodbc


SIGNIN = 'signin'
SIGNUP = 'signup'
IP = '192.168.52.100'
PORT = 12345

current_dir = os.path.dirname(os.path.abspath(__file__))

# Kết nối tới database
conx = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};\
    SERVER=LAPTOP-84HLVAJD\SQLEXPRESS; DATABASE=BTL_Python_Account;\
        UID=vtl; PWD=19122003;')

cursor = conx.cursor()

# Cấu hình socket bên server
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# AF_INET: IPv4
# SOCK_STREAM: TCP
server_socket.bind((IP, PORT)) # Cấu hình IP, Port của Server
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
        
        try:
            status = client_socket.recv(1024).decode('utf-8')
        except:
            print(f"{address} disconnected")
            client_socket.close()
            continue
        
        if status == SIGNUP:
            data_bytes = client_socket.recv(1024)
            data = pickle.loads(data_bytes)
            
            cursor.execute("select * from Account where username = ?", data['username'])
            result = cursor.fetchall()
            
            if result:
                client_socket.send('fail'.encode('utf-8'))
            else:
                cursor.execute("insert Account values (?, ?, ?)", data['username'], data['pass'], data['name'])
                cursor.commit()
                client_socket.send('success'.encode('utf-8'))
            client_socket.close()
            continue
        elif status == SIGNIN:
            data_bytes = client_socket.recv(1024)
            data = pickle.loads(data_bytes)
            
            cursor.execute("select * from Account where username = ? and pass = ?", data['username'], data['pass'])
            result = cursor.fetchone()
            if result:
                client_socket.send('success'.encode('utf-8'))
            else:
                client_socket.send('fail'.encode('utf-8'))
                client_socket.close()
                continue
        
        client_name = result[2]
        
        client_socket.recv(1024)
        client_socket.send(client_name.encode('utf-8'))
        
        with open(current_dir + '/images/user.png', 'rb') as f:
            image_bytes = f.read()
        image_extension = 'png'
        print(f"{address} identified itself as {client_name}")

        # Lưu tên, id người dùng
        clients_connected[client_socket] = (client_name, count)
        
        # Lưu dữ liệu Client    
        clients_data[count] = (client_name, image_bytes, 'png')
        
        # Gửi danh sách dữ liệu người dùng tới client đã connect
        clients_data_bytes = pickle.dumps(clients_data) # Chuyển đối tượng thành chuỗi bytes
        clients_data_length = struct.pack('i', len(clients_data_bytes)) # Lưu kích thước đối tượng
        client_socket.recv(1024)
        client_socket.send(clients_data_length) # Gửi kích thước danh sách
        client_socket.recv(1024) 
        client_socket.sendall(clients_data_bytes) # Gửi danh sách
        
        # Nếu phía Client đã nhận được danh sách
        if client_socket.recv(1024).decode() == 'data_received':
            # Gửi ID tới Client
            client_socket.sendall(struct.pack('i', count))
            # Gửi thông báo tới các Client khác khi có 1 Client mới kết nối tới Server
            for client in clients_connected:
                if client != client_socket:
                    time.sleep(0.05)
                    client.sendall('notification'.encode())
                    time.sleep(0.05)
                    # Gửi các thông tin của Client mới đăng nhập
                    data = pickle.dumps(
                        {'message': f"{clients_connected[client_socket][0]} joined the chat", 'extension': image_extension,
                         'image_bytes': image_bytes, 'name': clients_connected[client_socket][0], 'n_type': 'joined', 'id': count})
                    
                    data_length_bytes = struct.pack('i', len(data))
                    client.sendall(data_length_bytes)
                    time.sleep(0.05)
                    client.sendall(data)
                    
        count += 1
        # Tạo đa luồng nhận tin nhắn từ Client
        t = threading.Thread(target=receive_data, args=(client_socket,))
        
        t.start()
        

# Nhận thông tin từ Client
def receive_data(client_socket):
    while True:
        try: # Nhận tin nhắn từ Client
            data_tyte = client_socket.recv(1024).decode('utf-8')
        except: # Khi 1 Client ngắt kết nối
            print(f"{clients_connected[client_socket][0]} disconnected")

            # Thông báo tới các Client khác
            for client in clients_connected:
                if client != client_socket:
                    time.sleep(0.05)
                    client.sendall('notification'.encode())
                    time.sleep(0.05)
                    data = pickle.dumps({'message': f"{clients_connected[client_socket][0]} left the chat",
                                         'id': clients_connected[client_socket][1], 'n_type': 'left'})
                    
                    data_length_bytes = struct.pack('i', len(data))
                    client.sendall(data_length_bytes)
                    time.sleep(0.05)
                    client.sendall(data)

            # Xóa Client đó ra khỏi danh sách kết nối
            del clients_data[clients_connected[client_socket][1]]
            del clients_connected[client_socket]
            client_socket.close()
            break
             
        if data_tyte == 'message':
            data_bytes = client_socket.recv(1024)
            # Gửi tin nhắn của Client đó tới Client khác
            for client in clients_connected:
                if client != client_socket:
                    time.sleep(0.05)
                    client.send('message'.encode())
                    time.sleep(0.05)
                    client.sendall(data_bytes)
        elif data_tyte == 'file':
            info_sender = pickle.loads(client_socket.recv(1024))
            from_ = info_sender['from']
            name = info_sender['name']
            
            file_name = client_socket.recv(1024).decode('utf-8')
                        
            file_bytes = b""
            done = False
            
            while not done:
                data = client_socket.recv(1024)
                file_bytes += data
                if file_bytes[-5:] == b"<END>":
                    done = True
            file_bytes = file_bytes[:-5]
            
            for client in clients_connected:
                if client != client_socket:
                    time.sleep(0.05)
                    client.send('file'.encode())
                    time.sleep(0.05)
                    client.send(pickle.dumps({'from': from_, 'name': name, 'file_name': file_name}))
                    time.sleep(0.05)
                    client.send(file_bytes)
                    client.send(b"<END>")
                     

try:
    connection_requests()
except KeyboardInterrupt:
    pass
finally:
    server_socket.close()
    conx.close()   

