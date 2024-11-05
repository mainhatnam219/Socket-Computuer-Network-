from socket import *
import base64
from utils import extract_mail, filter, create_folder, current_mail_number_on_local
import json
from datetime import datetime
import os

class MailClient:
	def __init__(self, host, smtp_port, pop3_port, filter, bufferSize=1024):
		self.host = host
		self.smtp_port = smtp_port
		self.pop3_port = pop3_port
		self.filter = filter
		self.bufferSize = bufferSize

	def connect(self):
		self.smtp_socket = socket(AF_INET, SOCK_STREAM)
		print('Connecting to SMTP server...')
		self.smtp_socket.connect((self.host, self.smtp_port))

		self.pop3_socket = socket(AF_INET, SOCK_STREAM)
		print('Connecting to POP3 server...')
		self.pop3_socket.connect((self.host, self.pop3_port))
		self.respone(self.pop3_socket)

	def respone(self, server):
		try:
			recv = ''
			while True:
				part = server.recv(self.bufferSize)
				recv += part.decode()
				if len(part) < self.bufferSize:
					break
			return recv
		except timeout:
			pass

	def request(self, server, message, expect_return_msg=True, display_msg=True):
		server.send(f'{message}\r\n'.encode())
		if expect_return_msg:
			recv = self.respone(server)
			if display_msg: 
				print(recv)
			return recv

	def quit(self):
		return self.request('QUIT')

	#SMTP
	def login(self, user: str, password: str):
		str = '\x00' + user + '\x00' + password
		base64_str = base64.b64encode(str.encode())
		auth_msg = 'AUTH PLAIN ' + base64_str.decode()
		self.request(self.smtp_socket, auth_msg)

	def send_mail(self, sjt, msg, from_addr, to_addr, cc_addr, bcc_addr, attach_file=None):
		self.request(self.smtp_socket, f'MAIL FROM:<{from_addr}>', expect_return_msg=False)
		for addr in (to_addr + cc_addr) if cc_addr != [] else to_addr:
			self.request(self.smtp_socket, f'RCPT TO:<{addr}>', expect_return_msg=False)
		for addr in bcc_addr:
			self.request(self.smtp_socket, f'RCPT TO:<{addr}>',expect_return_msg=False)
			
		self.request(self.smtp_socket, f'DATA', expect_return_msg=False)
		self.request(self.smtp_socket, f'DATE: {datetime.today().strftime("%Y-%m-%d %H:%M:%S")}', expect_return_msg=False)
		self.request(self.smtp_socket, f'FROM: {from_addr}', expect_return_msg=False)
		self.request(self.smtp_socket, f'TO: {", ".join(to_addr)}', expect_return_msg=False)
		self.request(self.smtp_socket, f'CC: {", ".join(cc_addr)}', expect_return_msg=False)
		self.request(self.smtp_socket, f'SUBJECT: {sjt}', expect_return_msg=False)
		self.request(self.smtp_socket, f'CONTENT: {msg}', expect_return_msg=False)
		if attach_file:
			self.request(self.smtp_socket, f'FILES: {", ".join(attach_file)}', expect_return_msg=False)
			for file in attach_file:
				with open(file, 'rb') as f:
					l = f.read(self.bufferSize)
					l = base64.b64encode(l)
					self.request(self.smtp_socket, f'ATTACH: {file}: {l}', expect_return_msg=False)
					while l:
						l = f.read(self.bufferSize)
						l = base64.b64encode(l)
						self.request(self.smtp_socket, l, expect_return_msg=False)
		self.request(self.smtp_socket, '.', expect_return_msg=False)

	#POP3
	def authenticate(self, user):
		
		# print("Sent: USER " + user)
		self.request(self.pop3_socket, "USER " + user, display_msg=False)
		
	def current_mail_number_on_server(self):
		# print("Sent: STAT")
		number = self.request(self.pop3_socket, "STAT", display_msg=False)
		number = int(number.split(' ')[1])
		return number
	def save_files(self, path, files):
		for file in files:
			if file['data'] != '':
				f = open(path + '/downloaded_' + file['name'], 'wb')
				encoded = bytes(file['data'], 'ascii')
				fdata = base64.b64decode(encoded)
				f.write(fdata)
				f.close()

	def download_mail(self, user):
		create_folder(user)

		current_on_local = current_mail_number_on_local(user) # số lượng mail trên local

		current_on_server = self.current_mail_number_on_server() # số lượng mail trên server

		for i in range(current_on_local, current_on_server + 1):
			# print("Sent: RETR " + str(i))
			recv = self.request(self.pop3_socket, "RETR " + str(i), display_msg=False)
			# print('Get mail successfully')

			dict = extract_mail(recv)
			folder = filter(dict, self.filter)

			for each_folder in folder:
				self.save_files(f'mail_boxes/{user}/{each_folder}', dict['FILES'])
				with open(f'mail_boxes/{user}/{each_folder}/mail{i}.json', 'w') as f:
					#json dump file without dict['FILES]
					dict['FILES'] = ', '.join(files['name'] for files in dict['FILES'])
					# dict.pop('FILES')
					json.dump(dict, f)
	def get_mail_boxes(self):
		current_on_server = self.current_mail_number_on_server()
		dict_list = []
		for i in range(1, current_on_server + 1):
			# print("Sent: RETR " + str(i))
			recv = self.request(self.pop3_socket, "RETR " + str(i), display_msg=False)
			# print('Get mail successfully')
			dict_list.append(extract_mail(recv))
		return dict_list

