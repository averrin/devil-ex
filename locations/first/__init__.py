def init(basic):
    class Location(basic):
        name = 'first'

        def load(self):
            self.loadPage('templates/first.html')

        @basic.route('first.bzz')
        def bzz(self):
            self.loadPage('templates/second.html')




    return Location
