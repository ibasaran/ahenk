#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Volkan Şahin <basaran.ismaill@gmail.com>
# Author: İsmail BAŞARAN <ismail.basaran@tubitak.gov.tr> <basaran.ismaill@gmail.com>

import configparser
import slixmpp
from slixmpp.exceptions import IqError, IqTimeout
from ahenkd import AhenkDeamon

"""
--fetch parameters of connection  from conf file
--connect xmpp
--send direct message
--receive direct message
--send muc message
--receive muc message
--listen to muc invites
--auto accept muc invites
--send auto reply to muc messages
--receive file (0065)
--send file (0065)

"""

class Messaging(slixmpp.ClientXMPP):

    def __init__(self):

        # global scope of ahenk
        scope = AhenkDeamon.scope()

        # logger comes from ahenk deamon
        self.logger = scope.getLogger()

        # configurationManager comes from ahenk deamon
        self.configurationManager = scope.getConfigurationManager()

        #set parameters
        slixmpp.ClientXMPP.__init__(self, self.configurationManager.get('CONNECTION', 'jid'), self.configurationManager.get('Connection_Param', 'password'))
        self.nick = self.configurationManager.get('CONNECTION', 'nick')
        self.receiver=self.configurationManager.get('CONNECTION','receiverJid')
        self.sendfile=open(self.configurationManager.get('CONNECTION','sendFilePath'), 'rb')
        self.receivefile=self.configurationManager.get('CONNECTION', 'receiveFileParam')
        self.logger.info('Parameters were established')

        self.add_event_handler("session_start", self.start)
        self.room=self.add_event_handler("groupchat_invite", self.invite_auto_accept)

        self.add_listeners()
        #!!! you have to use modified slixmpp for file transfering
        #self.send_file()

    def add_listeners(self):

        self.add_event_handler("groupchat_message", self.recv_muc_message)
        self.add_event_handler("message", self.recv_direct_message)

        #file_listeners
        #self.add_event_handler("socks5_connected", self.stream_opened)
        #self.add_event_handler("socks5_data", self.stream_data)
        #self.add_event_handler("socks5_closed", self.stream_closed)

        self.logger.info('Listeners were added')


    def stream_opened(self, sid):
        self.logger.info('Stream opened. %s', sid)
        return open(self.receivefile, 'wb')

    def stream_data(self, data):
        self.logger.info('Stream data.')
        self.file.write(data)

    def stream_closed(self, exception):
        self.logger.info('Stream closed. %s', exception)
        self.file.close()
        #self.disconnect()


    def send_file(self):
        try:
            # Open the S5B stream in which to write to.
            proxy = yield from self['xep_0065'].handshake(self.receiver)

            # Send the entire file.
            while True:
                data = self.file.read(1048576)
                if not data:
                    break
                yield from proxy.write(data)
            # And finally close the stream.
            proxy.transport.write_eof()
        except (IqError, IqTimeout):
            print('File transfer errored')
        else:
            print('File transfer finished')
        finally:
            self.file.close()



    def start(self, event):
        self.get_roster()
        self.send_presence()


    def invite_auto_accept(self, inv):

        self.room=inv['from']
        print("(%s) invite is accepted" % str(self.room))
        self.plugin['xep_0045'].joinMUC(self.room,self.nick,wait=True)
        self.send_message(mto=self.room.bare,mbody="Hi all!",mtype='groupchat')
        return self.room

    def recv_muc_message(self, msg):#auto reply

        if msg['mucnick'] != self.nick:
            print("%s : %s" % (str(msg['from']),str(msg['body'])) )
            self.send_message(mto=msg['from'].bare,mbody="I got it, %s." % msg['mucnick'],mtype='groupchat')
        else:
            print("%s : %s" % (str(msg['mucnick']),str(msg['body'])))

    def send_direct_message(self,msg):
        self.send_message(mto=self.receiver,mbody=msg,mtype='chat')

    def recv_direct_message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            print ("%s : %s" % (msg['from'], msg['body']))

    def connectToServer(self):
        try:
            self.register_plugin('xep_0030') # Service Discovery
            self.register_plugin('xep_0045') # Multi-User Chat
            self.register_plugin('xep_0199') # XMPP Ping
            self.register_plugin('xep_0065') # SOCKS5 Bytestreams

            self.logger.info('Plugins were registered: xep_0030,xep_0045,xep_0199,xep_0065')

            self.connect()
            self.process()
            return True
        except Exception as e:
            self.logger.error('Connection to server failed!')
            return False


if __name__ == '__main__':

    xmpp = Messaging(None,None)
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0045') # Multi-User Chat
    xmpp.register_plugin('xep_0199') # XMPP Ping
    xmpp.register_plugin('xep_0065') # SOCKS5 Bytestreams

    self.logger.info('Plugins were registered: xep_0030,xep_0045,xep_0199,xep_0065')

    # Connect to the XMPP server and start processing XMPP stanzas.
    xmpp.connect()
    xmpp.process()
