from pymote.algorithm import NodeAlgorithm
from pymote.message import Message
import random

class Saturation(NodeAlgorithm):
    default_params = {'neighborsKey': 'Neighbors', 'tempNeighborsKey': 'tempNeighbors', 'parentKey': 'parent'}

    def initializer(self):
        ini_nodes = []
        isInitiator = False

        for node in self.network.nodes():
            self.initialize(node)

            node.memory[self.neighborsKey] = node.memory['neighborsTree']
            node.memory[self.tempNeighborsKey] = node.memory['neighborsTree']
            
            node.status = 'AVAILABLE'

            isInitiator = random.choice([True, False])
            if isInitiator:
                ini_nodes.append(node)

        for ini_node in ini_nodes:
            self.network.outbox.insert(0, Message(header=NodeAlgorithm.INI, destination=ini_node))

    def available(self, node, message):
        #Spontaineosly
        if message.header == NodeAlgorithm.INI:

            destination_nodes = list(node.memory[self.neighborsKey])
            header = 'Activate'
            node.send(Message(destination=destination_nodes, header=header))

            #self.initialize(node)

            node.memory[self.tempNeighborsKey] = destination_nodes

            if len(destination_nodes) == 1:
                new_message = self.prepare_message(node, message)
                node.memory[self.parentKey] = destination_nodes[0]
                node.send(Message(destination=node.memory[self.parentKey],
                              header=new_message.header,
                              data=new_message.data))
                status = 'PROCESSING'
            else:
                status = 'ACTIVE'

        elif (message.header == 'Activate'):
            header = 'Activate'
            destination_nodes = list(node.memory[self.neighborsKey])
            destination_nodes.remove(message.source)
            node.send(Message(destination=destination_nodes, header=header))

            #self.initialize(node)

            destination_nodes = list(node.memory[self.neighborsKey])
            node.memory[self.tempNeighborsKey] = destination_nodes

            if len(destination_nodes) == 1:
                new_message = self.prepare_message(node, message)
                node.memory[self.parentKey] = destination_nodes[0]
                node.send(Message(destination=node.memory[self.parentKey], header=new_message.header,data=new_message.data))
                status = 'PROCESSING'
            else:
                status = 'ACTIVE'

        node.status = status

    def active(self, node, message):
        status = 'ACTIVE'

        if (message.header == 'Message'):
            self.process_message(node, message)

            destination_nodes = list(node.memory[self.tempNeighborsKey])
            destination_nodes.remove(message.source)
            node.memory[self.tempNeighborsKey] = destination_nodes

            if len(destination_nodes) == 1:
                new_message = self.prepare_message(node, message)
                node.memory[self.parentKey] = destination_nodes[0]
                node.send(Message(destination=node.memory[self.parentKey],
                              header=new_message.header,
                              data=new_message.data))
                status = 'PROCESSING'

        node.status = status

    def processing(self, node, message):
        if (message.header == 'Message'):
            self.process_message(node, message)
            self.resolve(node, message)

    def saturated():
        pass

    def initialize(self, node):
        pass

    def prepare_message(self, node, message):
        message.header = 'Message'
        message.data = None
        return message

    def process_message(self, node, message):
        pass

    def resolve(self, node, message):
        node.status = 'SATURATED'
        #START RESOLUTION STAGE

    STATUS = {
        'ACTIVE': active,
        'AVAILABLE': available,
        'PROCESSING': processing,
        'SATURATED': saturated
    }