#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: İsmail BAŞARAN <ismail.basaran@tubitak.gov.tr> <basaran.ismaill@gmail.com>
from enum import Enum


class MessageType(Enum):
    EXECUTE_POLICY = 'EXECUTE_POLICY'
    EXECUTE_SCRIPT = 'EXECUTE_SCRIPT'
    EXECUTE_TASK = 'EXECUTE_TASK'
    GET_POLICIES = 'GET_POLICIES'
    INSTALL_PLUGIN = 'INSTALL_PLUGIN'
    LOGIN = 'LOGIN'
    LOGOUT = 'LOGOUT'
    MISSING_PLUGIN = 'MISSING_PLUGIN'
    MOVE_FILE = 'MOVE_FILE'
    POLICY_STATUS = 'POLICY_STATUS'
    REGISTER = 'REGISTER'
    REGISTER_LDAP = 'REGISTER_LDAP'
    REQUEST_FILE = 'REQUEST_FILE'
    RETRIVE_FILE = 'SEND_FILE'
    UNREGISTER = 'UNREGISTER'
    TASK_STATUS = 'TASK_STATUS'
