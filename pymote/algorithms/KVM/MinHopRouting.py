from pymote.algorithm import NodeAlgorithm
from pymote.message import Message
import random
import math
import sys

class MinHopRouting(NodeAlgorithm):

    default_params = {'neighborsKey': 'Neighbors', 'sourceKey': 'source', 'myDistanceKey': 'myDistance', 'ackCountKey': 'ackCount', 
                      'iterationKey': 'iteration', 'childrenKey': 'children', 'activeChildrenKey': 'activeChildren', 'unvisitedKey': 'unvisited',
                      'parentKey': 'parent', 'iterationCompletedCounterKey':'iterationCompletedCounter', 'terminateCouterKey': 'terminateCouter',
                      'routingTableKey': 'routingTable', 'routingListKey': 'routingList', 'masterKey': 'master', 'macroIterationKey': 'macroIteration',
                      'masterChildrenKey': 'masterChildren', 'masterParentKey': 'masterParent', 'tokenNeighboursKey': 'tokenNeighbours'}

    def initializer(self):
        #first node is initiator
        ini_node = self.network.nodes()[0]

        #initialize all variables
        for node in self.network.nodes():
            node.memory[self.neighborsKey] = \
                node.compositeSensor.read()['Neighbors']
            self.initializeVariables(node, False)
            node.status = 'IDLE'

        #set initiator variables
        ini_node.status = 'INITIATOR'
        ini_node.memory[self.masterKey] = True
        ini_node.memory[self.macroIterationKey] = 0

        #send Spontainously message
        self.network.outbox.insert(0, Message(header=NodeAlgorithm.INI,destination=ini_node))

    def initiator(self, node, message):
        if message.header == NodeAlgorithm.INI:
            #set initiator flag
            node.memory[self.sourceKey] = True
            #add neighbours to unvisited
            node.memory[self.unvisitedKey] = node.memory[self.neighborsKey]
            #set ack counter to len of neighbours
            node.memory[self.ackCountKey] = len(node.memory[self.neighborsKey])
            #send Explore message
            node.send(Message(header='Explore',
                              data=[1, node.memory[self.macroIterationKey]],
                              destination=node.memory[self.neighborsKey]))

        elif message.header == "Ack" and message.data[0] == 'Positive':
            #count received responses from neighbors
            node.memory[self.ackCountKey] -= 1
            #add initiator neighbors (i=1) to its childrend
            children = list(node.memory[self.childrenKey])
            children.append(message.source)
            node.memory[self.childrenKey] = children
            #add source to routing table
            node.memory[self.routingTableKey][message.source] = message.source
            #add initiator neighbors (i=1) to its activeChildrend (not done)
            activeChildren = list(node.memory[self.activeChildrenKey])
            activeChildren.append(message.source)
            node.memory[self.activeChildrenKey] = activeChildren
            #remove visited node from unvisited list
            unvisited = list(node.memory[self.unvisitedKey])
            unvisited.remove(message.source)
            node.memory[self.unvisitedKey] = unvisited

            #if all responses received start new iteration on new level (new distance)
            if (node.memory[self.ackCountKey] == 0):
                #send explore message to nodes on next iteration (distance)
                iteration = message.data[1] + 1
                node.send(Message(header='Start Iteration',
                                  data=iteration,
                                  destination=node.memory[self.childrenKey]))
                node.status = 'ACTIVE'

    def idle(self, node, message):
        if message.header == 'Explore':
            #initialize unvisited array for all nodes (except initiator)
            if node.memory[self.macroIterationKey] < message.data[1]:
                #add all neighbours to unvisited
                node.memory[self.unvisitedKey] = node.memory[self.neighborsKey]
                #save distance 
                node.memory[self.myDistanceKey] = message.data[0]
                #save macroiteration
                node.memory[self.macroIterationKey] = message.data[1]
                #mark sender as parent
                node.memory[self.parentKey] = message.source
                #remove visited node (source) from unvisited list
                unvisited = list(node.memory[self.unvisitedKey])
                unvisited.remove(message.source)
                node.memory[self.unvisitedKey] = unvisited
                #initialize ack counter for all nodes (except initiator)
                node.memory[self.ackCountKey] = len(unvisited)
                #send positive ack to parent
                node.send(Message(header='Ack',
                                 data=['Positive', message.data[0]],
                                 destination=node.memory[self.parentKey]))
                node.status = 'ACTIVE'
            else:
                #send negative ack
                node.send(Message(header='Ack',
                                 data=['Negative', message.data[0]],
                                 destination=message.source))

        elif message.header == 'Token':
            #if routing table is empty
            if not node.memory[self.routingTableKey]:
                #set macro iteration
                node.memory[self.macroIterationKey] = message.data+1
                #send Spontainously to start new macro iteration
                node.send(Message(header=NodeAlgorithm.INI,
                              destination=node))
                node.status = 'INITIATOR'

            else:
                if node.memory[self.tokenNeighboursKey]:
                    #increase macro iteration
                    node.memory[self.macroIterationKey]+=1
                    #set token neighbour
                    tokenNeighbour = node.memory[self.tokenNeighboursKey][0]
                    #send Token message to token neighbour
                    node.send(Message(header='Token',
                                  data=node.memory[self.macroIterationKey],
                                  destination=tokenNeighbour))
                    #remove this neighbour from the list
                    tokenNeighbours = list(node.memory[self.tokenNeighboursKey])
                    tokenNeighbours.remove(tokenNeighbour)
                    node.memory[self.tokenNeighboursKey] = tokenNeighbours
                else:
                    #if node is not master
                    if not node.memory[self.masterKey]:
                        #send Token to parent
                        node.send(Message(header='Token',
                                  data=node.memory[self.macroIterationKey],
                                  destination=node.memory[self.masterParentKey]))
                    #if node is master
                    else:
                        #send Done to master children 
                        node.send(Message(header='Done',
                                  destination=node.memory[self.masterChildrenKey]))
                        node.status = "DONE"

        elif message.header == 'Done':
            #send Done to master children
            node.send(Message(header='Done',
                             destination=node.memory[self.masterChildrenKey]))
            node.status = 'DONE'

    def active(self, node, message):
        if message.header == 'Ack':
            if message.data[0] == 'Positive':
                #count received responses from neighbors
                node.memory[self.ackCountKey] -= 1
                #add sender to routingList
                node.memory[self.routingListKey].append(message.source)
                #add initiator neighbors (i=1) to its childrend
                children = list(node.memory[self.childrenKey])
                children.append(message.source)
                node.memory[self.childrenKey] = children
                #add initiator neighbors (i=1) to its activeChildrend (not done)
                activeChildren = list(node.memory[self.activeChildrenKey])
                activeChildren.append(message.source)
                node.memory[self.activeChildrenKey] = activeChildren
                #remove visited node (source) from unvisited list
                unvisited = list(node.memory[self.unvisitedKey])
                unvisited.remove(message.source)
                node.memory[self.unvisitedKey] = unvisited

            else: #message.data[0] == 'Negative'
                #count received responses from neighbors
                node.memory[self.ackCountKey] -= 1
                #remove visited node (source) from unvisited list
                unvisited = list(node.memory[self.unvisitedKey])
                if message.source in unvisited:
                    unvisited.remove(message.source)
                    node.memory[self.unvisitedKey] = unvisited

            #initialize ack counter for all nodes (except initiator)
            #node.memory[self.ackCountKey] = len(unvisited)
            if node.memory[self.ackCountKey] == 0: 
                #send iteration completed to parent when new node is added to tree
                node.send(Message(header='Iteration Completed',
                                  data=[message.data[1], node.memory[self.routingListKey]], #proslijedi br iteracije (distance)
                                  destination=node.memory[self.parentKey]))

        if message.header == 'Iteration Completed':
            #increase iteration completed counter
            node.memory[self.iterationCompletedCounterKey] += 1
            #set active children
            activeChildren = list(node.memory[self.activeChildrenKey])
            #if node is initiator, and there is routing list in message, add the list to routing table
            if node.memory[self.sourceKey] and message.data[1]:
                for n in message.data[1]:
                        node.memory[self.routingTableKey][n] = message.source
            #if node is not initiator and there is routing list in message
            elif message.data[1]:
                #add every node from the message list to node routing list
                for n in message.data[1]:
                    routingList = node.memory[self.routingListKey]
                    routingList.append(n)
                    node.memory[self.routingListKey] = routingList

            #if all iteration completed messages are received
            if node.memory[self.iterationCompletedCounterKey] == len(activeChildren):
                #reset counter
                node.memory[self.iterationCompletedCounterKey] = 0
                #if node is not initator
                if not (node.memory[self.sourceKey]):
                    #send iteration completed to parent when new node is added to tree
                    node.send(Message(header='Iteration Completed',
                                      data=[message.data[0], node.memory[self.routingListKey]], #proslijedi br iteracije (distance)
                                      destination=node.memory[self.parentKey]))
                #if node is initiator
                else:
                    #add every node from message routing list to node routing table
                    for n in message.data[1]:
                        node.memory[self.routingTableKey][n] = message.source
                    #increase iteration number (distance)
                    iteration = message.data[0] + 1
                    #send start iteration message to active children
                    node.send(Message(header='Start Iteration',
                                      data=iteration+1,
                                      destination=node.memory[self.activeChildrenKey]))
          
        if message.header == 'Start Iteration':
            #set unvisited, activeChildren, reset routing list
            unvisited = list(node.memory[self.unvisitedKey])
            activeChildren = list(node.memory[self.activeChildrenKey])
            node.memory[self.routingListKey] = []
        
            if ( ((node.memory[self.myDistanceKey] <= (message.data - 1)) and (node.memory[self.myDistanceKey] != 0) ) ):
                #set destination to unvisited nodes
                destination = node.memory[self.unvisitedKey]
                #set ack counter to len of unvisited nodes
                node.memory[self.ackCountKey] = len(destination)
                #if there are unvisited nodes
                if destination:
                    #node.memory[self.ackCountKey] = len(unvisited)
                    #send explore message to unvisited nodes
                    node.send(Message(header='Explore',
                                      data=[message.data, node.memory[self.macroIterationKey]], 
                                      destination=destination))
                #if there are active childern (not done)
                elif activeChildren:
                    #send start iteration to them
                    node.send(Message(header='Start Iteration',
                                  data=message.data,
                                  destination=node.memory[self.activeChildrenKey]))
                #if node is leaf
                else:
                    #send Terminate message to parent
                    node.send(Message(header='Terminate',
                                  data=message.data,
                                  destination=node.memory[self.parentKey]))

                    self.initializeVariables(node)

                    node.status = 'IDLE'
            else:
                #set distance to message data
                node.memory[self.myDistanceKey] = message.data
                #set parent to message source
                node.memory[self.parentKey] = message.source
                #send positive ack to parent
                node.send(Message(header='Ack',
                                  data=['Positive', message.data],
                                  destination=node.memory[self.parentKey]))

        if message.header == 'Explore':
            #if node distance is already calculated, he is already in tree
            if ( node.memory[self.myDistanceKey] != 0 ):
                #send negative ack to parent
                node.send(Message(header='Ack',
                                  data=['Negative', message.data[0]],
                                  destination=message.source))
            #if node not in tree (first next neighbor)
            else:
                #set distance to message data
                node.memory[self.myDistanceKey] = message.data[0]
                #set parent to message source
                node.memory[self.parentKey] = message.source
                #send positive ack to parent
                node.send(Message(header='Ack',
                                  data=['Positive', message.data[0]],
                                  destination=node.memory[self.parentKey]))

        if message.header == 'Terminate':
            #increase terminate counter
            node.memory[self.terminateCouterKey] += 1
            #remove message sender from activeChildrend (not done)
            activeChildren = list(node.memory[self.activeChildrenKey])
            activeChildren.remove(message.source)
            node.memory[self.activeChildrenKey] = activeChildren
            #if there are active children(node done) and all the iteration completed messages are received
            if activeChildren and (node.memory[self.iterationCompletedCounterKey] == len(activeChildren)):
                #reset counter
                node.memory[self.iterationCompletedCounterKey] = 0
                #if node is not initiator
                if not node.memory[self.sourceKey]:
                    #send iteration completed to parent with iteration number (distance)
                    node.send(Message(header='Iteration Completed',
                                  data=[message.data, node.memory[self.routingListKey]],
                                  destination=node.memory[self.parentKey]))
                #if node is initiator
                else:
                    #send start iteration with distance to active children
                    node.send(Message(header='Start Iteration',
                                  data=message.data,
                                  destination=node.memory[self.activeChildrenKey]))                    
            children = list(node.memory[self.childrenKey])
            #if all termination messages are received
            if node.memory[self.terminateCouterKey] == len(children):
                #if node is not initiator
                if not node.memory[self.sourceKey]:
                    #send Terminate message to parent
                    node.send(Message(header='Terminate',
                                      data=message.data,
                                      destination=node.memory[self.parentKey]))
                    
                    self.initializeVariables(node)

                    node.status = 'IDLE'
                #if node is initator
                else:
                    self.initializeVariables(node)

                    #if token neighbours are set
                    if node.memory[self.tokenNeighboursKey]:
                        #save first token neighbour
                        tokenNeighbour = node.memory[self.tokenNeighboursKey][0]
                        #send token to that node
                        node.send(Message(header='Token',
                                      data=node.memory[self.macroIterationKey],
                                      destination=tokenNeighbour))
                        #remove that node from token neighbours
                        tokenNeighbours = list(node.memory[self.tokenNeighboursKey])
                        tokenNeighbours.remove(tokenNeighbour)
                        node.memory[self.tokenNeighboursKey] = tokenNeighbours
                        node.status = 'IDLE'
                    else:
                        #if node is not master(first) initator
                        if not node.memory[self.masterKey]:
                            #send Token message to master parent
                            node.send(Message(header='Token',
                                      data=node.memory[self.macroIterationKey],
                                      destination=node.memory[self.masterParentKey]))
                            node.status = 'IDLE'
                        #if node is master initiator
                        else:
                            #send Done message to master children
                            node.send(Message(header='Done',
                                      destination=node.memory[self.masterChildrenKey]))
                            node.status='DONE'

    def done(self, node, message):
        pass

    def initializeVariables(self, node, macro=True): 
        #if it's the start of the algorithm
        if not macro:
            node.memory[self.masterKey] = False
            node.memory[self.masterChildrenKey] = []
            node.memory[self.masterParentKey] = None
            node.memory[self.macroIterationKey] = -1
            node.memory[self.tokenNeighboursKey] = []
            node.memory[self.routingTableKey] = dict()
            #if this is first iteration
            
        #else it's the start of new macroiteration
        else:
            if node.memory[self.macroIterationKey] == 0:
                node.memory[self.masterChildrenKey] = node.memory[self.childrenKey]
                node.memory[self.masterParentKey] = node.memory[self.parentKey]
                node.memory[self.tokenNeighboursKey] = node.memory[self.childrenKey]
            

        #reset other variables
        node.memory[self.sourceKey] = False
        node.memory[self.myDistanceKey] = 0
        node.memory[self.childrenKey] = []
        node.memory[self.parentKey] = None
        node.memory[self.activeChildrenKey] = []
        node.memory[self.iterationCompletedCounterKey] = 0
        node.memory[self.terminateCouterKey] = 0
        node.memory[self.unvisitedKey] = []
        node.memory[self.routingListKey] = []
        node.memory[self.ackCountKey] = 0
    




    STATUS = {
        'INITIATOR': initiator,
        'IDLE': idle,
        'ACTIVE': active,
        'DONE': done
    }