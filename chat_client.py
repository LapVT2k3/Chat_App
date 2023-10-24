import socket
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
import pickle
from datetime import datetime
import os
import threading
import struct

# Lấy đường dẫn thư mục chứa file hiện tại
current_dir = os.path.dirname(os.path.abspath(__file__))
IP = '127.0.0.1'
PORT = 12345

# Thay đổi DPI giúp ứng dụng hiển thị đẹp hơn trên màn hình có độ phân giải cao
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

# Màn hình đăng nhập
class FirstScreen(tk.Tk): # Kế thừa lớp tk.Tk để tạo giao diện
    def __init__(self):
        super().__init__() # Khởi tạo lớp cha để tạo cửa sổ giao diện
        
        # Cấu hình cửa sổ giao diện
        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight() 
        self.x_co = int((screen_width / 2) - (550 / 2))
        self.y_co = int((screen_height / 2) - (400 / 2)) - 80
                
        self.geometry(f"550x400+{self.x_co}+{self.y_co}")
        self.title("Chat Room")

        
        self.user = None # Tên người dùng
        self.image_extension = None # Đuôi file ảnh
        self.image_path = None # Đường dẫn ảnh

        # Tạo First Frame
        self.first_frame = tk.Frame(self, bg="sky blue")
        self.first_frame.pack(fill="both", expand=True)

        # Icon App
        app_icon = Image.open(current_dir + '\\images\\icon_chat.png')
        app_icon = ImageTk.PhotoImage(app_icon)
        self.iconphoto(False, app_icon)

        # Background
        background = Image.open(current_dir + '\\images\\bg_reg.png')
        background = background.resize((550, 400), Image.LANCZOS) # Thay đổi kích cỡ và làm mịn ảnh
        background = ImageTk.PhotoImage(background)
        tk.Label(self.first_frame, image=background).place(x=0, y=0)

        # Icon của nút Upload ảnh
        upload_image = Image.open(current_dir + '\\images\\icon_upload.jpg')
        upload_image = upload_image.resize((25, 25), Image.LANCZOS)
        upload_image = ImageTk.PhotoImage(upload_image)

        self.user_image = current_dir + '\\images\\user.png' 

        # Label "Login"
        head = tk.Label(self.first_frame, text="Login", font="lucida 17 bold", bg="#00FFFF")
        head.place(x=0, y=0, width=550)

        # Label chứa ảnh
        self.profile_label = tk.Label(self.first_frame, bg="grey")
        self.profile_label.place(x=200, y=63, width=160, height=150)

        # Nút upload ảnh
        upload_button = tk.Button(self.first_frame, image=upload_image, compound="left", text="Upload Image",
                                  cursor="hand2", font="lucida 12 bold", padx=2, command=self.add_photo)
        upload_button.place(x=200, y=220)

        # Label "Username"
        self.username = tk.Label(self.first_frame, text="Username", font="lucida 12 bold", bg = "SystemWindow")
        self.username.place(x=90, y=280)

        # Ô nhập tên
        self.username_entry = tk.Entry(self.first_frame,  font="lucida 12 bold", width=12,
                                       highlightcolor="blue", highlightthickness=1)
        self.username_entry.place(x=210, y=280)
        self.username_entry.focus_set()

        # Nút "Connect"
        submit_button = tk.Button(self.first_frame, text="Connect", font="lucida 12 bold", padx=30, cursor="hand2",
                                  command=self.process_data, bg="#16cade", relief="solid", bd=2)

        submit_button.place(x=200, y=335)
        
        self.mainloop() # Chạy giao diện

    def add_photo(self):
        self.image_path = filedialog.askopenfilename() # Hiển thị hộp thoại chọn file
        image_name = os.path.basename(self.image_path)  # Tách tên file ảnh từ đường dẫn
        self.image_extension = image_name[image_name.rfind('.')+1:] # Lấy đuôi file ảnh

        # Lấy ảnh lưu lại và đặt ảnh trong lable chứa ảnh
        if self.image_path:
            # Lấy ảnh
            user_image = Image.open(self.image_path)
            user_image = user_image.resize((150, 140), Image.LANCZOS)
            # Lưu ảnh
            user_image.save('resized'+image_name)
            user_image.close()
            self.image_path = 'resized'+image_name
            # Đặt ảnh vào lable chứa ảnh
            user_image = Image.open(self.image_path)
            user_image = ImageTk.PhotoImage(user_image)
            self.profile_label.image = user_image
            self.profile_label.config(image=user_image)

    # Xử lý kết nối tới server
    def process_data(self):
        if self.username_entry.get():
            self.profile_label.config(image="")

            # Lấy tên tối đa 6 ký tự
            if len((self.username_entry.get()).strip()) > 6:
                self.user = self.username_entry.get()[:6]+"."
            else:
                self.user = self.username_entry.get()

            # Cấu hình socket bên client
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                client_socket.connect((IP, PORT))
                status = client_socket.recv(1024).decode()
                if status == 'not_allowed': # Nếu server đã quá 4 người
                    client_socket.close()
                    messagebox.showinfo(title="Can't connect !", message='Sorry, server is completely occupied.'
                                                                         'Try again later')
                    return

            except ConnectionRefusedError: # Lỗi server chưa mở
                messagebox.showinfo(title="Can't connect !", message="Server is offline , try again later.")
                print("Server is offline , try again later.")
                return

            # Gửi tên người dùng cho Server
            client_socket.send(self.user.encode('utf-8'))

            # Gửi ảnh người dùng cho Server
            # Đọc dữ liệu ảnh
            if not self.image_path:
                self.image_path = self.user_image
            with open(self.image_path, 'rb') as image_data: # Đọc dưới chế độ nhị phân
                image_bytes = image_data.read()

            # NOTE: Nếu ảnh có kích thước lớn hơn 1 Mb (1024 bytes) thì phải gửi kích thước ảnh
            #       để Server có thể đọc từng Mb 1 lần 
            # Gửi kích thước độ lớn của ảnh
            image_size_int = len(image_bytes)
            image_size_bytes = struct.pack('i', image_size_int) # Nén kích thước ảnh thành chuỗi bytes
            client_socket.send(image_size_bytes)

            if client_socket.recv(1024).decode() == 'received': 
                client_socket.send(str(self.image_extension).strip().encode()) # Gửi đuôi ảnh

            client_socket.send(image_bytes) # Gửi dữ liệu ảnh

            clients_data_size_bytes = client_socket.recv(1024)
            clients_data_size_int = struct.unpack('i', clients_data_size_bytes)[0]
            
            # Nhận danh sách dữ liệu các người dùng kết nối tới Server
            # Lưu dữ liệu danh sách dữ liệu người kết nối tới Server dạng byte
            b = b''
            while True:
                clients_data_bytes = client_socket.recv(1024)
                b += clients_data_bytes
                if len(b) == clients_data_size_int:
                    break
            # Giải nén dữ liệu danh sách về dạng ban đầu
            clients_connected = pickle.loads(b)

            # Gửi thông báo đã nhận danh sách tới Server
            client_socket.send('data_received'.encode())

            # Nhận ID
            user_id = struct.unpack('i', client_socket.recv(1024))[0]
            print(f"{self.user} is user no. {user_id}")
            
            # Mở cửa sổ chat
            ChatScreen(self, self.first_frame, client_socket, clients_connected, user_id)

