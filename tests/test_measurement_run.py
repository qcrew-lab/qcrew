""" Test script simulating a single measurement run """

import pprint
from tests.test_client import TestClient
from qcrew.helpers import logger

# import experiment classes, helpers, other measurement run dependencies


# initialize client and get mode objects from the client
client = TestClient()
qubit, rr = client.modes


# make changes to qubit and rr objects (as you would in configuration.py)
logger.info(f"{qubit} state before making changes")
pprint.pp(qubit.parameters)
#qubit.lo_freq = 3e9
#qubit.int_freq = -30e6
#logger.info(f"{qubit} state after making changes")
#pprint.pp(qubit.parameters)

logger.info(f"{rr} state before making changes")
pprint.pp(rr.parameters)
#rr.lo_freq = 7e9
#rr.int_freq = -70e6
#rr.tof = 700
#logger.info(f"{rr} state after making changes")
#pprint.pp(rr.parameters)


# run measurement, fetch, plot, save etc... (as you would in a usual measurement script)


#logger.info("Sending sync and save request...")
#client.sync()  # ask client to sync current state of modes to server
#client.server.save()  # ask server to save current instruments and modes to disk

# do this only if you want to stop running the server entirely (affects all meas runs!)
#logger.info("Sending server shutdown request...")
#client.server.shutdown()
