from pymote.algorithms.saturationKVM import Saturation
from pymote.sensor import Sensor
from pymote.message import Message
import random

class TemperatureSensor(Sensor):

    def read(self,node):
        return {'Temperature': random.randrange(-100,100,1)}

class MinFind(Saturation):

    default_params = {'temperatureKey':'Temperature','minKey':'Min'}

    def processing(self, node, message):
        Saturation.processing(self, node, message)
            
        if message.header == "Resolution":
            self.process_message(node, message)
            destination_nodes = list(node.memory[self.neighborsKey])
            destination_nodes.remove(node.memory[self.parentKey])
            node.send(Message(header='Resolution', data=node.memory[self.minKey], destination=destination_nodes))        

            if node.memory[self.temperatureKey] == message.data:
                node.status = 'MINIMUM'
            else :
                node.status = 'LARGE'

    
    def initialize(self, node):
        node.compositeSensor = (TemperatureSensor,'Temperature')
        node.memory[self.temperatureKey] = node.compositeSensor.read()['Temperature']
        node.memory[self.minKey] = node.memory[self.temperatureKey]       
    
    def prepare_message(self, node, message):
        message.header = 'Message'
        message.data = node.memory[self.minKey]
        return message
                   
    def process_message(self, node, message): 
        if message.data < node.memory[self.minKey]:
            node.memory[self.minKey] = message.data
    
    def resolve(self, node, message):
        destination_nodes = list(node.memory[self.neighborsKey])
        destination_nodes.remove(node.memory[self.parentKey])
        self.process_message(node, message)
        node.send(Message(header='Resolution', data=node.memory[self.minKey], destination=destination_nodes))        

        if node.memory[self.temperatureKey] == node.memory[self.minKey]:
            node.status = 'MINIMUM'
        else :
            node.status = 'LARGE'
                                                     
    def minimum(self, node, message):
        pass

    def large(self, node, message):
        pass
    
    STATUS = {
      'MINIMUM' : minimum,
      'LARGE' : large,
      'AVAILABLE': Saturation.STATUS.get('AVAILABLE'),
      'ACTIVE': Saturation.STATUS.get('ACTIVE'),
      'PROCESSING': processing, 
      'SATURATED': Saturation.STATUS.get('SATURATED')
      }