# Màn hình chat
class ChatScreen(tk.Canvas): # Kế thừa tk.Canvas vẽ các hình ảnh, giao diện và các đối tượng đồ họa khác
    def __init__(self, parent, first_frame, client_socket, clients_connected, user_id):

        super().__init__(parent)
        self.window = 'ChatScreen' # Đặt tên để xác định cửa sổ

        self.first_frame = first_frame
        self.first_frame.pack_forget() # Ẩn First Frame

        self.parent = parent
        self.parent.bind('<Return>', lambda e: self.sent_message_format(e)) # Gán hàm xử lý sự kiện khi nhấn phím enter

        self.user_id = user_id

        self.clients_connected = clients_connected

        self.parent.protocol("WM_DELETE_WINDOW", self.on_closing) # Gán sự kiện khi thực hiện tắt cửa sổ

        self.client_socket = client_socket
        
        screen_width, screen_height = self.winfo_screenwidth(), self.winfo_screenheight()

        x_co = int((screen_width / 2) - (680 / 2))
        y_co = int((screen_height / 2) - (750 / 2)) - 80
        self.parent.geometry(f"680x750+{x_co}+{y_co}")

        global background
        background = Image.open(current_dir + '\\images\\bg_chat.jpg')
        background = background.resize((1600, 1900), Image.LANCZOS) # Thay đổi kích cỡ và làm mịn ảnh
        background = ImageTk.PhotoImage(background)
        self.create_image(0, 0, image = background)

        # Lấy ảnh người dùng
        user_image = Image.open(self.parent.image_path)
        user_image = user_image.resize((40, 40), Image.LANCZOS)
        self.user_image = ImageTk.PhotoImage(user_image)

        # Tạo ảnh nhóm
        global group_photo
        group_photo = Image.open(current_dir + '\\images\\group_ca.png')
        group_photo = group_photo.resize((60, 60), Image.LANCZOS)
        group_photo = ImageTk.PhotoImage(group_photo)
        self.create_image(60, 40, image=group_photo)
        
        self.y = 140 # Tọa độ y hiển thị client online đầu tiên trong bảng danh sách
        self.clients_online_labels = {} # Danh sách Client

        # Tạo giao diện 1 số label đơn giản
        self.create_text(580, 120, text="Online", font="lucida 12 bold", fill="red")

        # tk.Label(self, text="   ", font="lucida 15 bold").place(x=4, y=29)
        self.create_text(270, 40, text = "Group Chat", font="lucida 16 bold", fill = "red")
        # tk.Label(self, text="Group Chat", font="lucida 15 bold", padx=20, fg="green",
        #          anchor="w").place(x=88, y=29, relwidth=1)

        # Cửa sổ chat
        container = tk.Frame(self)
        container.place(x=30, y=90, width=470, height=590)
        self.canvas = tk.Canvas(container, bg="#595656")
        self.scrollable_frame = tk.Frame(self.canvas, bg="#595656")

        # Cấu hình cửa sổ cuộn
        scrollable_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Cấu hình thuộc tính scrollregion của canvas để xác định vùng cuộn bên trong canvas
        def configure_scroll_region(e):
            # bbox(): xác định hình chữ nhật bao quanh 1 hoặc nhiều đối tượng trong widget
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))

        # Thay đổi kích thước của scrollable_window để phù hợp với kích thước của canvas
        def resize_frame(e):
            self.canvas.itemconfig(scrollable_window, width=e.width)

        # Gán sự kiện khi thay kích thước hoặc vị trí của scrollable_frame thay đổi
        self.scrollable_frame.bind("<Configure>", configure_scroll_region)

        # Cấu hình thanh cuộn
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview) # Tạo thanh cuộn dọc
        self.canvas.configure(yscrollcommand=scrollbar.set) # Cấu hình canvas sử dụng thanh cuộn dọc
        self.yview_moveto(1.0) # Thiết lập vị trí hiện tại của thanh cuộn (1.0 là vị trí cuối cùng)
        scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", resize_frame) # Gán sự kiện khi kích thước frame thay đổi
        self.canvas.pack(fill="both", expand=True)

        # Cấu hình nút "Send"
        send_button = tk.Button(self, text="Send", fg="#83eaf7", font="lucida 11 bold", bg="#7d7d7d", padx=10,
                                relief="solid", bd=2, command=self.sent_message_format)
        send_button.place(x=400, y=688)

        # Cấu hình text nhập tin nhắn
        self.entry = tk.Text(self, font="lucida 10 bold", width=38,height=2,
                             highlightcolor="blue", highlightthickness=1)
        self.entry.place(x=30, y=685)

        self.entry.focus_set()

        # ---------------------------emoji code logic-----------------------------------
                
        emoji_data = [(current_dir + '/emojis/u0001f44a.png', '\U0001F44A'), (current_dir + '/emojis/u0001f44c.png', '\U0001F44C'), (current_dir + '/emojis/u0001f44d.png', '\U0001F44D'),
                      (current_dir + '/emojis/u0001f495.png', '\U0001F495'), (current_dir + '/emojis/u0001f496.png', '\U0001F496'), (current_dir + '/emojis/u0001f4a6.png', '\U0001F4A6'),
                      (current_dir + '/emojis/u0001f4a9.png', '\U0001F4A9'), (current_dir + '/emojis/u0001f4af.png', '\U0001F4AF'), (current_dir + '/emojis/u0001f595.png', '\U0001F595'),
                      (current_dir + '/emojis/u0001f600.png', '\U0001F600'), (current_dir + '/emojis/u0001f602.png', '\U0001F602'), (current_dir + '/emojis/u0001f603.png', '\U0001F603'),
                      (current_dir + '/emojis/u0001f605.png', '\U0001F605'), (current_dir + '/emojis/u0001f606.png', '\U0001F606'), (current_dir + '/emojis/u0001f608.png', '\U0001F608'),
                      (current_dir + '/emojis/u0001f60d.png', '\U0001F60D'), (current_dir + '/emojis/u0001f60e.png', '\U0001F60E'), (current_dir + '/emojis/u0001f60f.png', '\U0001F60F'),
                      (current_dir + '/emojis/u0001f610.png', '\U0001F610'), (current_dir + '/emojis/u0001f618.png', '\U0001F618'), (current_dir + '/emojis/u0001f61b.png', '\U0001F61B'),
                      (current_dir + '/emojis/u0001f61d.png', '\U0001F61D'), (current_dir + '/emojis/u0001f621.png', '\U0001F621'), (current_dir + '/emojis/u0001f624.png', '\U0001F621'),
                      (current_dir + '/emojis/u0001f631.png', '\U0001F631'), (current_dir + '/emojis/u0001f632.png', '\U0001F632'), (current_dir + '/emojis/u0001f634.png', '\U0001F634'),
                      (current_dir + '/emojis/u0001f637.png', '\U0001F637'), (current_dir + '/emojis/u0001f642.png', '\U0001F642'), (current_dir + '/emojis/u0001f64f.png', '\U0001F64F'),
                      (current_dir + '/emojis/u0001f920.png', '\U0001F920'), (current_dir + '/emojis/u0001f923.png', '\U0001F923'), (current_dir + '/emojis/u0001f928.png', '\U0001F928')] 
        emoji_x_pos = 510
        emoji_y_pos = 520
        for Emoji in emoji_data:
            global emojis
            emojis = Image.open(Emoji[0])
            emojis = emojis.resize((20, 20), Image.LANCZOS)
            emojis = ImageTk.PhotoImage(emojis)

            emoji_unicode = Emoji[1]
            emoji_label = tk.Label(self, image=emojis, text=emoji_unicode, bg="#194548", cursor="hand2")
            emoji_label.image = emojis
            emoji_label.place(x=emoji_x_pos, y=emoji_y_pos)
            emoji_label.bind('<Button-1>', lambda x: self.insert_emoji(x)) # Gán sự kiện khi nhấn chuột trái

            emoji_x_pos += 25
            cur_index = emoji_data.index(Emoji)
            if (cur_index + 1) % 6 == 0:
                emoji_y_pos += 25
                emoji_x_pos = 510

        # -------------------end of emoji code logic-------------------------------------

        # Tạo frame chào mừng client đăng nhập vào Chat Room
        m_frame = tk.Frame(self.scrollable_frame, bg="#d9d5d4")

        #Thêm thời gian tham gia của user
        t_label = tk.Label(m_frame, bg="#d9d5d4", text=datetime.now().strftime('%H:%M'), font="lucida 9 bold")
        t_label.pack()

        m_label = tk.Label(m_frame, wraplength=250, text=f"Happy Chatting {self.parent.user}",
                           font="lucida 10 bold", bg="orange")
        m_label.pack(fill="x")

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.pack(fill="both", expand=True)

        # Khởi tạo danh sách client online dựa trên những Client đã tham gia
        self.clients_online([])

        # Tạo đa luồng nhận dữ liệu từ Server
        t = threading.Thread(target=self.receive_data)
        t.daemon = True
        t.start()

    # Nhận dữ liệu từ Server
    def receive_data(self):
        while True:
            try:
                data_type = self.client_socket.recv(1024).decode()

                if data_type == 'notification': # Thông báo có user khác kết nối hoặc ngắt kết nối đến server
                    data_size = self.client_socket.recv(1024)
                    data_size_int = struct.unpack('i', data_size)[0]
                    b = b''
                    while True:
                        data_bytes = self.client_socket.recv(1024)
                        b += data_bytes
                        if len(b) == data_size_int:
                            break
                    data = pickle.loads(b)
                    self.notification_format(data)

                else: # Nếu data_type = 'message'
                    data_bytes = self.client_socket.recv(1024) # Nhận tin nhắn từ client khác
                    data = pickle.loads(data_bytes)
                    self.received_message_format(data) # Xử lý tin nhắn

            except ConnectionAbortedError: # Lỗi khi ngắt kết nối (thoát chương trình)
                print("you disconnected ...")
                self.client_socket.close()
                break
            except ConnectionResetError: # Lỗi khi server tắt
                messagebox.showinfo(title='No Connection !', message="Server offline..try connecting again later")
                self.client_socket.close()
                self.first_screen()
                break
    
    # Sự kiện thoát
    def on_closing(self):
        if self.window == 'ChatScreen': # Khi đã kết nối client vào server
            res = messagebox.askyesno(title='Warning !',message="Do you really want to disconnect ?")
            if res: # Nếu chọn yes
                self.client_socket.close()
                self.first_screen()
        else:
            self.parent.destroy()

    # Xử lý nhận tin nhắn
    def received_message_format(self, data):
        # Nhận thông tin tin nhắn
        name = data['name']
        message = data['message']
        from_ = data['from']

        # Lấy thông tin dữ liệu ảnh từ thông tin Client
        sender_image = self.clients_connected[from_][1]
        sender_image_extension = self.clients_connected[from_][2]

        # Lưu ảnh ra file 
        with open(f"{from_}.{sender_image_extension}", 'wb') as f:
            f.write(sender_image)

        # Lấy dữ liệu ảnh
        im = Image.open(f"{from_}.{sender_image_extension}")
        im = im.resize((40, 40), Image.LANCZOS)
        im = ImageTk.PhotoImage(im)

        # Cấu hình giao diện nhận tin nhắn
        m_frame = tk.Frame(self.scrollable_frame, bg="#595656")

        m_frame.columnconfigure(1, weight=1)

        n_label = tk.Label(m_frame, bg="#595656",fg="white", text= name, font="lucida 7 bold",
                           justify="left", anchor="w")
        n_label.grid(row=0, column=1, padx=2, sticky="w")
        t_label = tk.Label(m_frame, bg="#595656",fg="white", text=datetime.now().strftime('%H:%M'), font="lucida 7 bold",
                           justify="left", anchor="w")
        t_label.grid(row=2, column=1, padx=2, sticky="w")

        m_label = tk.Label(m_frame, wraplength=250,fg="black", bg="#c5c7c9", text=message, font="lucida 9 bold", justify="left",
                           anchor="w")
        m_label.grid(row=1, column=1, padx=2, pady=2, sticky="w")
        
        i_label = tk.Label(m_frame, bg="#595656", image=im, bd=0)
        i_label.image = im
        i_label.grid(row=0, column=0, rowspan=4)

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    # Xử lý gửi tin nhắn
    def sent_message_format(self, event=None):
        name = self.parent.user
        message = self.entry.get('1.0', 'end-1c') # Lấy toàn bộ nội dung text

        if message:
            if event:
                message = message.strip()
            self.entry.delete("1.0", "end-1c") # Xóa text

            # Gửi thông tin tin nhắn tới Server
            from_ = self.user_id
            data = {'from': from_, 'message': message, 'name': name}
            data_bytes = pickle.dumps(data)
            self.client_socket.send(data_bytes)
            
            # Cấu hình giao diện tin nhắn được gửi
            m_frame = tk.Frame(self.scrollable_frame, bg="#595656")

            m_frame.columnconfigure(0, weight=1) # Cấu hình cột 0 trong m_frame ưu tiên mở rộng hoặc co lại

            n_label = tk.Label(m_frame, bg="#595656", fg="white", text=name,
                               font="lucida 7 bold", justify="right", anchor="e")
            n_label.grid(row=0, column=0, padx=2, sticky="e")

            t_label = tk.Label(m_frame, bg="#595656", fg="white", text=datetime.now().strftime('%H:%M'),
                               font="lucida 7 bold", justify="right", anchor="e")
            t_label.grid(row=2, column=0, padx=2, sticky="e")

            m_label = tk.Label(m_frame, wraplength=250, text=message, fg="black", bg="#40C961",
                               font="lucida 9 bold", justify="left",
                               anchor="e")
            m_label.grid(row=1, column=0, padx=2, pady=2, sticky="e")

            i_label = tk.Label(m_frame, bg="#595656", image=self.user_image)
            i_label.image = self.user_image
            i_label.grid(row=0, column=1, rowspan=4, sticky="e")

            m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

            self.canvas.update_idletasks() # Cập nhật giao diện chat khi tin nhắn gửi lên
            self.canvas.yview_moveto(1.0)

    # Xử lý thông báo tham gia hay rời đi của 1 Client
    def notification_format(self, data):
        if data['n_type'] == 'joined': # Nếu có người dùng mới tham gia
            name = data['name']
            image = data['image_bytes']
            extension = data['extension']
            message = data['message']
            client_id = data['id']
            
            # Thêm thông tin Client mới vào danh sách kết nối
            self.clients_connected[client_id] = (name, image, extension)
            # Xử lý sự kiện có Client tham gia
            self.clients_online([client_id, name, image, extension])

        elif data['n_type'] == 'left': # Nếu có người dùng rời đi
            client_id = data['id']
            message = data['message']
            # Xử lý sự kiện có Client rời đi
            self.remove_labels(client_id)
            # Xóa Client ra khỏi danh sách kết nối
            del self.clients_connected[client_id]

        m_frame = tk.Frame(self.scrollable_frame, bg="#595656")

        t_label = tk.Label(m_frame, fg="white", bg="#595656", text=datetime.now().strftime('%H:%M'),
                           font="lucida 9 bold")
        t_label.pack()

        m_label = tk.Label(m_frame, wraplength=250, text=message, font="lucida 10 bold", justify="left", bg="sky blue")
        m_label.pack()

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    # Sự kiện có Client tham gia
    def clients_online(self, new_added):
        if not new_added:
            # NOTE: Xảy ra khi người dùng mới đăng nhập và phải tạo danh sách những người đang tham gia
            for user_id in self.clients_connected:
                # Lấy thông tin các Client đang tham gia
                name = self.clients_connected[user_id][0]
                image_bytes = self.clients_connected[user_id][1]
                extension = self.clients_connected[user_id][2]

                # Lưu lại ảnh của từng Client tham gia
                with open(f"{user_id}.{extension}", 'wb') as f:
                    f.write(image_bytes)

                # Cấu hình giao diện danh sách Client tham gia
                user = Image.open(f"{user_id}.{extension}")
                user = user.resize((45, 45), Image.LANCZOS)
                user = ImageTk.PhotoImage(user)

                b = tk.Label(self, image=user, text=name, compound="left",fg="white", bg="#2b2b2b", font="lucida 10 bold", padx=20, width=80)
                b.image = user
                self.clients_online_labels[user_id] = (b, self.y)

                b.place(x=530, y=self.y)
                self.y += 60
        else:
            # NOTE: Xảy ra khi Client được Server thông báo có Client mới tham gia
            # Lấy thông tin Client mới tham gia
            user_id = new_added[0]
            name = new_added[1]
            image_bytes = new_added[2]
            extension = new_added[3]

            with open(f"{user_id}.{extension}", 'wb') as f:
                f.write(image_bytes)

            # Thêm giao diện Client mới vào giao diện danh sách các Client tham gia
            user = Image.open(f"{user_id}.{extension}")
            user = user.resize((45, 45), Image.LANCZOS)
            user = ImageTk.PhotoImage(user)

            b = tk.Label(self, image=user, text=name, compound="left", fg="white", bg="#2b2b2b",
                         font="lucida 10 bold", padx=15)
            b.image = user
            self.clients_online_labels[user_id] = (b, self.y)

            b.place(x=500, y=self.y)
            self.y += 60

    # Sự kiện có Client rời đi
    def remove_labels(self, client_id):
        for user_id in self.clients_online_labels.copy():
            b = self.clients_online_labels[user_id][0]
            y_co = self.clients_online_labels[user_id][1]
            if user_id == client_id:
                b.destroy()
                del self.clients_online_labels[client_id]
                self.y -= 60
            elif user_id > client_id:
                y_co -= 60
                b.place(x=500, y=y_co)
                self.clients_online_labels[user_id] = (b, y_co)

    # Chèn biểu cảm vào tin nhắn
    def insert_emoji(self, x):
        self.entry.insert("end-1c", x.widget['text']) # Chèn vào cuối

    # Quay về FirstScreen khi thoát
    def first_screen(self):
        self.destroy()
        self.parent.geometry(f"550x400+{self.parent.x_co}+{self.parent.y_co}")
        self.parent.first_frame.pack(fill="both", expand=True)
        self.window = None


FirstScreen()