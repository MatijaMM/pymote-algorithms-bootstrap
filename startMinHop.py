from pymote.algorithms.KVM.MinHopRouting import MinHopRouting
from pymote.networkgenerator import NetworkGenerator
from pymote.npickle import write_pickle
from pymote.simulation import Simulation
from pymote.network import Network
import networkx as nx

#generate random network
net_gen = NetworkGenerator(15)
net = net_gen.generate_random_network()
#add MinHopRouting algorithm and show the network
net.algorithms = (MinHopRouting,)
net.show()

#write network to file
write_pickle(net, 'minMreza.tar.gz')

#start simulation
sim = Simulation(net)
sim.run()

#after simulation write node memory and status
print "\n"
for node in net.nodes():
    print node.id, node.memory, node.status
    print str(len(node.memory['routingTable']))
    print " "
#sim.reset()

#initialize tmp routing list, set error counter to 0
tmpPathList = []
errorResultCounter = 0

#go through every node pair
for node in net.nodes():
    for node2 in net.nodes():
        #if nodes are not equal
        if not node == node2:
            #set all the shortest paths between nodes
            tmpPathList = [p for p in nx.all_shortest_paths(net,source=node,target=node2)]
            #add current node to beginning of list
            shortestPath = [node]
            #set next hop node
            n = node.memory['routingTable'][node2]
            #while n is not target node
            while n != node2:
                #add n to list
                shortestPath.append(n)
                #set next hop node
                n = n.memory['routingTable'][node2]
            #lastly, add target node to list
            shortestPath.append(node2)
            #if the path from algorithm is not in shortest path list, increase error counter
            if shortestPath not in tmpPathList:
                errorResultCounter += 1

#report error number
print "\nERRORS: " + str(errorResultCounter)
print "\nDone script."

