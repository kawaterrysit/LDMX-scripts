import os
import sys

from LDMX.Framework import ldmxcfg

thisPassName = 'test'
p=ldmxcfg.Process(thisPassName)

p.termLogLevel = 0
# This need to be set but has no meaning given p.totalEvents
p.maxEvents = 1
# kaon-focused sample takes about twice as long as normal PN,
# so we ask for half as many events such that validation jobs stay
# time-limited by the PN
LDMX_NUM_EVENTS = 10000
p.totalEvents = int(LDMX_NUM_EVENTS) // 2
p.run = int(LDMX_NUM_EVENTS)

from LDMX.SimCore import generators as gen
from LDMX.SimCore import bias_operators
from LDMX.SimCore import kaon_physics
from LDMX.SimCore import photonuclear_models as pn
from LDMX.Biasing import ecal
from LDMX.Biasing import filters
from LDMX.Biasing import particle_filter
from LDMX.Biasing import util
from LDMX.Biasing import include as includeBiasing

detector = 'ldmx-det-v14-8gev'
generator=gen.single_8gev_e_upstream_tagger()
bias_factor = 550.
bias_treshold = 5000.

mySim = ecal.photo_nuclear(detector, generator)
mySim.description = f'8 GeV ECal Kaon PN simulation, xsec bias {bias_factor}' 
mySim.biasing_operators = [ bias_operators.PhotoNuclear('ecal',bias_factor,bias_treshold,only_children_of_primary = True) ]

# Configure the sequence in which user actions should be called.
includeBiasing.library()
mySim.actions.clear()
mySim.actions.extend([
        filters.TaggerVetoFilter(thresh=2*3800.),
        # Only consider events where a hard brem occurs
        filters.TargetBremFilter(recoil_max_p = 2*1500.,brem_min_e = 2*2500.),
        # Only consider events where a PN reaction happnes in the ECal
        filters.EcalProcessFilter(),
        # Tag all photo-nuclear tracks to persist them to the event.
        util.TrackProcessFilter.photo_nuclear()
])

# set up "upKaon" parameters which reduces the charged kaon lifetimes by a factor 1/50
# and forces decays to be into one of the leptonic decay modes.
mySim.kaon_parameters = kaon_physics.KaonPhysics.upKaons()

# Alternative pn models
myModel = pn.BertiniAtLeastNProductsModel.kaon() 
# Count all (not stopped) particles as "hard"
myModel.hard_particle_threshold=0.
# Apply the model to any nucleus
myModel.zmin = 0
# Apply the model for photonuclear reactions with > 5000 MeV photons
myModel.emin = 5000.
# PDG ids for K^0_L, K^0_S, K^0, K^+, and K^- respectively
myModel.pdg_ids = [130, 310, 311, 321, -321]
# Require at least 1 hard particle from the list above
myModel.min_products = 1

# Change the default model to the kaon producing model
mySim.photonuclear_model = myModel

# Add the filter at the end of the current list of user actions. 
# Filter for events with a kaon daughter
myFilter = particle_filter.PhotoNuclearProductsFilter.kaon()
mySim.actions.extend([myFilter])

# Loading calorimeter and TS processors
import LDMX.Ecal.EcalGeometry
import LDMX.Ecal.ecal_hardcoded_conditions
import LDMX.Hcal.HcalGeometry
import LDMX.Hcal.hcal_hardcoded_conditions

from LDMX.Ecal import digi as eDigi
from LDMX.Ecal import vetos
from LDMX.Hcal import digi as hDigi
from LDMX.Hcal import hcal
                                                                                                      
from LDMX.TrigScint.trigScint import TrigScintDigiProducer
from LDMX.TrigScint.trigScint import TrigScintClusterProducer
from LDMX.TrigScint.trigScint import trigScintTrack

from LDMX.Recon.electronCounter import ElectronCounter

#TS digi + clustering + track chain
tsDigisDown  =TrigScintDigiProducer.pad1()
tsDigisTag   =TrigScintDigiProducer.pad2()
tsDigisUp    =TrigScintDigiProducer.pad3()

tsDigis = [tsDigisDown, tsDigisTag, tsDigisUp]
for d in tsDigis :
    d.randomSeed = 1

tsClustersDown  =TrigScintClusterProducer.pad1()
tsClustersTag  =TrigScintClusterProducer.pad2()
tsClustersUp  =TrigScintClusterProducer.pad3()

tsClustersDown.input_collection = tsDigisDown.output_collection
tsClustersTag.input_collection = tsDigisTag.output_collection
tsClustersUp.input_collection = tsDigisUp.output_collection

#make sure to pick up the right pass 
tsClustersTag.input_pass_name = thisPassName 
tsClustersUp.input_pass_name = tsClustersTag.input_pass_name
tsClustersDown.input_pass_name = tsClustersTag.input_pass_name

trigScintTrack.input_pass_name = thisPassName
trigScintTrack.seeding_collection = tsClustersTag.output_collection



layerZPositions = [ 
    7.932, 14.532, 32.146, 40.746, 58.110, 67.710, 86.574, 96.774, 115.638, 125.838, 
    144.702, 154.902, 173.766, 183.966, 202.830, 213.030, 231.894, 242.094, 260.958, 
    271.158, 290.022, 300.222, 319.086, 329.286, 351.650, 365.250, 387.614, 401.214, 
    423.578, 437.178, 459.542, 473.142, 495.506, 509.106
]

layer_ZPos_diff = np.round(np.diff(layerZPositions), decimals=0)


# Taking absolute values, remove duplicates,and sort the differences from smallest to largest
layer_ZPos_diff = sorted(list(set([abs(x) for x in layer_ZPos_diff])))

# ECAL part
ecalReco   =eDigi.EcalRecProducer()
ecalDigi = eDigi.EcalDigiProducer()
ecalVeto   =vetos.EcalVetoProcessor()
ecalVeto.linreg_dist = float(layer_ZPos_diff[7])

# HCAL part
hcalDigi   =hDigi.HcalDigiProducer()
hcalReco   =hDigi.HcalRecProducer()
hcalVeto   =hcal.HcalVetoProcessor()

# electron counter for trigger processor 
eCount = ElectronCounter( 1, "ElectronCounter") # first argument is number of electrons in simulation
eCount.input_pass_name = ''
from LDMX.Recon.simpleTrigger import TriggerProcessor
simpleTrig = TriggerProcessor("simpleTrig",8000.)
simpleTrig.input_pass=thisPassName

# Load DQM 
from LDMX.DQM import dqm

p.sequence=[ 
        mySim, 
        ecalDigi, 
        ecalReco, 
        ecalVeto,
        *tsDigis, 
        tsClustersTag,
        tsClustersUp,
        tsClustersDown, 
        trigScintTrack, 
        eCount, 
        simpleTrig, 
        hcalDigi, 
        hcalReco, 
        hcalVeto,
        dqm.PhotoNuclearDQM(verbose=False)
        ]

p.sequence.extend(dqm.all_dqm)


p.histogramFile = f'hist.root'
p.outputFiles = [f'events.root']
