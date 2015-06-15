def init(basic):
    class Location(basic):
        def load(self):
            self.loadPage('templates/first.html')

        @basic.method()
        def start(self):
            self.goTo('01_Street')

    return Location
