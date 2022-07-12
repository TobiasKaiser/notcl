from ..bridge_server import BridgeServer
from ..bridge_client import BridgeClient

import threading
from .. import msg_classes as msg
from contextlib import contextmanager

@contextmanager
def bridge_server_with_client():
    with BridgeServer() as bs:
        client = BridgeClient(fn_tcl2py=bs.fn_tcl2py, fn_py2tcl=bs.fn_py2tcl)
        client_thread = threading.Thread(target=client.run)
        client_thread.start()

        try:
            yield bs
        finally:
            client_thread.join()

def test_bridge_server_client():
    with bridge_server_with_client() as bs:
        r=bs.recv(msg.TclHello)
        print(f"received {r}")
        
        for cmd in ["abc", "Defgh", "Guten Tag"]:
            bs.send(msg.PyProcedureCall(command=cmd))
            resp=bs.recv(msg.TclProcedureResult)
            print(f"received {resp}")
            assert resp.result == cmd.upper()
        bs.send(msg.PyExit())
