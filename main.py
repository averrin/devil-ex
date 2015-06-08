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
        self.__app = app
        self.view = app.view
        self.world = world
        self.name = self.__class__.name
        self.state = AttrDict({'visited': True})
        if 'locations' not in self.world:
            self.world.locations = AttrDict({})
        self.world.locations += {self.name: self.state}
        print(self.world.locations, self.state)

    def loadPage(self, path, args={}):
        path = self.name + '/' + path
        args['world'] = self.world
        self.__app.loadPage(path, args)

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
        self.setWindowTitle('Diaboli Ex')

        world = json.load(open(os.path.join(CWD, 'world.json'), 'r'))
        self.world = AttrDict(world)

        self.tabs = QTabWidget()
        self.view = QWebView()
        self.view.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.view.page().linkClicked.connect(self.click)

        self.editor = QTextEdit()
        self.updateEditor()
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateEditor)
        self.timer.start(1000)
        editPanel = QWidget()
        editPanel.setLayout(QVBoxLayout())
        editPanel.layout().addWidget(self.editor)
        buttonPanel = QWidget()
        buttonPanel.setLayout(QHBoxLayout())
        self.applyButton = QPushButton('Apply')
        self.applyButton.clicked.connect(self.applyWorld)
        self.reloadButton = QPushButton('Apply && Reload')
        self.reloadButton.clicked.connect(self.reloadWorld)
        buttonPanel.layout().addWidget(self.applyButton)
        buttonPanel.layout().addWidget(self.reloadButton)
        editPanel.layout().addWidget(buttonPanel)

        self.tabs.addTab(self.view, 'Main')
        self.tabs.addTab(editPanel, 'Editor')

        self.setCentralWidget(self.tabs)
        self.loadWorld()

    def updateEditor(self):
        text = json.dumps(self.world, indent=4)
        if text != self.editor.toPlainText() and not self.editor.hasFocus():
            self.editor.setText(text)

    def applyWorld(self):
        try:
            world = json.loads(self.editor.toPlainText())
            with open(os.path.join(CWD, 'world.json'), 'w') as f:
                f.write(self.editor.toPlainText())
        except:
            return
        self.world = AttrDict(world)

    def reloadWorld(self):
        self.applyWorld()
        self.loadWorld()

    def loadWorld(self):
        self.locations = Locations(self, self.world, BasicLocation)
        print(self.world)
        if 'currentLocation' not in self.world:
            self.loadPage('menu.html')
        else:
            self.locations.load(self.world.currentLocation)

    def loadPage(self, path, args={}):
        template = env.get_template(path)

        def link(action, text):
            return '<a href="%s">%s</a>' % (action, text)
        def show(id, text):
            return '<a href="#" onclick="$(\'#%s\').show()">%s</a>' % (id, text)

        args['link'] = link
        args['show'] = show
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
