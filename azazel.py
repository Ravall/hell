# -*- coding: utf-8 -*-
import logging
import time
import os
import re
from daemon import runner
from sets import Set

_PATH = '/home/web/django_admin'
LOG_PATH = '/home/var/log/hell'
PID_PATH = '/home/var/run/hell'

class Azazel():
    '''
    демон азазель, синхронизирует и ресайзит изображения.
    проверяет изменение в папке origin (новые и удаленные изображения)
    и раскидывает кропнутые изображения по нужным папкам

    нужные папки - это папки формата 000x000 находящиеся в папке crop
                и папки в из дополнительного списка add_sync_folders
    настройка
        origin_folder - оригинальная папка
        sync_folder куда нужно синхронизировать
        add_sync_folders - дополнительные папки
        pidfile_path - путь к pid файлу
        file_save_last_sync_data файл в котором хранится отметка о последней
                                 синхронизации демоном
        LOG_PATH - путь к лог файлу
        PID_PATH - путь к pid файлу
    '''

    #папка куда нужно синхронизировать
    sync_folder = os.path.abspath(
        os.path.join(_PATH, 'files', 'media', 'crop'))
    # файл в котором храним время
    # последней синхронизации
    file_save_last_sync_data = PID_PATH + "/last_update"
    # папка откуда берем изображения,
    # которые нужно синхронизировать
    origin_folder = os.path.abspath(
        os.path.join(_PATH, 'files', 'media', 'origin'))
    #дополнительные папки, куда нужно
    #синхронизировать изображения
    add_sync_folders = []
    pidfile_path = PID_PATH + '/azazel.pid'
    stdin_path = '/dev/null'
    stdout_path = '/dev/tty'
    stderr_path = '/dev/tty'
    pidfile_timeout = 5

    def __init__(self):
        self.last_time_update = self.get_last_sync_date()

    def get_last_update_origin_folder(self):
        '''
        считываем время последнего изменения оригинальной папки
        '''
        last_update = str(os.path.getmtime(self.origin_folder))
        return last_update

    def set_last_update(self, time):
        '''
        записываем в файл время последней синхронизации
        '''
        # сохраним отметку синхронизации
        self.last_time_update = time
        # запишем в файл
        f = open(self.file_save_last_sync_data, 'w')
        f.write(str(time))
        f.close()

    def get_last_sync_date(self):
        '''
        берем время последней синхронизации из файла
        '''
        f = open(self.file_save_last_sync_data, 'r')
        last_sync = f.read()
        f.close()
        return last_sync

    def get_folders_to_sync(self):
        '''
        получаем список папок, куда нужно синхронизавть.
        список берем из dir (где храняться кропнутые изображения)
        добавляем дополнительные папки
        (мало-ли, если придется синхронизировать куда-нибудь кроме этого)
        из списка берем только те которые удовлетвояют виду 000x000
        '''
        folders = map(
            lambda folder_name: self.sync_folder + '/' + folder_name,
            os.listdir(self.sync_folder)) + self.add_sync_folders
        logger.info("folders list:" + str(folders))
        return filter(
            lambda folder: re.match('^\d{,4}x\d{,4}$', folder.split('/')[-1]),
            folders)

    def folder_sync(self, folder):
        '''
        синхронизатор папки. Для папки, мы проходимся и смотрим
        какие файлы появились в оригинальной и их нужно синхронизировать,
        какие нужно удалить - если они есть в синхронизируемой, но отсутсвуют
        в оригинальной
        '''
        logger.info("обработка для папки :" + folder)
        # файлы в папке
        folder_image_list = os.listdir(folder)
        # файлы которые есть в origin_image_list но нет в folder_image_list
        new_files = Set(self.origin_image_list) - Set(folder_image_list)
        logger.info("новые файлы :" + str(new_files))
        # добавляем
        for file_to_sync in new_files:
            #получаем размеры нужного изображения из имени папки
            size = folder.split('/')[-1]
            command = 'convert "%s" -resize %s "%s"' % (
                    self.origin_folder + '/' + file_to_sync,
                    size,
                    folder + '/' + file_to_sync,
                  )
            logger.info(command)
            result = os.system(command)
            logger.info(result)
        # файлы которые есть в folder_image_list но нет в origin_image_list
        delte_files = Set(folder_image_list) - Set(self.origin_image_list)
        logger.info("устаревшие файлы:" + str(delte_files))
        # удаляем
        for file_to_sync in delte_files:
            logger.info('delete ' + folder + '/' + file_to_sync)
            os.remove(folder + '/' + file_to_sync)

    def sunc_folders(self):
        '''
        проходимся по всем папкам и для кадой запускаем синхронизатор
        '''
        #запоминаем список файлов  в оригинальной директории
        self.origin_image_list = os.listdir(self.origin_folder)
        #проходим по каждой папке и запускаем синхронизатор
        for folder in self.get_folders_to_sync():
            self.folder_sync(folder)

    def run(self):
        logger.info("start daemon azazel")
        self.sunc_folders()
        while True:
            last_update = self.get_last_update_origin_folder()
            if self.last_time_update < last_update:
                logger.info("обнаружено изменение")
                self.sunc_folders()
                self.set_last_update(last_update)
        time.sleep(10)

daemon = Azazel()
logger = logging.getLogger("DaemonLog")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.FileHandler(LOG_PATH + "/azazel.log")
handler.setFormatter(formatter)
logger.addHandler(handler)

daemon_runner = runner.DaemonRunner(daemon)

daemon_runner.daemon_context.files_preserve = [handler.stream]
daemon_runner.do_action()
