def init(basic):
    class Location(basic):
        name = 'first'

        def load(self):
            self.state.visits = 1
            self.loadPage('templates/first.html')
            # self.js('$("body").html("mya")')

        @basic.route('first.bzz')
        def bzz(self):
            self.loadPage('templates/second.html')




    return Location
