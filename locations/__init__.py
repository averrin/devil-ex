import importlib


class Locations(dict):
    def __init__(self, app, world, basicLocation):
        self.app = app
        self.world = world
        self.basicLocation = basicLocation
        dict.__init__(self)

    def load(self, locationName):
        location = importlib.import_module('.' + locationName, 'locations')
        location = location.init(self.basicLocation)(
            locationName, self.app, self.world
        )
        self.world.currentLocation = locationName
        self.app.currentLocation = location
        location.load()
        self[locationName] = location
        return location
