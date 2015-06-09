def init(basic):
    class Location(basic):
        def load(self):
            self.state.visits = 1 if not 'visits' in self.state else (self.state.visits + 1)
            self.loadPage('templates/first.html')
            # self.js('$("body").html("mya")')

        @basic.route('first.exit')
        def exit(self):
            self.goTo('01_Street')




    return Location
