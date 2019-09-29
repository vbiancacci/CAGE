#!/usr/bin/env python3
import json
import multiprocessing
from pprint import pprint
import collections
import pika

from dateutil import parser
from datetime import datetime, timedelta


def main():
    """
    """
    # consumer_thread = multiprocessing.Process(target=start_listener)
    # consumer_thread.start()
    
    # read_queue()
    # exit()
    
    start_listener()
    
    # # test the non-blocking queue reader
    # def start_listener():
    #     with RabbitQueueMonitor() as consumer:
    #         consumer.consume(keys=[...], callback=listen)
    # rabbit_thread = multiprocessing.Process(target=start_listener)
    # rabbit_thread.start()
    # exit()


def start_listener():
    """
    note: we walk backwards in time, starting from now and ending ... back then.
    for now i'm also using datetime objects directly, but i might need to be able
    to start with string objects.
    it would also be cool to have a graphical calendar select in the GUI.
    """
    key_list = ["mj60_baseline", "cage_pressure"]
    start = "now"
    end = "2019-09-28" 
    with QueueMonitor(key_list, start, end) as qmon:
        qmon.listen()


class QueueMonitor():
    """
    listen to RabbitMQ and parse each value from the DB: (sensor_value.*)
    the user can specify a list of inputs, or leave blank to save all values
    as they come in.
    
    by default, fill the DB with 'n_days' worth of entries or 'n_list' entries,
    whichever comes first.
    """
    def __init__(self, keys=None, start_date=None, end_date=None):
        with open('config.json') as f:
            self.config = json.load(f)

        # defaults
        self.n_days = 1 
        self.n_list = 10000

        # use pika to connect to the message queue
        self.cpars = pika.ConnectionParameters(host=self.config['cage_daq'])
        self.conn = pika.BlockingConnection(self.cpars)
        self.channel = self.conn.channel()
        self.channel.exchange_declare(exchange='cage', exchange_type='topic')
        
        # circular buffers to store data from each sensor (key) of interest
        self.keys = keys
        self.data_lists = {}

        # optionally pre-fill the buffers
        self.conn = None
        self.start = get_datetime(start_date)
        if end_date is None:
            self.end = self.start - timedelta(days=self.n_days)
        else:
            self.end = get_datetime(end_date)
        if (start_date is not None) or (end_date is not None):
            prefill_db()
        
    def get_datetime(self, date_str, end=False):
        """
        take an input string from the user and parse to a datetime obj
        """
        if date_str == "now" or date_str is None:
            return datetime.now()
        try:
            return parser.parse(date_str)
        except:
            print("failed to parse date string:", date_str)
            exit()
                
    def prefill_db(self, keys=None):
        """
        pre-fill the data lists with a postgres call
        """
        self.start
        self.end
        self.config

        self.conn = psycopg2.connect(
            dbname = self.config["db_name"],
            user = self.config["db_user"], 
            password = self.config["password"],
            host = self.config["cage_daq"]
            )
        cursor = conn.cursor()        
        
        if keys is None:
            cmd = "SELECT * FROM endpoint_id_map;"
            cursor.execute(cmd)
            record = cursor.fetchall()
            self.keys = [rec[1] for rec in record]
        else:
            self.keys = [f'{key}' for key in keys]
            
        print("using key list:", self.keys)
        
        for key in self.keys:
            # need to get an ISO-formatted string from self.start and self.end
            str_start = self.start.isoformat()
            str_end = self.end.isoformat()
            
            print("start string:", str_start)
            print("end string:", str_end)
            
            query = f"SELECT value_cal, timestamp FROM numeric_data "
            query += f"WHERE endpoint_name='{key}' "
            query += f"AND timestamp < {str_start} and timestamp > {str_end};"
            
            print("query is:")
            print(query)
            print("\n")
            
        
        # run main query
        # cmd = "SELECT value_cal, timestamp FROM numeric_data WHERE endpoint_name='cage_ln_level' AND timestamp>'2019-09-27T00:00';"
        


    def listen(self):
        """
        using the pika BlockingConnection, we listen to the queue.  when we
        get a value, we run the callback function decode_values.
        """
        result = self.channel.queue_declare(queue=self.config['queue'], 
                                            exclusive=True)
        queue_name = result.method.queue
        
        if self.keys is not None:
            for key in self.keys:
                self.channel.queue_bind(exchange=self.config['exchange'], 
                                        queue=self.config['queue'],
                                        routing_key=key)
        else:
            self.channel.queue_bind(exchange=self.config['exchange'],
                                    queue=self.config['queue'],
                                    routing_key="sensor_value.#")
                                
        self.channel.basic_consume(queue=queue_name, 
                                   on_message_callback=self.decode_values, 
                                   auto_ack=True)
        
        self.channel.start_consuming()
        
    def decode_values(self, ch, method, properties, body):
        """
        decode the DB records and save to results arrays.  
        one example record:
        key: sensor_value.mj60_temp
        {'msgtype': 4,
         'payload': {'value_cal': -192.48926526480463,
                     'value_raw': -192.48926526480463},
         'sender_info': {'commit': 'g7190b92',
                         'exe': '/home/pi/controls/latest/bin/dragonfly',
                         'hostname': 'scannerpi',
                         'package': 'dripline',
                         'service_name': 'scannerpi_service',
                         'username': 'pi',
                         'version': 'v3.7.3'},
         'timestamp': '2019-09-28T23:37:16.592536Z'}
        """
        key = method.routing_key
        record = json.loads(body.decode()) # decode binary string to dict
        # pprint(record)
        
        # get the name of the record, strip off 'sensor_value.'
        rec_name = key.split('.')[-1]
        
        if rec_name not in self.data_lists:
            self.data_lists[key] = collections.deque(maxlen=5000)
        
        # right now, save only the values and ignore the sender_info
        cal, raw = None, None
        if 'value_cal' in record['payload']:
            cal = record['payload']['value_cal']
        if 'value_raw' in record['payload']:
            raw = record['payload']['value_raw']

        # convert timestamp string to a python friendly type automatically
        ts_raw = record['timestamp']
        ts_fmt = parser.parse(ts_raw)

        # read data to a circular buffer
        for key in self.keys:
            
            # initialize the buffer
            if key not in self.data_lists:
                self.data_lists[key] = collections.deque(maxlen=5000)
            
            if cal is not None:
                self.data_lists["cal"].append(cal)
    

if __name__=="__main__":
    main()