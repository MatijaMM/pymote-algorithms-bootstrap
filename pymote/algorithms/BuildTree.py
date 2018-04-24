from pymote.algorithm import NodeAlgorithm
from pymote.message import Message


class BuildTree(NodeAlgorithm):
    required_params = ('informationKey',)
    default_params = {'neighborsKey': 'Neighbors', 'numNeighboursKey': 'numNeighbours',
                      'pathKey': 'path', 'numReceived': 'numReceived',
                      'isReceivedKey': 'isReceived', 'neighborsTreeKey': 'neighborsTree'}

    def initializer(self):
        ini_nodes = []
        for node in self.network.nodes():
            node.memory[self.neighborsKey] = \
                node.compositeSensor.read()['Neighbors']
            node.status = 'IDLE'
            node.memory[self.numReceived] = 0
            node.memory[self.isReceivedKey] = False
            node.memory[self.numNeighboursKey] = len(node.memory[self.neighborsKey])
            node.memory[self.neighborsTreeKey] = []
            if self.informationKey in node.memory:
                node.status = 'INITIATOR'
                node.memory[self.neighborsTreeKey] = node.memory[self.neighborsKey]

                ini_nodes.append(node)
        for ini_node in ini_nodes:
            self.network.outbox.insert(0, Message(header=NodeAlgorithm.INI,
                                                  destination=ini_node))

    def initiator(self, node, message):
        if message.header == NodeAlgorithm.INI:
            node.send(Message(header='Information',
                              data=node.memory[self.informationKey]))


        elif (message.header == 'Max Temperature'):
            node.memory[self.numReceived] += 1
            if node.memory[self.numReceived] == node.memory[self.numNeighboursKey]:
                node.status = 'AVAILABLE'

    def idle(self, node, message):
        header = 'Information'
        status = 'IDLE'

        if message.header == 'Information' and not (node.memory[self.isReceivedKey]):

            node.memory[self.isReceivedKey] = True

            destination_nodes = list(node.memory[self.neighborsKey])
            node.memory[self.pathKey] = message.source
            destination_nodes.remove(message.source)

            treePath = list(node.memory[self.neighborsTreeKey])
            treePath.append(message.source)
            node.memory[self.neighborsTreeKey] = treePath


            if destination_nodes:
                for destination_node in destination_nodes:
                    if destination_node.status == 'INITIATOR':
                        destination_nodes.remove(destination_node)

            else:
                header = 'Max Temperature'
                destination_nodes = message.source
                status = 'AVAILABLE'

            node.send(Message(destination=destination_nodes,
                              header=header))

        else:
            node.memory[self.numReceived] += 1

            if (message.header == 'Max Temperature'):
                treePath = list(node.memory[self.neighborsTreeKey])
                treePath.append(message.source)
                node.memory[self.neighborsTreeKey] = treePath

            if node.memory[self.numReceived] == node.memory[self.numNeighboursKey] - 1:
                header = 'Max Temperature'
                destination = node.memory[self.pathKey]

                node.send(Message(destination=destination,
                                  header=header))

                status = 'AVAILABLE'

        node.status = status


    def available(self, node, message):
        pass

    STATUS = {
        'INITIATOR': initiator,
        'IDLE': idle,
        'AVAILABLE': available,
    }