from pymote.algorithms.KVM.PTConstruction import PTConstruction
from pymote.networkgenerator import NetworkGenerator
from pymote.npickle import write_pickle
from pymote.simulation import Simulation
from pymote.network import Network
import networkx as nx
import random

#generiraj random mrezu, dodaj PTConstruction algoritam i prikazi mrezu
net_gen = NetworkGenerator(6)
net = net_gen.generate_random_network()
net.algorithms = (PTConstruction,)
net.show()

#zapisi mrezu
write_pickle(net, 'pt_mreza3.tar.gz')

#pokreni simulaciju
sim = Simulation(net)
sim.run()

#kad se simulacija zavrsi, prikazi id, memoriju i status svakog svora
print "\n"
for node in net.nodes():
    print node.id, node.memory, node.status
    print " "
#sim.reset()


#inicijaliziraj tmp routing listu, i postavi brojac greski na 0
tmpPathList = []
errorResultCounter = 0
#prolazi svaki par cvorova
for node in net.nodes():
    for node2 in net.nodes():
        #ako cvorovi nisu jednaki
        if not node == node2:
            #uzmi sve nakrace puteve izmedju para cvorova
            tmpPathList = [p for p in nx.all_shortest_paths(net,source=node,target=node2, weight='weight')]
            #uzmi najkraci put dobiven iz algoritma
            shortestPath = node.memory['routingTable'][node2]
            #makni sebe iz liste najkracih puteva
            for l in tmpPathList:
                l.remove(node)
            #provjeri ako je algoritam dobio najkraci put, ako nije povecaj brojac greski
            if shortestPath not in tmpPathList:
                errorResultCounter += 1

#ispisi broj gresaka i obavijesti o zavrsetku algoritma
print "\nERRORS: " + str(errorResultCounter)
print "\nDone script."
