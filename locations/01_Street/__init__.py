def init(basic):
    class Location(basic):
        def load(self):
            self.state.visits = 1 if not 'visits' in self.state else (self.state.visits + 1)
            self.loadPage('templates/main.html')



    return Location
