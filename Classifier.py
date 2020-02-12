import random

class Classifier:

    def __init__(self):
        pass

    def classify(self, image):
        return image if random.random() < 0.5 else 8
