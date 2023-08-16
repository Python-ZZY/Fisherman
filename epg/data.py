import epg
import os
import hashlib
import pickle

class SaveFileException(Exception):
    pass

def set_default_path(path="savefile.bin", org=None, app=None):
    global default_path
    
    dir = epg.system.get_pref_path(org, app) if org and app else ""
    default_path = os.path.join(dir, path)

set_default_path()
hash_name = "md5"

def get_hash(data):
    h = hashlib.new(hash_name)
    h.update(data)
    return h.hexdigest()

def clear(path=None):
    if not path: path = default_path

    os.remove(path)
    
def load(path=None, default=None, error=False):
    if not path: path = default_path

    try:
        with open(path, "rb") as f:
            obj, hash = pickle.load(f)
    except FileNotFoundError as e:
        if default is None:
            raise e
        else:
            return default
    
    if get_hash(pickle.dumps(obj)) != hash:
        if error:
            raise SaveFileException(str(path))
        else:
            return default

    else:
        return obj

def dump(obj, path=None):
    if not path: path = default_path

    with open(path, "wb") as f:
        pickle.dump([obj, get_hash(pickle.dumps(obj))], f)
