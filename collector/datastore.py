import sqlite3
from datetime import datetime

class Event():
    
    type = None
    name = None
    value = None
    timestamp = None

    def __init__(self, event_type, name, value, timestamp = datetime.utcnow()):
        self.name = name
        self.value = value
        self.timestamp = timestamp
        self.type = event_type
        

class DataStore(object):

    def __init__(self):
        pass
    
    def record_data(self,event_id,value,timestamp=None):
        pass
    
    def record_event(self, event):
        self.record_data(event.type+":"+event.name, event.value, event.timestamp)
         

    
class SQLiteDatastore(DataStore):
    
    conn = None
    
    def __init__(self, filename):
        self.conn = sqlite3.connect(filename)
        self.create_tables()
            
    def create_tables(self):
        try: 
            cur = self.conn.cursor()
            cur.execute("create table valuelog (sensor, timestamp, value)")
        except Exception as e:
            print(e)
            
    def record_data(self,event_id,value,timestamp=datetime.utcnow()):
        cur = self.conn.cursor()
        print(timestamp.isoformat())
        cur.execute("insert into valuelog (sensor,timestamp,value) values (?, ?, ?)", 
                    (event_id, timestamp.isoformat(),value))
        self.conn.commit()
        
    
