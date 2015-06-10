def init(basic):
    class Location(basic):
        def load(self):
            if self.visits is None:
                self.set('visits', 1)
            else:
                self.set('visits', self.visits + 1)
            self.loadPage('templates/main.html')



    return Location
