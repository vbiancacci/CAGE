#!/usr/bin/env python3
import sys
import time
import json
import argparse
import psycopg2
import pika
import multiprocessing
import numpy as np
from pprint import pprint

import pyqtgraph as pg
from pyqtgraph.parametertree import ParameterTree, Parameter
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from PyQt5 import QtGui
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLayout, QTabWidget

def main():
    """
    """
    par = argparse.ArgumentParser(description='Live plotting app')
    arg, st, sf = par.add_argument, 'store_true', 'store_false'
    arg('-d', '--debug', action=st, help='debug mode')
    args = vars(par.parse_args())
    
    # create the main application
    app = pg.mkQApp()
    pg.setConfigOption('background', 'k')
    pg.setConfigOption('foreground', 'w')
    
    dm = DataMonitor()
        
    if not args["debug"]:
        print("do i get here?")
        exit(app.exec_())
    



class DataMonitor(QMainWindow):
    """
    we use a tabbed main window, to organize widgets for each subsystem.
    
    TODO: add ability to drag tabs to separate windows, and also reattach:
    https://stackoverflow.com/questions/48901854/is-it-possible-to-drag-a-qtabwidget-and-open-a-new-window-containing-whats-in-t
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle('CAGE Detector Monitor')
        self.setGeometry(0, 0, 1000, 900)
        
        tabs = QTabWidget()

        # tab 1 -- db monitor
        dbmon = DBMonitor()
        dbmon.init_gui()
        dbmon.open_connections()
        tabs.addTab(dbmon,"DB Monitor")
        
        # tab 2 -- motor controller
        # st2 = MotorMonitor()
        st2 = QWidget() # blank
        tabs.addTab(st2,"Motor Controller")

        self.setCentralWidget(tabs)
        self.show()
        

class DBMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.show()
        self.resize(1000,1000)
        self.tree = ParameterTree()
        
        
        
        # declare the parameter tree
        self.params = [
            {'name': 'Basic parameter data types', 
             'type': 'group', 
             'children': [
                 
                 {'name': 'Named List', 'type': 'list', 
                  'values': {"one": 1, "two": "twosies", "three": [3,3,3]}}, 
                 {'name': 'Action 1', 'type': 'action'},
                 {'name': 'Action 2', 'type': 'action'},
                 
                 {'name': 'Integer', 'type': 'int', 'value': 10},
                 {'name': 'Float', 'type': 'float', 'value': 10.5, 'step': 0.1},
                 {'name': 'String', 'type': 'str', 'value': "hi"},
                 {'name': 'List', 'type': 'list', 'values': [1,2,3], 'value': 2}
                 
              ]
             }
            ]
        
    def open_connections(self):
        """
        """
        # get credentials
        with open("config.json") as f:
            self.config = json.load(f)

        # access the postgres DB
        self.init_postgres()
        
        # access the live message queue with a separate thread
        self.rabbit = RabbitQueueMonitor()
        
        listener = multiprocessing.Process(target=self.rabbit.listen)
        listener.start()
        # listener.terminate() # TODO: need to run this when we exit the GUI
        
        
    def init_postgres(self):
        """
        establish a connection with UW's CAGE postgres database
        """
        self.connection = psycopg2.connect(
            host = self.config["cage_daq"],
            dbname = self.config["db_name"],
            user = self.config["user"],
            password = self.config["password"]
            )
        self.cursor = self.connection.cursor()

        # get a list of all endpoints in the DB
        self.cursor.execute("SELECT * FROM endpoint_id_map;")
        record = self.cursor.fetchall()
        
        # save info: {endpoint_name : type (usually 'numeric' or 'string')}
        self.endpoints = {}
        for rec in record:
            self.endpoints[rec[1]] = rec[2]
        pprint(self.endpoints)
        
        
    def init_gui(self):
        
        p = Parameter.create(name='params', type='group', children=self.params)
        
        def change(param, changes):
            print("tree changes:")
            for param, change, data in changes:
                path = p.childPath(param)
                if path is not None:
                    childName = '.'.join(path)
                else:
                    childName = param.name()
                print('  parameter: %s'% childName)
                print('  change:    %s'% change)
                print('  data:      %s'% str(data))
                print('  ----------')
        p.sigTreeStateChanged.connect(change)

        # create a parameter tree widget
        t = ParameterTree()
        t.setParameters(p, showTop=False)
        t.setWindowTitle('pyqtgraph example: Parameter Tree')
        
        # plot some data
        plot = pg.PlotWidget()
        n = 1000
        xv = np.arange(n)
        yv = 1 * pg.gaussianFilter(np.random.random(size=n), 10)
        plot.plot(xv, yv, pen='r')
        
        # make a second plot
        plot2 = pg.PlotWidget()
        plot2.plot(xv, yv, pen='g')
        
        # set the layout of the widget
        layout = QtGui.QGridLayout()
        
        # layout.columnStretch(5)
        layout.setColumnStretch(2, 2)
        
        # NOTE: (widget, # y_row, x_row, y_span, x_span)
        # layout.addWidget(QtGui.QLabel("Data monitor thing"), 0, 0, 1, 2)
        
        layout.addWidget(t, 0, 0, 2, 1)
        
        layout.addWidget(plot, 0, 2) 
        layout.addWidget(plot2, 1, 2)
        
        self.setLayout(layout)

        # test save/restore
        s = p.saveState()
        p.restoreState(s)
        


class RabbitQueueMonitor():

    def __init__(self, *args, **kwargs):
        
        with open('config.json') as f:
            self.config = json.load(f)
        
        self.cpars = pika.ConnectionParameters(host = self.config["cage_daq"])
        self.conn = pika.BlockingConnection(self.cpars)
        self.channel = self.conn.channel()
        self.channel.exchange_declare(exchange = 'bunny', # needs a dummy name
                                      exchange_type = 'topic')
        
        print("i'm loaded")
        
    def listen(self):
        result = self.channel.queue_declare('', exclusive=True)
        queue_name = result.method.queue
        # print("queue name is:", queue_name)
        # for key in keys:
        self.channel.queue_bind(queue=queue_name, 
                                exchange="alerts", 
                                routing_key='sensor_value.#')

        self.channel.basic_consume(queue = queue_name, 
                                   on_message_callback = self.read_records, 
                                   auto_ack = True)

        self.channel.start_consuming()
        
        
    def read_records(self, ch, method, properties, body):
        """
        one example record:
        {'msgtype': 4,
         'payload': {'value_cal': -192.61142915943446,
                     'value_raw': -192.61142915943446},
         'sender_info': {'commit': 'g7190b92',
                         'exe': '/home/pi/controls/latest/bin/dragonfly',
                         'hostname': 'scannerpi',
                         'package': 'dripline',
                         'service_name': 'scannerpi_service',
                         'username': 'pi',
                         'version': 'v3.7.3'},
         'timestamp': '2019-09-28T16:35:20.089774Z'}
        """
        re
        
        

    # def __enter__(self):
    # 
    #     self.consume(keys=[...], callback=self.read_records)
    # 
    #     # return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.conn.close()
        
        




if __name__=="__main__":
    main()