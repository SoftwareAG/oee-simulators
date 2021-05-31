FROM python:2

# general simulator
ADD simulator.py /

# duerr simulator
ADD duerr_simulator.py /
ADD duerr_alarmlog.csv /
ADD duerr_measurements /duerr_measurements

# asm simulator
ADD asm_simulator.py /
ADD asmEventLog.csv /
ADD asmEventMetadata.csv /

# dmg mori simulator
ADD dmg_simulator.py /
ADD dmg_machineData.csv /
ADD dmg_metadata.csv /

RUN pip install requests

# Comment out the simulator you want to run
#CMD [ "python", "./simulator.py" ]
#CMD [ "python", "./duerr_simulator.py" ]
#CMD [ "python", "./asm_simulator.py" ]
CMD [ "python", "./dmg_simulator.py" ]
