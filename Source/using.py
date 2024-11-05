from mail_client import MailClient
from console import menu, send_mail_console, mail_boxes_console, mail_box_console, mail_content_console, display_files_console
import yaml
import os
from constants import mail_boxes_dict
from utils import read_mail_boxes
import json
import time
import threading

with open('config.yml', encoding='utf-8') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
    
bufferSize = config['Server']['bufferSize']
smtpServer = config['Server']['MailServer']
smtp_port = config['Server']['SMTP']
pop3_port = config['Server']['POP3']
username = config['Authentication']['username']
password = config['Authentication']['password']
filter = config['Filter']



def load_menu():
    while True:
        os.system('cls')
        menu(username)
        choice = input('Your choice: ')
        if choice == '1':
            os.system('cls')
            mail_client.connect()
            subject, message, from_addr, to_addr, cc_addr, bcc_addr, attach_files = send_mail_console()
            try:
                mail_client.send_mail(subject, message, from_addr, to_addr, cc_addr, bcc_addr, attach_files)
                print('Send mail successfully!\n')
                os.system('pause')
            except:
                print('Send mail failed!\n')
                os.system('pause')
        if choice == '2':
            os.system('cls')
            print('=====Download mail=====')
            try:
                mail_client.authenticate(username)
                mail_client.download_mail(username)
                print('\nDownload mail successfully!\n')
                os.system('pause')
            except:
                print('\nDownload mail failed!\n')
                os.system('pause')
        if choice == '3':
            os.system('cls')
            mail_dict = read_mail_boxes(username)
            if mail_dict == -1:
                continue
            while True:
                os.system('cls')
                mail_boxes_console()
                mail_boxes_choice = input('Your choice: ')
                while mail_boxes_choice not in ['0', '1', '2', '3', '4', '']:
                    print('Invalid choice!')
                    mail_boxes_choice = input('Your choice: ')
                if mail_boxes_choice == '':
                    break
                while True:
                    os.system('cls')
                    box_index = mail_boxes_dict[int(mail_boxes_choice)]
                    mail_box_console(mail_dict[box_index])
                    mail_box_choice = input('Your choice: ')
                    if mail_box_choice == '':
                        break
                    mail_index = int(mail_box_choice)
                    os.system('cls')
                    mail_content_console(mail_dict[box_index][mail_index])
                    #save read status
                    mail_dict[box_index][mail_index]['READ'] = True
                    with open(f'mail_boxes/{username}/{box_index}/{mail_dict[box_index][mail_index]["NAME_MAIL_FILE"]}', 'w') as f:
                        mail_dict[box_index][mail_index].pop('NAME_MAIL_FILE')
                        json.dump(mail_dict[box_index][mail_index], f)
                    # print('Do you want to download attachment files?\n')
                    # attach_choice = input('Y/Yes - N/No: ')
                    # if attach_choice in ['Y', 'Yes', 'y', 'yes']:
                    #     all_files = mail_dict[box_index][mail_index]['FILES'].split(', ')
                    #     if all_files == []:
                    #         print('\nThere is not file here!\n')
                    #     else:
                    #         display_files_console(all_files)
                    #         down_file_choice = input('Your choice: ')
                    #         mail_client.download_attachment(down_file_choice)
                    #         print('\nDownload attachment files successfully!\n')
                    os.system('pause')
                    # display_mail
def auto_download_mail():
    autoload_time = config.get('Autoload', {}).get('Time', 5)
    time.sleep(autoload_time)
    while True:
        # print('Downloading mail...')
        mail_client.authenticate(username)
        mail_client.download_mail(username)
        time.sleep(autoload_time)
       

if __name__ == '__main__':
    mail_client = MailClient(smtpServer, smtp_port, pop3_port, filter, bufferSize)
    mail_client.connect()

    t1 = threading.Thread(target=load_menu)
    t2 = threading.Thread(target=auto_download_mail)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

# mail_client.send_mail('this is subject', 'this is a message', 'tuannhat@gmail.com', ['tn','tn1','tn2'], ['nhat.jpg', 'xstktl.pdf'])
# mail_client.authenticate('tuannhat1209@gmail.com')
# mail_client.download_mail('tuannhat1209@gmail.com')