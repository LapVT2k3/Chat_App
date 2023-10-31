import socket
import time
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
import customtkinter as ctk

# Lấy đường dẫn thư mục chứa file hiện tại
current_dir = os.path.dirname(os.path.abspath(__file__))
SIGNIN = 'signin'
SIGNUP = 'signup'
IP = '192.168.52.100'
PORT = 12345
BUFF_SIZE = 65536

# Thay đổi DPI giúp ứng dụng hiển thị đẹp hơn trên màn hình có độ phân giải cao
try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

class SignIn(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LogIn")
        self.geometry('925x500+300+200')
        self.configure(bg="#fff")
        self.resizable(False, False)
                
        img = Image.open(current_dir + '/images/signIn.png')
        img = ImageTk.PhotoImage(img)
        tk.Label(self, image=img, bg='white').place(x=50, y=50)
        
        self.name = ""
        
        # ---------------------------------------------
        # ---------------------------------------------
        # Một số hàm xử lý sự kiện
        def showFrameSignUp():
            self.signIn_frame.place_forget()
            signUp_frame.place(x=480,y=20)
            
        def showFrameSignIn():
            signUp_frame.place_forget()
            self.signIn_frame.place(x=480,y=70)
            
        def signUp():
            if self.pass_entry1.get() == self.pass_entry2.get():
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
                client_socket.send(SIGNUP.encode('utf-8'))
                data = {'username': self.user_entry1.get(), 'pass': self.pass_entry1.get(), 'name': self.name_entry.get()}
                data_bytes = pickle.dumps(data)
                client_socket.sendall(data_bytes)
                notification = client_socket.recv(1024).decode('utf-8')
                if notification == 'success':
                    messagebox.showinfo(title="Success!", message='Tạo tài khoản thành công')
                elif notification == 'fail':
                    messagebox.showinfo(title="Error!", message='Tài khoản đã tồn tại. Vui lòng sử dụng tên tài khoản khác')
                
                client_socket.close()    
                
            else:
                messagebox.showinfo(title="Error!", message='Mật khẩu không trùng nhau')
                
        def signIn():
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
            client_socket.send(SIGNIN.encode('utf-8'))
            data = {'username': self.user_entry.get(), 'pass': self.pass_entry.get()}
            data_bytes = pickle.dumps(data)
            client_socket.sendall(data_bytes)
            notification = client_socket.recv(1024).decode('utf-8')
            if notification == 'success':
                messagebox.showinfo(title="Success!", message='Đăng nhập thành công')  
                client_socket.send('received'.encode())
            elif notification == 'fail':
                messagebox.showinfo(title="Error!", message='Tài khoản hoặc mật khẩu không chính xác')
                client_socket.close()
                return
            self.name = client_socket.recv(1024).decode('utf-8')
            client_socket.send('received'.encode())
            clients_data_size_bytes = client_socket.recv(1024)
            client_socket.send('received'.encode())
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
            clients_data = pickle.loads(b)

            # Gửi thông báo đã nhận danh sách tới Server
            client_socket.send('data_received'.encode())
            
            # Nhận ID
            user_id = struct.unpack('i', client_socket.recv(1024))[0]
            print(f"{self.name} is user no. {user_id}")
            
            # Mở cửa sổ chat
            ChatScreen(self, self.signIn_frame, client_socket, clients_data, user_id)


        # ----------------------------------
        # ----------------------------------
        # ----------------------------------
        # Frame đăng nhập
        self.signIn_frame = tk.Frame(self, width=350, height=350 ,bg='white')
        self.signIn_frame.place(x=480, y=70)
        
        heading = tk.Label(self.signIn_frame, text='Sign in', fg='#57a1f8', bg='white', font=('Microsoft YaHei UI Light', 23, 'bold'))
        heading.place(x=110, y=5)
        # -----------------------------------------
        def on_enter(e):
            name = self.user_entry.get()
            if name == 'Username':
                self.user_entry.delete(0, 'end')
        
        def on_leave(e):
            name = self.user_entry.get()
            if name == '':
                self.user_entry.insert(0, 'Username')
        
        # Ô nhập tài khoản
        self.user_entry = tk.Entry(self.signIn_frame, width=25, fg='black', border=0, bg='white', font=('Microsoft YaHei UI Light', 11))
        self.user_entry.place(x=30, y=80)
        self.user_entry.insert(0, 'Username')
        self.user_entry.bind('<FocusIn>', on_enter)
        self.user_entry.bind('<FocusOut>', on_leave)
        
        tk.Frame(self.signIn_frame, width=350, height=2, bg='black').place(x=25, y=110)
        
        # -----------------------------------------
        def on_enter(e):
            self.pass_entry.config(show='*')
            name = self.pass_entry.get()
            if name == 'Password':
                self.pass_entry.delete(0, 'end')
        
        def on_leave(e):
            name = self.pass_entry.get()
            if name == '':
                self.pass_entry.config(show='')
                self.pass_entry.insert(0, 'Password')
        
        # Ô nhập mật khẩu
        self.pass_entry = tk.Entry(self.signIn_frame, width=25, fg='black', border=0, bg='white', font=('Microsoft YaHei UI Light', 11))
        self.pass_entry.place(x=30, y=150)
        self.pass_entry.insert(0, 'Password')
        self.pass_entry.bind('<FocusIn>', on_enter)
        self.pass_entry.bind('<FocusOut>', on_leave)
        
        tk.Frame(self.signIn_frame, width=350, height=2, bg='black').place(x=25, y=180)
        
        
        # Button đăng nhập
        tk.Button(self.signIn_frame, width=40, pady=7, text='Sign In', bg='#57a1f8', fg='white', border=0, command=signIn).place(x=35,y=210)
        
        tk.Label(self.signIn_frame, text="Don't have an account?",fg='black',bg='white',font=('Microsoft YaHei UI Light', 9)).place(x=75,y=270)
        
        # Button đăng ký
        tk.Button(self.signIn_frame, width=6,text='Sign Up',border=0,bg='white',cursor='hand2',fg='#57a1f8', command=showFrameSignUp).place(x=245, y=268)
        
        # ----------------------------------
        # ----------------------------------
        # ----------------------------------
        # Frame đăng ký
        signUp_frame = tk.Frame(self, width=350, height=450 ,bg='white')
        
        heading1 = tk.Label(signUp_frame, text='Sign up', fg='#57a1f8', bg='white', font=('Microsoft YaHei UI Light', 23,'bold'))
        heading1.place(x=100,y=5)
        
        # -----------------------------------------
        def on_enter(e):
            name = self.user_entry1.get()
            if name == 'Username':
                self.user_entry1.delete(0, 'end')
        
        def on_leave(e):
            name = self.user_entry1.get()
            if name == '':
                self.user_entry1.insert(0, 'Username')
        
        # Ô nhập tài khoản
        self.user_entry1 = tk.Entry(signUp_frame, width=25, fg='black', border=0, bg='white', font=('Microsoft YaHei UI Light', 11))
        self.user_entry1.place(x=30, y=80)
        self.user_entry1.insert(0, 'Username')
        self.user_entry1.bind('<FocusIn>', on_enter)
        self.user_entry1.bind('<FocusOut>', on_leave)
        
        tk.Frame(signUp_frame, width=350, height=2, bg='black').place(x=25, y=110)
        
        # -------------------------------------------
        def on_enter(e):
            self.pass_entry1.config(show='*')
            name = self.pass_entry1.get()
            if name == 'Password':
                self.pass_entry1.delete(0, 'end')
        
        def on_leave(e):
            name = self.pass_entry1.get()
            if name == '':
                self.pass_entry1.config(show='')
                self.pass_entry1.insert(0, 'Password')
        
        # Ô nhập mật khẩu
        self.pass_entry1 = tk.Entry(signUp_frame, width=25, fg='black', border=0, bg='white', font=('Microsoft YaHei UI Light', 11))
        self.pass_entry1.place(x=30, y=150)
        self.pass_entry1.insert(0, 'Password')
        self.pass_entry1.bind('<FocusIn>', on_enter)
        self.pass_entry1.bind('<FocusOut>', on_leave)
        
        tk.Frame(signUp_frame, width=350, height=2, bg='black').place(x=25, y=180)
        
        # -------------------------------------------
        def on_enter(e):
            self.pass_entry2.config(show='*')
            name = self.pass_entry2.get()
            if name == 'Confirm Password':
                self.pass_entry2.delete(0, 'end')
        
        def on_leave(e):
            name = self.pass_entry2.get()
            if name == '':
                self.pass_entry2.config(show='')
                self.pass_entry2.insert(0, 'Confirm Password')
        
        # Ô nhập lại mật khẩu
        self.pass_entry2 = tk.Entry(signUp_frame, width=25, fg='black', border=0, bg='white', font=('Microsoft YaHei UI Light', 11))
        self.pass_entry2.place(x=30, y=220)
        self.pass_entry2.insert(0, 'Confirm Password')
        self.pass_entry2.bind('<FocusIn>', on_enter)
        self.pass_entry2.bind('<FocusOut>', on_leave)
        
        tk.Frame(signUp_frame, width=350, height=2, bg='black').place(x=25, y=250)
        
        # -------------------------------
        def on_enter(e):
            name = self.name_entry.get()
            if name == 'Name':
                self.name_entry.delete(0, 'end')
        
        def on_leave(e):
            name = self.name_entry.get()
            if name == '':
                self.name_entry.insert(0, 'Name')
        
        # Ô nhập tên người dùng
        self.name_entry = tk.Entry(signUp_frame, width=25, fg='black', border=0, bg='white', font=('Microsoft YaHei UI Light', 11))
        self.name_entry.place(x=30, y=290)
        self.name_entry.insert(0, 'Name')
        self.name_entry.bind('<FocusIn>', on_enter)
        self.name_entry.bind('<FocusOut>', on_leave)
        
        tk.Frame(signUp_frame, width=350, height=2, bg='black').place(x=25, y=320)
        
        # -------------------------------
        # Button đăng ký
        tk.Button(signUp_frame, width=40, pady=7, text='Sign In', bg='#57a1f8', fg='white', border=0, command=signUp).place(x=35,y=350)
        
        tk.Label(signUp_frame, text="Have an account already?",fg='black',bg='white',font=('Microsoft YaHei UI Light', 9)).place(x=75,y=420)
        
        # Button đăng nhập
        tk.Button(signUp_frame, width=6,text='Sign In',border=0,bg='white',cursor='hand2',fg='#57a1f8', command=showFrameSignIn).place(x=255, y=418)
        
        self.mainloop()
        

# Màn hình chat
class ChatScreen(tk.Canvas): # Kế thừa tk.Canvas vẽ các hình ảnh, giao diện và các đối tượng đồ họa khác
    def __init__(self, parent, signIn_frame, client_socket, clients_connected, user_id):
        super().__init__(parent)
        self.window = 'ChatScreen' # Đặt tên để xác định cửa sổ

        self.signIn_frame = signIn_frame
        self.signIn_frame.pack_forget() # Ẩn First Frame

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
        background = Image.open(current_dir + '/images/bg_chat.jpg')
        background = background.resize((1600, 1900), Image.LANCZOS) # Thay đổi kích cỡ và làm mịn ảnh
        background = ImageTk.PhotoImage(background)
        self.create_image(0, 0, image = background)

        # Lấy ảnh người dùng
        user_image = Image.open(current_dir + '/images/user.png')
        user_image = user_image.resize((40, 40), Image.LANCZOS)
        self.user_image = ImageTk.PhotoImage(user_image)

        # Tạo ảnh nhóm
        global group_photo
        group_photo = Image.open(current_dir + '/images/group_ca.png')
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
        send_button.place(x=450, y=688)
        
        
        
        # Cấu hình nút "Send File"
        send_file_button = tk.Button(self, text="Send File", fg="#83eaf7", font="lucida 11 bold", bg="#7d7d7d", padx=10,
                                relief="solid", bd=2, command=self.sent_file_format)
        
        send_file_button.place(x=550,y=688)
        
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

        m_label = tk.Label(m_frame, wraplength=250, text=f"Happy Chatting {self.parent.name}",
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

                elif data_type == 'message':
                    data_bytes = self.client_socket.recv(1024) # Nhận tin nhắn từ client khác
                    data = pickle.loads(data_bytes)
                    self.received_message_format(data) # Xử lý tin nhắn
                elif data_type == 'file':
                    info_sender = pickle.loads(self.client_socket.recv(1024))
                    
                    file_bytes = b""
                    done = False
                    
                    while not done:
                        data = self.client_socket.recv(1024)
                        file_bytes += data
                        if file_bytes[-5:] == b"<END>":
                            done = True
                    file_bytes = file_bytes[:-5]
                    
                    self.received_file_format(info_sender, file_bytes)
                    

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

    # Xử lý gửi tin nhắn
    def sent_message_format(self, event=None):
        name = self.parent.name
        print(name)
        message = self.entry.get('1.0', 'end-1c') # Lấy toàn bộ nội dung text

        if message:
            if event:
                message = message.strip()
            self.entry.delete("1.0", "end-1c") # Xóa text

            self.client_socket.send('message'.encode('utf-8'))
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

    # Xử lý gửi file
    def sent_file_format(self):
        file_path = filedialog.askopenfilename()
        
        if not file_path:
            return
        
        file = open(file_path, 'rb')
        file_name = os.path.basename(file_path)
        
        self.client_socket.send('file'.encode('utf-8'))
        
        name = self.parent.name
        from_ = self.user_id
        self.client_socket.send(pickle.dumps({'from': from_, 'name': name}))
        time.sleep(0.1)
        self.client_socket.send(file_name.encode('utf-8'))
        time.sleep(0.1)
        data = file.read()
        self.client_socket.sendall(data)
        self.client_socket.send(b"<END>")
        
        # Cấu hình giao diện tin nhắn được gửi
        m_frame = tk.Frame(self.scrollable_frame, bg="#595656")

        m_frame.columnconfigure(0, weight=1) # Cấu hình cột 0 trong m_frame ưu tiên mở rộng hoặc co lại

        n_label = tk.Label(m_frame, bg="#595656", fg="white", text=name,
                            font="lucida 7 bold", justify="right", anchor="e")
        n_label.grid(row=0, column=0, padx=2, sticky="e")

        t_label = tk.Label(m_frame, bg="#595656", fg="white", text=datetime.now().strftime('%H:%M'),
                            font="lucida 7 bold", justify="right", anchor="e")
        t_label.grid(row=2, column=0, padx=2, sticky="e")

        m_button = tk.Button(m_frame, text=file_name, fg="black", bg="#40C961",
                            font="lucida 9 bold", justify="left", cursor='hand2',
                            anchor="e", command=lambda: self.download_file(file_name, data))
        m_button.grid(row=1, column=0, padx=2, pady=2, sticky="e")

        i_label = tk.Label(m_frame, bg="#595656", image=self.user_image)
        i_label.image = self.user_image
        i_label.grid(row=0, column=1, rowspan=4, sticky="e")

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.canvas.update_idletasks() # Cập nhật giao diện chat khi tin nhắn gửi lên
        self.canvas.yview_moveto(1.0)
     
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
     
    # Xử lý nhận file
    def received_file_format(self, info_sender, file_bytes): 
        from_ = info_sender['from']
        name = info_sender['name']
        file_name = info_sender['file_name']    
        
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
        
        m_button = tk.Button(m_frame, text=file_name, fg="black", bg="#c5c7c9",
                            font="lucida 9 bold", justify="left", cursor='hand2',
                            anchor="w", command=lambda: self.download_file(file_name, file_bytes))
        m_button.grid(row=1, column=1, padx=2, pady=2, sticky="w")
        
        i_label = tk.Label(m_frame, bg="#595656", image=im, bd=0)
        i_label.image = im
        i_label.grid(row=0, column=0, rowspan=4)

        m_frame.pack(pady=10, padx=10, fill="x", expand=True, anchor="e")

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0) 
        
    
    # Xử lý tải file    
    def download_file(self, file_name, data):
        folder_path = filedialog.askdirectory()
        
        if not folder_path:
            return
        
        file = open(folder_path + '/' + file_name, 'wb')
        file.write(data)
        file.close()
        messagebox.showinfo(title="Successful!", message='Tải file thành công')
        
    
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

                b = tk.Label(self, image=user, text=name, compound="left",fg="white", bg="#2b2b2b", font="lucida 10 bold",
                     padx=15, width=100, justify="left", anchor='w')
                b.grid(row=self.y, column=0, sticky="w")
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
                         font="lucida 10 bold", padx=15, width=100, justify='left', anchor='w')
            b.image = user
            self.clients_online_labels[user_id] = (b, self.y)

            b.place(x=530, y=self.y)
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
        self.parent.geometry('925x500+300+200')
        self.parent.signIn_frame.place(x=480,y=70)
        self.window = None

SignIn()