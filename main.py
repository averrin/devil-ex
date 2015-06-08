#!/usr/bin/python
# -*- coding: utf8 -*-

import sys
import os
import time
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebKitWidgets import *

import json
from attrdict import AttrDict

from locations import Locations

from jinja2 import Environment, FileSystemLoader
CWD = os.path.abspath(os.path.split(sys.argv[0])[0])
env = Environment(loader=FileSystemLoader([
    os.path.join(CWD, 'templates'),
    os.path.join(CWD, 'locations')
]))


app = QApplication(sys.argv)

_world = json.load(open(os.path.join(CWD, 'world.json'), 'r'))
world = AttrDict(_world)
print(dir(world))

routing = {
    'menu.exit': exit
}


class route(object):
    def __init__(self, path):
        self.path = path

    def __call__(self, f):
        if self.path not in routing:
            routing[self.path] = f

        def wrapped_f(*args):
            f(*args)
        return wrapped_f


class BasicLocation(object):
    route = route

    def __init__(self, app, world):
        self.app = app
        self.view = app.view
        self.world = world
        self.name = self.__class__.name
        self.state = AttrDict({})
        if 'locations' not in self.world:
            self.world.locations = AttrDict({})
        self.world.locations[self.name] = self.state

    def loadPage(self, path, args={}):
        path = self.name + os.sep + path
        args['world'] = world
        self.app.loadPage(path, args)

    def show(self, id):
        self.js('$("#%s").show()' % id)

    def hide(self, id):
        self.js('$("#%s").hide()' % id)

    def js(self, script):
        self.view.page().mainFrame().evaluateJavaScript(script)


class Window(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.resize(800, 600)

        self.tabs = QTabWidget()
        self.view = QWebView()
        self.view.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.view.page().linkClicked.connect(self.click)

        self.editor = QTextEdit()
        self.editor.setText(str(_world))

        self.tabs.addTab(self.view, 'Main')
        self.tabs.addTab(self.editor, 'Editor')

        self.setCentralWidget(self.tabs)
        self.loadWorld()

    def loadWorld(self):
        self.locations = Locations(self, world, BasicLocation)
        if not len(world.items()):
            self.loadPage('menu.html')

    def loadPage(self, path, args={}):
        template = env.get_template(path)

        def link(action, text):
            return '<a href="%s">%s</a>' % (action, text)

        args['link'] = link

        self.view.setHtml(template.render(args))

    def click(self, url):
        cmd = url.toString()
        if cmd in routing:
            objName = cmd.split('.')[0]
            if objName in ('main', 'menu'):
                obj = self
            else:
                obj = self.locations[objName]
            routing[cmd](obj)

    @route('menu.play')
    def play(self):
        self.locations.load('first')

win = Window()
win.show()

if __name__ == "__main__":
    app.exec_()
