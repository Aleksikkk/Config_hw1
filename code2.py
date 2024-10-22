import os
import zipfile
import chardet
import yaml
import xml.etree.ElementTree as ET
from datetime import datetime


class ShellEmulator:
    def __init__(self, config):
        self.username = config['username']
        self.hostname = config['hostname']
        self.vfs_path = config['vfs_path']
        self.log_path = config['log_path']
        self.startup_script = config['startup_script']
        self.current_directory = "vfs"
        self.commands = {
            'ls': self.ls,
            'cd': self.cd,
            'exit': self.exit,
            'rmdir': self.rmdir,
            'tail': self.tail,
            'cat': self.cat
        }

    def log_creation(self):
        root = ET.Element("log")
        tree = ET.ElementTree(root)
        tree.write(self.log_path)

    def log_action(self, action):
        tree = ET.parse(self.log_path)
        root = tree.getroot()
        time = ET.SubElement(root, "time")
        entry = ET.SubElement(time, "entry")
        date = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
        time.text = date
        entry.text = f"{self.username} executed: {action}"
        tree.write(self.log_path)

    def ls(self):
        with zipfile.ZipFile(self.vfs_path, 'r') as zipf:
            for info in zipf.infolist():
                if info.filename.startswith(self.current_directory + '/') and not info.filename.endswith('/'): #Исключаем пустые директории
                    print(info.filename)
        self.log_action("ls")

    def cd(self, path):
        if path.startswith('/'):
            new_path = path[1:]
        else:
            new_path = self.abspath(path)

        try:
            with zipfile.ZipFile(self.vfs_path, 'r') as zip:
                if any(member == new_path + '/' for member in zip.namelist()):
                    self.current_directory = new_path
                    self.log_action(f"cd {path}")
                else:
                    print(f"Директория '{path}' не найдена.")
        except Exception as e:
            print(f"Ошибка при выполнении cd: {e}")

    def exit(self):
        self.log_action("exit")
        print("Выход...")
        exit(0)

    def cat(self, path):
        file_path = self.abspath(path)
        vfs_path = self.vfs_path

        if not os.path.exists(vfs_path):
            print(f"Ошибка: Файл виртуальной файловой системы '{vfs_path}' не найден.")
            return

        try:
            with zipfile.ZipFile(vfs_path, 'r') as zipf:
                found = False
                for info in zipf.infolist():
                    if info.filename == file_path and not info.is_dir():
                        try:
                            with zipf.open(info) as f:
                                # Автоматическое определение кодировки
                                rawdata = f.read()
                                result = chardet.detect(rawdata)
                                encoding = result['encoding']
                                if encoding is None:
                                    encoding = 'utf-8' # Дефолтная кодировка, если не удалось определить
                                content = rawdata.decode(encoding, errors='ignore') # игнорируем ошибки декодирования

                            print(content)
                            self.log_action(f"cat {path}")
                            found = True
                            break
                        except UnicodeDecodeError as e:
                            print(f"Ошибка декодирования файла '{path}': {e}. Попробуйте указать кодировку.")
                        except zipfile.BadZipFile:
                            print(f"Ошибка: Файл '{vfs_path}' поврежден.")
                            return
                        except Exception as e:
                            print(f"Ошибка при чтении файла '{path}': {e}")
                            break  # Прерываем только при непреодолимой ошибке
                if not found:
                    print(f"Файл '{path}' не найден в архиве '{vfs_path}'.")
        except FileNotFoundError:
            print(f"Ошибка: Файл виртуальной файловой системы '{vfs_path}' не найден.")
        except Exception as e:
            print(f"Непредвиденная ошибка: {e}")
    
    def abspath(self, path):
        return  os.path.normpath(os.path.join(self.current_directory, path)).replace('\\', '/')

    def tail(self, path, n=10): 
        file_path = self.abspath(path)
        with zipfile.ZipFile(self.vfs_path, 'r') as zipf:
            found = False
            for info in zipf.infolist():
                if info.filename == file_path and not info.is_dir():
                    try:
                        content = zipf.read(info).decode('utf-8')
                        lines = content.splitlines()
                        if len(lines) <= n:
                            print('\n'.join(lines))
                        else:
                            print('\n'.join(lines[-n:]))
                        self.log_action(f"tail -n {n} {path}")
                        found = True
                        break
                    except UnicodeDecodeError:
                        print("Ошибка: Не удалось декодировать файл. Возможно, неверная кодировка.")
                        break
                    except Exception as e:
                        print(f"Ошибка при чтении файла: {e}")
                        break

            if not found:
                print(f"Файл '{path}' не найден.")

    def rmdir(self, path):
        checker = 0
        directory_to_remove = self.abspath(path) + '/' # Добавим слеш для корректного сравнения

        with zipfile.ZipFile(self.vfs_path, 'r') as zipf:
            if any(info.filename.startswith(directory_to_remove) for info in zipf.infolist()):
                checker = 1 
            else:
                checker = 2 

        if checker == 2:
            print("Ошибка: директория не существует")
        else:
            temp_zip_path = 'temp.zip'
            with zipfile.ZipFile(self.vfs_path, 'r') as input_zip:
                with zipfile.ZipFile(temp_zip_path, 'w') as output_zip:
                    for info in input_zip.infolist():
                        if not info.filename.startswith(directory_to_remove):
                            output_zip.writestr(info, input_zip.read(info))

            os.remove(self.vfs_path)
            os.rename(temp_zip_path, self.vfs_path)
            self.log_action(f"rmdir {path}")


    def run(self):
        self.log_creation()
        while True:
            command = input(f"{self.username}@{self.hostname}:{self.current_directory}$ ")
            parts = command.split()
            cmd_name = parts[0]
            args = parts[1:]

            if cmd_name in self.commands:
                if args:
                    self.commands[cmd_name](*args)
                else:
                    self.commands[cmd_name]()
            else:
                print(f"Команда '{cmd_name}' не найдена.")

if __name__ == "__main__":
    with open('config1.yaml', 'r') as f:
        config = yaml.safe_load(f)
    emulator = ShellEmulator(config)
    emulator.run()