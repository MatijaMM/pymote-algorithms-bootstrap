from pymote.sensor import Sensor
from pymote.algorithms.saturationKVM import Saturation
from pymote.message import Message

class Center(Saturation):

    default_params = {'parentKey': 'parent', 'MaxValueKey1': 'MaxValue1', 'MaxValueKey2': 'MaxValue2', 'MaxNeighborKey': 'MaxNeighbor'}

    def processing(self, node, message):
        Saturation.processing(self, node, message)

        if message.header == 'Center':
            self.process_message(node, message)
            self.resolve(node, message)

    def initialize(self, node):
        node.memory[self.MaxValueKey1]  = 0
        node.memory[self.MaxValueKey2]  = 0

    def prepare_message(self, node, message):
        message.header = 'Message'
        message.data = int(node.memory[self.MaxValueKey1]) + 1
        return message

    def process_message(self, node, message):
        if int(node.memory[self.MaxValueKey1]) < int(message.data):
            node.memory[self.MaxValueKey2] = node.memory[self.MaxValueKey1]
            node.memory[self.MaxValueKey1] = message.data
            node.memory[self.MaxNeighborKey] = message.source
        else:
            if int(node.memory[self.MaxValueKey2]) < int(message.data):
                node.memory[self.MaxValueKey2] = message.data

    def resolve(self, node, message):
        if (int(node.memory[self.MaxValueKey1]) - int(node.memory[self.MaxValueKey2])) == 1:
            if node.memory[self.MaxNeighborKey] != node.memory[self.parentKey]:
                data = int(node.memory[self.MaxValueKey2]) + 1
                node.send(Message(header='Center', data=data, destination=node.memory[self.MaxNeighborKey]))
            node.status = 'CENTER'
        else:
            if (int(node.memory[self.MaxValueKey1]) - int(node.memory[self.MaxValueKey2])) > 1:
                data = int(node.memory[self.MaxValueKey2]) + 1
                node.send(Message(header='Center', data=data, destination=node.memory[self.MaxNeighborKey]))
            else:
                node.status = 'CENTER'

    def center(self, node, message):
        pass

    STATUS = {
        'AVAILABLE': Saturation.STATUS.get('AVAILABLE'),
        'ACTIVE': Saturation.STATUS.get('ACTIVE'),
        'PROCESSING': processing,
        'SATURATED': Saturation.STATUS.get('SATURATED'),
        'CENTER': center
    }