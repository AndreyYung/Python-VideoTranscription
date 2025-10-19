# USBKey.py
import datetime
import threading
import time

from PyQt6.QtCore import QObject, pyqtSignal

import os
import win32file
import win32api
import wmi

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from base64 import b64decode
from cryptography.hazmat.primitives import padding


class USBKey(QObject):

    usb_disconnected_or_connected = pyqtSignal()  # Сигнал для передачи сообщения

    def __init__(self):
        super().__init__()
        # Информация ключа
        self.decrypted_info = {}
        # Запуск мониторинга USB в фоновом потоке
        usb_thread = threading.Thread(target=self.usb_monitor, daemon=True)
        usb_thread.start()


    def decrypt_key(self, encrypted_data):
        try:
            # Декодируем данные из base64
            encrypted_data = b64decode(encrypted_data)

            # Создаем дешифратор
            cipher = Cipher(algorithms.AES(b"thisisaverysecretkey123456789012"), modes.CBC(b"thisisinitialvec"),
                            backend=default_backend())
            decryptor = cipher.decryptor()

            # Дешифруем данные
            decrypted_padded = decryptor.update(encrypted_data) + decryptor.finalize()

            # Удаляем дополнение
            unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
            decrypted_data = unpadder.update(decrypted_padded) + unpadder.finalize()

            name, organization, expiration_date, access_level, serial_number = decrypted_data.decode('utf-8').split('#')

            # Сохранение информации
            self.decrypted_info = {
                "name": name,
                "organization": organization,
                "expiration_date": expiration_date,
                "access_level": access_level,
                "serial_number": serial_number
            }

            return True
        except Exception as e:
            print(f"Ошибка расшифровки: {e}")
            return False

    def get_drive_serial(self, drive_letter):
        wmi_context = wmi.WMI()
        # Получаем список USB устройств
        for usb in wmi_context.query("SELECT * FROM Win32_DiskDrive WHERE InterfaceType='USB'"):
            # Перебираем ассоциации дисков и логических разделов
            for partition in usb.associators("Win32_DiskDriveToDiskPartition"):
                for logical_disk in partition.associators("Win32_LogicalDiskToPartition"):
                    if logical_disk.Caption == drive_letter.strip("\\"):
                        return usb.PNPDeviceID.split('\\')[-1]  # Возвращаем последнюю часть PNPDeviceID

        return 'Unknown'  # Возвращаем 'Unknown', если не найдено

    def find_key(self):
        self.decrypted_info = {}
        drives = win32api.GetLogicalDriveStrings()
        drives = drives.split('\000')[:-1]
        key_found = False

        for drive in drives:
            if win32file.GetDriveType(drive) == win32file.DRIVE_REMOVABLE:
                key_file_path = os.path.join(drive, 'key.txt')
                if os.path.exists(key_file_path):
                    serial_number = self.get_drive_serial(drive)  # Получаем серийный номер в HEX
                    print(f"Найден ключ на устройстве {drive} серийный номер: {serial_number}")

                    with open(key_file_path, 'r') as file:
                        encrypted_data = file.read().strip()

                        # Расшифровка данных
                        success = self.decrypt_key(encrypted_data)
                        # Получение серийного номера флешки
                        serial_number = self.get_drive_serial(drive)

                        # Получение текущей даты
                        current_date = datetime.datetime.now().date()

                        # Проверка, что серийный ключ в файле и сама флешка совпадают и что срок не истек при удачной расшифровке
                        if success and self.decrypted_info["serial_number"] == serial_number and datetime.datetime.strptime(self.decrypted_info['expiration_date'], '%Y-%m-%d').date() >= current_date:
                            print("Ключ-флешка действительна")
                            key_found = True
                        else:
                            print("Ключ-флешка не действительна")
                else:
                    print(f"Файл ключа не найден на устройстве {drive}")
            else:
                print(f"Устройство {drive} не является съемным носителем")

        return key_found

    # Функция для мониторинга подключения и отключения USB-накопителей
    def usb_monitor(self):
        # Получаем список всех логических дисков на момент начала мониторинга
        previous_drives = set(win32api.GetLogicalDriveStrings().split('\000')[:-1])

        # Бесконечный цикл для постоянного мониторинга изменений в списках дисков
        while True:
            try:
                # Получаем текущий список всех логических дисков
                current_drives = set(win32api.GetLogicalDriveStrings().split('\000')[:-1])

                # Вычисляем, какие диски были добавлены или удалены
                added_drives = current_drives - previous_drives
                removed_drives = previous_drives - current_drives

                # Если были добавлены или удалены диски, эмитим сигнал о смене состояния подключения
                if added_drives or removed_drives:
                    self.usb_disconnected_or_connected.emit()

                # Обновляем список предыдущих дисков для следующего цикла
                previous_drives = current_drives

                # Задержка между проверками, чтобы избежать чрезмерной нагрузки на процессор
                time.sleep(1)

            # Обработка исключений, возникающих при работе с API Windows
            except Exception as e:
                print(f"Ошибка при мониторинге USB: {e}")







