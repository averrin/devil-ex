def init(basic):
    class Location(basic):
        def load(self):
            self.loadPage('templates/first.html')

        @basic.route('first.exit')
        def exit(self):
            self.goTo('01_Street')




    return Location
