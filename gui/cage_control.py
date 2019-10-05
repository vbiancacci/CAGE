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
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *

# === PRIMARY EVENT LOOP =======================================================

def main():
    """
    """
    par = argparse.ArgumentParser(description='CAGE Slow Controls App')
    arg, st, sf = par.add_argument, 'store_true', 'store_false'
    arg('-d', '--debug', action=st, help='debug mode')
    args = vars(par.parse_args())
    
    # create the main application
    app = pg.mkQApp()
    pg.setConfigOption('background', 'k')
    pg.setConfigOption('foreground', 'w')
    
    # declare main window
    cm = CAGEMonitor()

    # debug a single plot widget
    # rp = RabbitPlot(["cage_pressure"], "2019-10-04T17:30", "now")
    
    # connect the RabbitPlot emit signal
    pool = QThreadPool()
    listener = RabbitListener()
    # listener.signals.target.connect(rp.update_data)
    listener.signals.target.connect(cm.dbmon.rp.update_data)
    pool.start(listener)
        
    # start the main Qt loop
    # if not args["debug"]:
    exit(app.exec_())
    

# === PRIMARY GUI WINDOW =======================================================

class CAGEMonitor(QMainWindow):
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
        self.dbmon = DBMonitor()
        self.dbmon.init_gui()
        tabs.addTab(self.dbmon,"DB Monitor")
        
        # tab 2 -- motor controller
        # st2 = MotorMonitor()
        # st2 = QWidget() # blank
        # tabs.addTab(st2,"Motor Controller")
        
        # tab 3 -- MJ60 DB monitor?
        # also need an HV biasing & interlock widget

        self.setCentralWidget(tabs)
        self.show()


class DBMonitor(QWidget):
    """
    Our first widget (tab).  Allows us to monitor values posted to the CAGE DB.
    Available data streams are called "endpoints": mj60_baseline, cage_pressure, etc.
    """
    def __init__(self):
        super().__init__()
        self.show()
        self.resize(1000,1000)
        
        # establish a postgres-style connection
        with open("config.json") as f:
            self.config = json.load(f)

        self.connection = psycopg2.connect(
            host = self.config["cage_daq"],
            dbname = self.config["db_name"],
            user = self.config["db_user"],
            password = self.config["password"]
            )
        self.cursor = self.connection.cursor()

        # get a list of all available endpoints in the DB
        # save info: {endpoint_name : type (usually 'numeric' or 'string')}
        self.endpoints = {}
        self.cursor.execute("SELECT * FROM endpoint_id_map;")
        for rec in self.cursor.fetchall():
            self.endpoints[rec[1]] = rec[2]
        # pprint(self.endpoints)
        
        # declare the parameter tree
        self.tree = ParameterTree()
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
                 ]}]


    def init_gui(self):
        
        p = Parameter.create(name='params', type='group', children=self.params)
        
        @pyqtSlot(dict)
        def change(param, changes):
            # could also emit stuff here
            # identify changes in the ParameterTree.
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
        
        # test save/restore
        s = p.saveState()
        p.restoreState(s)

        # create a parameter tree widget
        self.t = ParameterTree()
        self.t.setParameters(p, showTop=False)
        self.t.setWindowTitle('pyqtgraph example: Parameter Tree')
        
        # create a RabbitPlot 
        # self.rp = pg.PlotWidget(name="crap")
        self.rp = RabbitPlot(["cage_pressure"], "2019-10-04T17:30", "now")
        # self.rp.update_data()
        # self.rp.show()
        
        
        
        # # make a second plot
        # plot2 = pg.PlotWidget()
        # plot2.plot(xv, yv, pen='g')
        
        # set the layout of the widget
        # NOTE: (widget, # y_row, x_row, y_span, x_span)
        layout = QtGui.QGridLayout()
        layout.setColumnStretch(2, 2)
        layout.addWidget(self.t, 0, 0, 2, 1)
        layout.addWidget(self.rp, 0, 2) 
        # layout.addWidget(plot2, 1, 2)
        self.setLayout(layout)


# === RABBITMQ LISTENER (includes a live updating plot) ========================

class RabbitPlot(pg.PlotWidget):
    def __init__(self, endpoints, start=None, end=None):
        super().__init__()
        self.show()
        
        self.p1 = self.plot()
        self.p1.setPen('g')
        self.setLabel('left', "Value", units="V")
        self.setLabel('bottom', "Time", units="s")
        # self.p1.setLogMode(xMode=False, yMode=True)
        
        # declare endpoints of interest
        self.endpoints = ["cage_pressure"]
        self.start = "2019-10-04T17:30"
        self.end = "now" 
        
        # set the initial values
        self.yd = np.random.rand(10)
        self.update_data()
        
    def update_data(self, xv=None, yv=None):
        if yv is not None:
            print("appending:", yv)
            self.yd = np.append(self.yd, yv)
        xd = np.arange(len(self.yd))
        self.p1.setData(y=self.yd, x=xd)


class RabbitSignal(QObject):
    # used by RabbitListener to communicate w/ the main loop (app.exec_())
    # "if you want to define your own signals, they have to be class variables"
    target = pyqtSignal(str, float) 


class RabbitListener(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = RabbitSignal()

    def run(self):
        with open("config.json") as f:
            self.config = json.load(f)
            
        self.cpars = pika.ConnectionParameters(host=self.config['cage_daq'])
        self.conn = pika.BlockingConnection(self.cpars)
        self.channel = self.conn.channel()

        self.channel.exchange_declare(exchange=self.config["exchange"], 
                                      exchange_type='topic')
        
        self.channel.queue_declare(queue=self.config['queue'], 
                                   exclusive=True)
    
        self.channel.queue_bind(exchange=self.config['exchange'],
                                queue=self.config['queue'],
                                routing_key="sensor_value.cage_pressure")

        self.channel.basic_consume(queue=self.config['queue'], 
                                   on_message_callback=self.dispatch, 
                                   auto_ack=True)

        self.channel.start_consuming()


    def dispatch(self, channel, method, properties, body):
        key = method.routing_key
        record = json.loads(body.decode()) # decode binary string to dict
        print('got a record.  name:', key)
        # pprint(record)
        xv = record["timestamp"]
        yv = record["payload"]["value_cal"]
        self.signals.target.emit(xv, yv)
    

# === 




if __name__=="__main__":
    main()