import random


class Classifier:
    def classify(self, image):
        return image if random.random() < 0.5 else 8
