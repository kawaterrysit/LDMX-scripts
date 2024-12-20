from LDMX.Framework import ldmxcfg
p = ldmxcfg.Process('test')

p.maxTriesPerEvent = 10000

from LDMX.Biasing import target
det = 'ldmx-det-v14-8gev'
mySim = target.dark_brem(
    #A' mass in MeV - set in init.sh to same value in GeV
    10.0,
    # library path is uniquely determined by arguments given to `dbgen run` in init.sh
    #   easiest way to find this path out is by running `. init.sh` locally to see what
    #   is produced
    'electron_tungsten_MaxE_8.0_MinE_4.0_RelEStep_0.1_UndecayedAP_mA_0.01_run_1',
    det
)

p.sequence = [ mySim ]

##################################################################
# Below should be the same for all sim scenarios

import os
import sys

LDMX_NUM_EVENTS = 10000
p.totalEvents = int(LDMX_NUM_EVENTS) // 2
p.run = int(LDMX_NUM_EVENTS)

p.histogramFile = f'hist.root'
p.outputFiles = [f'events.root']
p.termLogLevel = 0

import LDMX.Ecal.EcalGeometry
import LDMX.Ecal.ecal_hardcoded_conditions
import LDMX.Hcal.HcalGeometry
import LDMX.Hcal.hcal_hardcoded_conditions
import LDMX.Ecal.digi as ecal_digi
import LDMX.Ecal.vetos as ecal_vetos
import LDMX.Hcal.digi as hcal_digi

from LDMX.TrigScint.trigScint import TrigScintDigiProducer
from LDMX.TrigScint.trigScint import TrigScintClusterProducer
from LDMX.TrigScint.trigScint import trigScintTrack
'''
ts_digis = [
        TrigScintDigiProducer.pad1(),
        TrigScintDigiProducer.pad2(),
        TrigScintDigiProducer.pad3(),
        ]
for d in ts_digis :
    d.randomSeed = 1

'''
from LDMX.Recon.electronCounter import ElectronCounter
from LDMX.Recon.simpleTrigger import TriggerProcessor

'''
count = ElectronCounter(1,'ElectronCounter')
count.input_pass_name = ''
'''

from LDMX.DQM import dqm

p.sequence.extend([
        ecal_digi.EcalDigiProducer(),
        ecal_digi.EcalRecProducer(), 
#        ecal_vetos.EcalVetoProcessor(),
#        count, TriggerProcessor('trigger', 8000.),
#        dqm.DarkBremInteraction()
        ] + dqm.all_dqm)
