import socket
import subprocess

def check_correct_bor_command(command):
    """Проверка корректности команды для бота"""
    return True if command == "update" else False


def check_complex_is_online(host):
    """Проверка доступности 22-го порта на обновляемом комплексе."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, 22))
    sock.close()
    return False if result else True


def check_deploy_group(chat_id, accept_group):
    """Проверка отправителя сообщения. Сообщения принимаются только из определенной группы"""
    return True if str(chat_id) == accept_group else False


def check_url(url):
    """Проверка доступности архива с обновлением"""
    cmd = f'curl -I {url} 2>/dev/null | head -n 1 | cut -d" " -f2'
    code = int(subprocess.check_output(cmd, shell=True))
    return True if code == 200 else False
