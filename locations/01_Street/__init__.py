def init(basic):
    class Location(basic):
        def load(self):
            if self.visits is None:
                self.set('visits', 1)
            else:
                self.set('visits', self.visits + 1)
            if not self.world.checkpoint:
                self.loadPage('templates/car.html')
            elif self.world.checkpoint:
                self.loadPage('templates/%s.html' % self.world.checkpoint)

        @basic.method()
        def toStreet(self):
            self.loadPage('templates/street_1.html')

    return Location
