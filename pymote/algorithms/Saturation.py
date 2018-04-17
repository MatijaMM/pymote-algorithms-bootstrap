from pymote.algorithm import NodeAlgorithm
from pymote.message import Message
import random

class Saturation(NodeAlgorithm):
    required_params = {}
    default_params = {'neighborsKey': 'Neighbors', 'numNeighboursKey': 'numNeighbours'}

    def initializer(self):
        ini_nodes = []
        isInitiator = False

        for node in self.network.nodes():
            node.memory[self.neighborsKey] = node.memory['neighborsTree']
            
            node.memory[self.numNeighboursKey] = len(node.memory[self.neighborsKey])
            node.status = 'AVAILABLE'

            isInitiator = random.choice([True, False])
            if isInitiator:
                ini_nodes.append(node)

        for ini_node in ini_nodes:
            self.network.outbox.insert(0, Message(header=NodeAlgorithm.INI,
                                                  destination=ini_node))

    def available(self, node, message):

        if message.header == NodeAlgorithm.INI:
            status = 'ACTIVE'
            destination_nodes = list(node.memory[self.neighborsKey])
            header = 'Activate'
            node.send(Message(destination=destination_nodes,
                              header=header,
                              data="Activate"))

            if len(destination_nodes) == 1:
                status = 'PROCESSING'
                header = 'Message'
                #zapisi parenta
                node.send(Message(destination=destination_nodes,
                              header=header,
                              data="Message"))
            else:
                status = 'ACTIVE'

        elif (message.header == 'Activate'):
            header = 'Activate'
            destination_nodes = list(node.memory[self.neighborsKey])
            destination_nodes.remove(message.source)
            node.send(Message(destination=destination_nodes,
                              header=header,
                              data="Activate"))

            destination_nodes = list(node.memory[self.neighborsKey])
            if len(destination_nodes) == 1:
                status = 'PROCESSING'
                header = 'Message'
                #zapisi parenta
                node.send(Message(destination=destination_nodes,
                              header=header,
                              data="Message"))
            else:
                status = 'ACTIVE'

        node.status = status

    def active(self, node, message):
        status = 'ACTIVE'

        if (message.header == 'Message'):
            destination_nodes = list(node.memory[self.neighborsKey])
            destination_nodes.remove(message.source)
            node.memory[self.neighborsKey] = destination_nodes
            
            if len(destination_nodes) == 1:
                status = 'PROCESSING'
                header = 'Message'
                #zapisi parenta
                node.send(Message(destination=destination_nodes,
                              header=header,
                              data="Message"))

        node.status = status

    def processing(self, node, message):
        status = 'PROCESSING'
        if (message.header == 'Message'):
            status = 'SATURATED'
        node.status = status

    def saturated():
        return


    STATUS = {
        'ACTIVE': active,
        'AVAILABLE': available,
        'PROCESSING': processing,
        'SATURATED': saturated
    }