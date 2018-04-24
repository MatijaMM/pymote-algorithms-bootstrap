from pymote.algorithms.buildTreeKVM import BuildTree
from pymote.algorithms.eccenrictiesKVM import Eccenricties
from pymote.algorithms.saturationKVM import Saturation
#from pymote.algorithms.centerKVM import Center
from pymote.algorithms.centerKVM import Center

#from pymote.algorithms.broadcast import Flood
from pymote.networkgenerator import NetworkGenerator
from pymote.network import Network
from pymote.simulation import Simulation

#from pymote.npickle import write_pickle

net_gen = NetworkGenerator(5)

net = net_gen.generate_random_network()
"""
net = Network()
root=net.add_node(pos=[300,500])
root.commRange=150
node=net.add_node(pos=[200,400])
node.commRange=150
node=net.add_node(pos=[400,400])
node.commRange=150

node=net.add_node(pos=[100,300])
node.commRange=150

node=net.add_node(pos=[250,300])
node.commRange=150
node=net.add_node(pos=[500,300])
node.commRange=150
node=net.add_node(pos=[450,200])
node.commRange=150
node=net.add_node(pos=[10,200])
node.commRange=150
"""

#NAPOMENA: u saturated makla random initiatore
net.algorithms = (BuildTree, Center)
#net.nodes()[0].memory['I'] = "Koja je tvoja temperatura?"

net.show()

write_pickle(net, 'sat_mreza.tar.gz')

sim = Simulation(net)
sim.run()

for node in net.nodes():
    print "\n"
    print node.id, node.memory, node.status

#sim.reset()	
print "\nDone script."