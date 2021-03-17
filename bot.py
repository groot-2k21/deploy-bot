import telebot
from bot_config import *
from bot_check import *
from datetime import datetime


bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start', 'help'])
def start_message(message):
    """Обработка команд"""
    resp = """
    Я умею обновлять комплексы.

    Для этого мне нужно одной строкой передать три параметра через пробел:
    - update -- команда
    - <hostname|ipaddress> -- хостнэйм или IP адрес
    - <url_link_архива_с_обновлением> -- ссылка на архив.
    
    Пример: update klba008-pc1.da http://teamcity.dev.local/artifacts/kop/kop.1.21_RC5_build_900.tar.xz"""
    bot.send_message(message.chat.id, resp)


@bot.message_handler(content_types=['text'])
def get_params(message):
    """Обработка ответа пользователя"""

    # проверка отправителя
    true_chat = check_deploy_group(message.chat.id, conf_accept_group)
    if not true_chat:
        bot.send_message(message.chat.id, "Я тебя не знаю. Уходи.")
        return

    try:
        command, host, url = message.text.split()
        archive = url.split("/")[-1]

        true_command = check_correct_bor_command(command)
        if not true_command:
            bot.send_message(message.chat.id,
                             f"Я не понял вашу команду <i><b>{command}</b></i>.\nУточнить поддерживаемые команды /help",
                             parse_mode="HTML")
            return

        # комплекс сейчас онлайн
        is_online = check_complex_is_online(host)
        if not is_online:
            bot.send_message(message.chat.id, f"<i><b>{host}</b></i> сейчас не доступен. Попробуйте позже.",
                             parse_mode="HTML")
            return

        url_correct = check_url(url)
        if not url_correct:
            bot.send_message(message.chat.id,
                             f"<i><b>{archive}</b></i> не найден.\nПроверьте имя архива и пробуйте еще раз.",
                             parse_mode="HTML")
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        resp = f'''***
        * ОБНОВЛЕНИЕ КОМПЛЕКСА
        * {now}
        * комлпекс: {host}
        * сборка: {archive}
        ***'''
        bot.send_message(message.chat.id, resp)

        # шаг первый
        update_step1(message, host, url, archive)

    except ValueError:
        resp = "Задано неверное кол-во аргументов. Подробнее по команде /help."
        bot.send_message(message.chat.id, resp)


# первый шаг в обновлении комплекса
def update_step1(message, host, url, archive):
    status = "[---]"
    resp1 = "STEP1: Подготавливаю файл с инструкциями для комплекса.\nSTATUS: "
    msg = bot.send_message(message.chat.id, resp1 + status)

    # подготавливаем файл с инструкциями для комплекса
    txt = f'''
    #!/bin/bash
    cd /tmp
    wget -c {url}
    tar -xJf {archive} -C /opt
    cd /opt/ptolemey/Complex/migrate/
    ./migrate > /tmp/{host}.update.log'''

    try:
        with open(f"/tmp/{host}.update", "w") as f:
            f.write(txt)
        status = "[OK]"
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=resp1 + status)

        # переходим к шагу 2
        update_step2(message, host, url, archive)
    except IOError:
        status = "[ERROR]"
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=resp1 + status)


def update_step2(message, host, url, archive):
    status = "[---]"
    resp2 = "STEP2: Передаю файл с интсрукциями на комплекс.\nSTATUS: "
    msg = bot.send_message(message.chat.id, resp2 + status)

    cmd = f"scp -o StrictHostKeyChecking=no -i $(pwd)/deploy.rsa /tmp/{host}.update root@{host}:/tmp/{host}.update"
    code = subprocess.call(cmd, shell=True)
    if code == 0:
        status = "[OK]"
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=resp2 + status)
        # переходим к шагу 3
        update_step3(message, host, url, archive)
    else:
        status = "[ERROR]"
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=resp2 + status)


def update_step3(message, host, url, archive):
    status = "[---]"
    resp3 = "STEP3: Выполняю файл с интсрукциями на комплексе.\nSTATUS: "
    msg = bot.send_message(message.chat.id, resp3 + status)

    cmd = f"ssh -o StrictHostKeyChecking=no -i /$(pwd)/deploy.rsa root@{host} /bin/bash /tmp/{host}.update"
    code = subprocess.call(cmd, shell=True)
    if code == 0:
        status = "[OK]"
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=resp3 + status)
        # переходим к шагу 4
        update_step4(message, host, url, archive)
    else:
        status = "[ERROR]"
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=resp3 + status)


def update_step4(message, host, url, archive):
    status = "[---]"
    resp4 = f"STEP4: Получаю лог обновления с комплкса.{host}\nSTATUS: "
    msg = bot.send_message(message.chat.id, resp4 + status)

    cmd = f"scp -o StrictHostKeyChecking=no -i /$(pwd)/deploy.rsa root@{host}:/tmp/{host}.update.log /tmp/{host}.update.log"
    code = subprocess.call(cmd, shell=True)
    if code == 0:
        status = "[OK]"
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=resp4 + status)

        log_file = f"/tmp/{host}.update.log"
        log = open(log_file, "rb")
        bot.send_document(message.chat.id, log)

    else:
        status = "[ERROR]"
        bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=resp4 + status)

bot.polling()
