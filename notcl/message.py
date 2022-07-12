import re
from base64 import b64encode, b64decode
import socket

class RawMessage(dict):
    """Keys can only contain a-z, A-Z and underscores.
    RawMessages can be decoded to Messages."""
    @classmethod
    def from_pipe(cls, f_in):
        """reads until EOF"""
        msg_list = f_in.read().split(b"\n")
        if len(msg_list)%2 != 0:
            raise ValueError("RawMessage requires an even number of items (key value pairs)")
    
        msg = cls()
        while len(msg_list)>0:
            key = msg_list.pop(0).decode("ascii")
            value = msg_list.pop(0)

            msg[key] = b64decode(value).decode("utf8")

        return msg


    def send_to_pipe(self, f_out):
        msg_list = []
        for key, value in self.items():
            if not re.fullmatch("[a-zA-Z_+]*", key):
                raise ValueError(f"Messages keys can only contain a-z, A-Z and underscores, got '{key}'")
            msg_list.append(key.encode("ascii"))
            msg_list.append(b64encode(value.encode("utf8")))
        f_out.write(b"\n".join(msg_list))
        f_out.flush()

    def decode(self, msg_classes):
        pass

    def to_message(self, permitted_msg_classes):
        """Converts RawMessage to Message.
        permitted_msg_classes can be either one message class or a list of message classes."""
        if isinstance(permitted_msg_classes, type):
            permitted_msg_classes = (permitted_msg_classes, )

        for cls in permitted_msg_classes:
            try:
                return cls(self)
            except WrongMessageClass:
                pass
        raise WrongMessageClass()

class WrongMessageClass(Exception):
    pass

class Message:
    """Overwrite keys_optional and keys_required in subclasses."""
    keys_optional = []
    keys_required = []

    __slots__=("_data",)

    def __init__(self, source: dict=None, **kwargs):
        """Can either be initialized from dict that has been received or by providing values for all fields."""
        if source:
            assert len(kwargs)==0
            assert not ("class" in kwargs) 
            if source["class"] != self.__class__.__name__:
                raise WrongMessageClass()
            self._data = dict(source)
        else:
            self._data = dict(kwargs)
            self._data["class"] = self.__class__.__name__

    def to_raw_message(self):
        return RawMessage(self._data)

    def __repr__(self):
        cls_name = self.__class__.__name__
        return f"<{cls_name} {self._data}>"

    def __getattr__(self, name):
        return self._data[name]