import uuid

from queue import Queue
from threading import Lock, Thread

import firebase_admin
from firebase_admin import firestore, db
cred_obj = firebase_admin.credentials.Certificate('service_key.json')
default_app = firebase_admin.initialize_app(
    cred_obj, 
    {
        'databaseURL':'https://drawing-e19ac-default-rtdb.firebaseio.com/'
    }
)
#db=firestore.client() #

class db_connection():
    def __init__(self, id=None, room='default'):
        if id is None:
            self.id = uuid.uuid4().hex
        else:
            self.id=id

        self.room=room

        self.own_path_ref = db.reference(f'rooms/{self.room}/paths/{self.id}')
        self.all_paths_ref = db.reference(f'rooms/{self.room}/paths')
        self.erase_ref = db.reference(f'rooms/{self.room}/erase/{self.id}')
        self.room_ref = db.reference(f'rooms/{self.room}')
        self.eraseQueue = Queue()
        self.pathQueue = Queue()
        self.OtherPathsLock = Lock()
        self.otherPaths = dict()

        self.pathUpdateThread = Thread(target=self._update_paths)
        self.pathUpdateThread.daemon = True
        self.pathUpdateThread.start()

        self.listen_for_changes()
    
    def _update_paths(self):
        while True:
            paths = self.pathQueue.get(block=True)
            while not self.pathQueue.empty():#safe in this instance because nothing else pulls from queue, only adds
                paths = self.pathQueue.get() #always get the most recent version of path, incase several have pushed since the last call.
            self.own_path_ref.set(paths)

    def push_updated_paths(self, paths):
        self.pathQueue.put(paths, True)

    def listen_for_changes(self):
        def erase_listener(event:db.Event):
            data=event.data
            paths_to_update = dict()
            for key in event:
                self.erase_ref.child(key).delete()
                self.eraseQueue.put(data)
                

        def paths_listener(event:db.Event):

            print(f'{event.path=}')
            print(f'{event.data=}')
            '''
            for key in data:
                if key != self.id:
                    paths_to_update[key] = data[key]
            '''
            if event.path != f'/{self.id}':
                with self.OtherPathsLock:
                    self.otherPaths[event.path] = event.data
        
        #let's add erase support once the core works
        #self.erase_ref.listen(erase_listener)
        self.all_paths_ref.listen(paths_listener)
        print("configured listener(s)")