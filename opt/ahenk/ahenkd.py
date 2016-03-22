#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: İsmail BAŞARAN <ismail.basaran@tubitak.gov.tr> <basaran.ismaill@gmail.com>
# Author: Volkan Şahin <volkansah.in> <bm.volkansahin@gmail.com>

from base.config.ConfigManager import ConfigManager
from base.deamon.BaseDeamon import BaseDaemon
from base.logger.AhenkLogger import Logger
from base.Scope import Scope
from base.messaging.Messaging import Messaging
from base.messaging.Messager import Messager
from base.execution.ExecutionManager import ExecutionManager
from base.registration.Registration import Registration
from base.messaging.MessageResponseQueue import MessageResponseQueue
from base.event.EventManager import EventManager
from base.plugin.PluginManager import PluginManager
from base.task.TaskManager import TaskManager
from base.database.AhenkDbService import AhenkDbService
import threading, time, sys, os, signal, configparser

pidfilePath = '/var/run/ahenk.pid'

class AhenkDeamon(BaseDaemon):
    """docstring for AhenkDeamon"""


    def reload(self,msg):
        # reload service here
        pass

    def run(self):
        print('Ahenk running...')

        globalscope = Scope()
        globalscope.setInstance(globalscope)

        configFilePath='/etc/ahenk/ahenk.conf'
        configfileFolderPath='/etc/ahenk/config.d/'

        #configuration manager must be first load
        configManager = ConfigManager(configFilePath,configfileFolderPath)
        config = configManager.read()
        globalscope.setConfigurationManager(config)

        # Logger must be second
        logger = Logger()
        logger.info('[AhenkDeamon] Log was set')
        globalscope.setLogger(logger)

        eventManager = EventManager()
        globalscope.setEventManager(eventManager)
        logger.info('[AhenkDeamon] Event Manager was set')

        db_service=AhenkDbService()
        db_service.connect()
        db_service.initialize_table()
        globalscope.setDbService(db_service)
        logger.info('[AhenkDeamon] Data Base Service was set')

        messageManager = Messaging()
        globalscope.setMessageManager(messageManager)
        logger.info('[AhenkDeamon] Message Manager was set')

        pluginManager = PluginManager()
        pluginManager.loadPlugins()
        globalscope.setPluginManager(pluginManager)
        logger.info('[AhenkDeamon] Plugin Manager was set')

        taskManager = TaskManager()
        globalscope.setTaskManager(taskManager)
        logger.info('[AhenkDeamon] Task Manager was set')

        registration=Registration()
        globalscope.setRegistration(registration)
        logger.info('[AhenkDeamon] Registration was set')

        execution_manager=ExecutionManager()
        globalscope.setExecutionManager(execution_manager)
        logger.info('[AhenkDeamon] Execution Manager was set')


        #TODO restrict number of attemption
        while registration.is_registered() is False:
            logger.debug('[AhenkDeamon] Attempting to register')
            registration.registration_request()

        logger.info('[AhenkDeamon] Ahenk is registered')

        messager = Messager()
        messanger_thread = threading.Thread(target=messager.connect_to_server)
        messanger_thread.start()

        while(messager.is_connected() is False):
            time.sleep(1)

        globalscope.setMessager(messager)
        logger.info('[AhenkDeamon] Messager was set')

        if registration.is_ldap_registered() is False:
            logger.debug('[AhenkDeamon] Attempting to registering ldap')
            registration.ldap_registration_request() #TODO work on message

        logger.info('[AhenkDeamon] LDAP registration of Ahenk is completed')

        #TODO###############
        cnfg = configparser.ConfigParser()
        cnfg.add_section('PID')
        cnfg.set('PID','pid_number',str(os.getpid()))

        with open(pidfilePath, 'w') as config_file:
            cnfg.write(config_file)
        #TODO##############

        try:
            signal.signal(signal.SIGALRM, self.signal_handler)
            logger.info('[AhenkDeamon] Signal handler is set up')
        except Exception as e:
            logger.error('[AhenkDeamon] Signal handler could not set up :'+e.errno+'-'+e.strerror)

        #messager.send_direct_message('test')

        while True:
            time.sleep(1)

        #request policies
        #logger.info('[AhenkDeamon] Requesting policies...')
        #messager.send_direct_message(messageManager.policy_request_msg())

        """
            this is must be created after message services
            responseQueue = queue.Queue()
            messageResponseQueue = MessageResponseQueue(responseQueue)
            messageResponseQueue.setDaemon(True)
            messageResponseQueue.start()
            globalscope.setResponseQueue(responseQueue)
        """

    def signal_handler (self, num, stack):

        #TODO######
        config = configparser.ConfigParser()
        config._interpolation = configparser.ExtendedInterpolation()
        config.read(pidfilePath)
        event=config.get('PID', 'event')
        #TODO######

        params = event.split()
        scope = Scope().getInstance()
        logger = scope.getLogger()

        if 'login' == str(params[0]):
            message = scope.getMessageManager().login_msg(params[1])
            scope.getMessager().send_direct_message(message)
            logger.debug('[AhenkDeamon] login event is handled for user:'+params[1])
        elif 'logout' == str(params[0]):
            message = scope.getMessageManager().logout_msg(params[1])
            scope.getMessager().send_direct_message(message)
            logger.debug('[AhenkDeamon] logout event is handled for user:'+params[1])
        else:
            logger.error('[AhenkDeamon] Unknown command error. Command:'+params[0])

        logger.debug('[AhenkDeamon] Processing of handled event is completed')

if __name__ == '__main__':

    ahenkdaemon = AhenkDeamon(pidfilePath)

    if len(sys.argv) == 2:
        if sys.argv[1] == 'start':
            print('starting')
            ahenkdaemon.run()
        elif sys.argv[1] == 'stop':
            ahenkdaemon.stop()
        elif sys.argv[1] == 'restart':
            ahenkdaemon.restart()
        elif sys.argv[1] == 'status':
            print('status')
        else:
            print('Unknown command. Usage : %s start|stop|restart|status' % sys.argv[0])
            sys.exit(2)

    elif len(sys.argv) == 3:
        if sys.argv[1] == 'login' or sys.argv[1] == 'logout':
            print('event:'+str(sys.argv[1]))

            #TODO##############
            config = configparser.ConfigParser()
            config._interpolation = configparser.ExtendedInterpolation()
            config.read(pidfilePath)
            pid_number = config.get('PID','pid_number')
            config.set('PID', 'event', str(sys.argv[1])+' '+sys.argv[2])
            #TODO##############

            with open(pidfilePath, 'w') as config_file:
                config.write(config_file)

            os.kill(int(pid_number), signal.SIGALRM)
        else:
            print('Unknown command. Usage : %s start|stop|restart|status' % sys.argv[0])
            sys.exit(2)
        sys.exit(0)
    else:
        print('Usage : %s start|stop|restart|status' % sys.argv[0])
        sys.exit(2)




