from pymote.algorithms.BuildTree import BuildTree
from pymote.algorithms.Saturation import Saturation

from pymote.algorithms.broadcast import Flood
from pymote.networkgenerator import NetworkGenerator
from pymote.simulation import Simulation

from pymote.npickle import write_pickle

net_gen = NetworkGenerator(5)

net = net_gen.generate_random_network()
net.algorithms = ( (BuildTree, {'informationKey':'I'}), (Saturation, {}))
net.nodes()[0].memory['I'] = "Koja je tvoja temperatura?"

net.show()

write_pickle(net, 'sat_mreza.tar.gz')

sim = Simulation(net)
sim.run()

for node in net.nodes():
	print node.id, node.memory, node.status

#sim.reset()	
print "\nDone script."