# settings for backup.py

from time import localtime, strftime
from app.helper import USER_DATA_DIRECTORY

sub_folder_name = strftime("%Y_%m_%d_%H%M%S", localtime())

now = strftime("%Y-%m-%d %H:%M:%S", localtime())

backup_items = [
    USER_DATA_DIRECTORY
]

mailing_list = [
    'anyemail@contoso.com',
    'dtrump@sux.com',
]

ignore_extensions = ['*.py', '*.pyc', '*.log']

target_folder = 'Backup'

send_mail = False

mail_settings = {
    'server'		: 'smtp.live.com',
    'port'			: 25,
    'mail_address'	: 'myemail@live.com',
    'username'		: 'myemail@live.com',
    'password'		: 'NeverForget@2017',
    'tls'			: True,
}

mail_subject = 'Backup. {0}'

mail_body = '''
Backup System
	Backup Performed at:	{0}
	Backup Items:	{1}
	Destination folder:	{2}
'''