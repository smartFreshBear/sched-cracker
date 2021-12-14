class Cell:
    def __init__(self, color=None, text: str = ''):
        if color is None:
            color = {}
        self.color = color
        self.text = text

    def __str__(self):
        return "colors are : {} text is {}".format(self.color, self.text)
