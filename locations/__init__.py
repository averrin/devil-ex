import importlib
import requests
import os


class Locations(dict):
    def __init__(self, app, url, world, basicLocation):
        self.app = app
        self.world = world
        self.basicLocation = basicLocation
        self.url = url
        dict.__init__(self)

    def load(self, locationName):
        if self.app.local:
            location = importlib.import_module('.' + locationName, 'locations')
        else:
            url = self.url + 'locations/' + locationName + '/__init__.py'
            print(url)
            code = requests.get(url).text
            locationPath = os.path.join(self.app.cwd, 'locations', locationName)
            if not os.path.isdir(locationPath):
                os.mkdir(locationPath)
            with open(os.path.join(locationPath, '__init__.py'), 'w') as f:
                f.write(code)
            location = importlib.import_module('.' + locationName, 'locations')
        location = location.init(self.basicLocation)(
            locationName, self.app, self.world
        )
        self.world.currentLocation = locationName
        self.app.currentLocation = location
        location.load()
        self[locationName] = location
        return location
