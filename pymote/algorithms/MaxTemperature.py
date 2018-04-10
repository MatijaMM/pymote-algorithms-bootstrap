from pymote.algorithm import NodeAlgorithm
from pymote.message import Message


class MaxTemperature(NodeAlgorithm):
    required_params = ('informationKey',)
    default_params = {'neighborsKey': 'Neighbors', 'numNeighboursKey': 'numNeighbours', 'temperatureKey': 'Temperature',
                      'pathKey': 'path', 'maxTempKey': 'maxTemp', 'numReceived': 'numReceived',
                      'isReceivedKey': 'isReceived'}

    def initializer(self):
        ini_nodes = []
        for node in self.network.nodes():
            node.memory[self.neighborsKey] = \
                node.compositeSensor.read()['Neighbors']
            node.memory[self.temperatureKey] = \
                node.compositeSensor.read()['Temperature']
            node.status = 'IDLE'
            node.memory[self.numReceived] = 0
            node.memory[self.isReceivedKey] = False
            node.memory[self.numNeighboursKey] = len(node.memory[self.neighborsKey])
            if self.informationKey in node.memory:
                node.status = 'INITIATOR'
                node.memory[self.maxTempKey] = node.memory[self.temperatureKey]

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
            if float(message.data) > float(node.memory[self.maxTempKey]):
                node.memory[self.maxTempKey] = float(message.data)

            if node.memory[self.numReceived] == node.memory[self.numNeighboursKey]:
                node.status = 'DONE'

    def idle(self, node, message):
        header = 'Information'
        status = 'IDLE'
        node.memory[self.maxTempKey] = node.memory[self.temperatureKey]

        if message.header == 'Information' and not (node.memory[self.isReceivedKey]):

            node.memory[self.isReceivedKey] = True

            maxTemp = float(node.memory[self.temperatureKey])
            destination_nodes = list(node.memory[self.neighborsKey])
            node.memory[self.pathKey] = message.source
            destination_nodes.remove(message.source)

            if destination_nodes:
                for destination_node in destination_nodes:
                    if destination_node.status == 'INITIATOR':
                        destination_nodes.remove(destination_node)

            else:
                header = 'Max Temperature'
                destination_nodes = message.source
                status = 'DONE'

            node.send(Message(destination=destination_nodes,
                              header=header,
                              data=maxTemp))

        else:
            if (message.header == 'Max Temperature'):
                if node.memory[self.maxTempKey] < message.data:
                    node.memory[self.maxTempKey] = message.data

            node.memory[self.numReceived] += 1

            if node.memory[self.numReceived] == node.memory[self.numNeighboursKey] - 1:
                header = 'Max Temperature'
                data = node.memory[self.maxTempKey]
                destination = node.memory[self.pathKey]

                node.send(Message(destination=destination,
                                  header=header,
                                  data=data))

                status = 'DONE'

        node.status = status


    def done(self, node, message):
        pass

    STATUS = {
        'INITIATOR': initiator,
        'IDLE': idle,
        'DONE': done,
    }