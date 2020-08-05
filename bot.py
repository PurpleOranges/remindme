#!/usr/bin/env python3

import time
from telethon import TelegramClient, events
import os, random
from dotenv import load_dotenv
from datetime import datetime
import parsedatetime
import logging
import sqlite3
import sched
import threading
import pickle
import json



# set logging config
logging.basicConfig(filename='remindme.log',
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.INFO)


# setup 
cal = parsedatetime.Calendar()
s = sched.scheduler(time.time, time.sleep)

# get telegram info from ./.env
load_dotenv()

session  = os.environ.get('TG_SESSION', 'printer')
api_id   = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")
phone    = os.getenv("PHONE_NUM")
password = os.getenv("PASSWORD") #if you have 2FA enabled
session_file = 'ikanye'


# create/open database
db = sqlite3.connect('data/reminders.sqlite')

# setup database
# cursor = db.cursor()
# cursor.execute('''
#    CREATE TABLE reminders(id INTEGER PRIMARY KEY,
#                           user_id TEXT,
#                           message_id TEXT, 
#                           creation_date TEXT, 
#                           reminder_date TEXT,
#                           message_json TEXT)
# ''')
# db.commit()


def remind():
    print('reminder sent.')


# threading stuff 
# https://www.tutorialspoint.com/python/python_multithreading.htm
exitFlag = 0

class myThread (threading.Thread):
   def __init__(self, threadID, name, counter):
      threading.Thread.__init__(self)
      self.threadID = threadID
      self.name = name
      self.counter = counter
   def run(self):
      print("Starting " + self.name)
      print_time(self.name, 999, self.counter)
      print("Exiting " + self.name)

def print_time(threadName, counter, delay):
   while counter:
      if exitFlag:
         threadName.exit()
      time.sleep(delay)
      print("%s: %s" % (threadName, time.ctime(time.time())))
      counter -= 1

# Create new threads
thread1 = myThread(1, "Thread-1", 1)

# Start new Threads
#thread1.start()

# main (idk what this if statement is for...)
if __name__ == '__main__':
    # Create the client and connect
    # use sequential_updates=True to respond to messages one at a time
    client = TelegramClient(session_file, api_id, api_hash, sequential_updates=True)



    @client.on(events.NewMessage)
    async def handle_new_message(event):
        #print(time.asctime(), '-', event.message)  # optionally log time and message
        print('message: ')
        #print("+"*20)
        #print(event)
        #print("+"*20)

        if event.raw_text.startswith('!remindme '):
            rt = event.message.message.split("!remindme ",1)[1]
            #print('rt: ', rt)
            time_struct, parse_status = cal.parse(rt)
            #print('time_struct: ', time_struct)
            #print('parse_status :', parse_status)
            readableTime = time.strftime('%Y-%m-%d %H:%M:%S', time_struct )
            #print('readableTime: ', readableTime)
            reminderMessage = 'reminder set for `' + readableTime + '`'

            # convert to datetime
            dt = datetime(*time_struct[:7]) #the [:7] should probably be changed to [:8] later. the 8th item is timezone

            # convert datetime to timetime
            t  = time.mktime(dt.timetuple()) + dt.microsecond / 1E6
            

            logging.info('test')
            # print(
            #         'created: ',    event.message.date,    '\n' 
            #         'message id: ', event.message.id,      '\n'
            #         'from: ',       event.message.from_id, '\n'
            #         'reminder: ',   readableTime,          '\n'
            #         '--------------------------------'
            #         )
            
            eventObject = event.to_dict() # thanks to simon schurrle from lonamiWebs telegram
            messageObject = event.original_update.message.to_dict()
            
            # encode message object as JSON so it can be stored in sqlite db
            serializedMessageObject = json.dumps(messageObject, indent=4, sort_keys=True, default=str) # https://stackoverflow.com/a/36142844/293064
            
            # add reminder to database
            #TODO add reminderSent flag to db 
            cursor = db.cursor()
            cursor.execute('''INSERT INTO reminders(user_id, message_id, creation_date, reminder_date, message_json) 
                              VALUES(?,?,?,?,?)''', (event.message.from_id, event.message.id, event.message.date, readableTime, serializedMessageObject))
            db.commit()

            # send reminder confirmation
            await event.reply(reminderMessage)
            print('t=',t)
            print(datetime.utcfromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S'))
            # schedule reminder
            s.enterabs(t, 1, remind)
            # run scheduled reminders
            s.run(False) #the "True/False" means not blocking.




    print(time.asctime(), '-', 'Auto-replying...')
    client.start(phone, password)
    client.run_until_disconnected()
    print(time.asctime(), '-', 'Stopped!')
    db.close()



