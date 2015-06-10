#!/usr/bin/python
# -*- coding: utf8 -*-

import sys
import os
import time
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebKit import *
from PyQt5.QtWebKitWidgets import *

import json
from attrdict import AttrDict

from locations import Locations

from jinja2 import Environment, FileSystemLoader, meta
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

    def __init__(self, name, app, world):
        self.__app = app
        self.view = app.view
        self.world = world
        self.name = name
        self.state = AttrDict({'visited': True})
        if 'locations' not in self.world:
            self.world.locations = AttrDict({})
        self.world.locations += {self.name: self.state}

    def load(self):
        pass

    def loadPage(self, path, args={}):
        path = self.name + '/' + path
        self.__app.loadPage(path)

    def show(self, id):
        self.js('$("#%s").show()' % id)

    def hide(self, id):
        self.js('$("#%s").hide()' % id)

    def js(self, script):
        self.view.page().mainFrame().evaluateJavaScript(script)

    def goTo(self, location):
        self.__app.locations.load(location)
        self.__app.saveWorld()


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
        self.view.page().settings().setAttribute(QWebSettings.DeveloperExtrasEnabled, True)

        self.editor = QTextEdit()
        self.updateEditor()
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateEditor)
        self.timer.start(1000)

        # self.saveTimer = QTimer()
        # self.saveTimer.timeout.connect(self.saveWorld)
        # self.saveTimer.start(5000)

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

        def link(action, *args):
            text = args[-1]
            args = '/'.join(args[:-1])
            return '<a href="%s/%s" onclick="$(this).addClass(\'visited\')">%s</a>' % (action, args, text)

        def show(id, text):
            return '<a href="main.show/%s" onclick="$(this).addClass(\'visited\')">%s</a>' % (id, text)

        self.context = {
            'world': self.world,
            'link': link,
            'show': show
        }
        self.loadWorld()

    def updateEditor(self):
        text = json.dumps(self.world, indent=4)
        if text != self.editor.toPlainText() and not self.editor.hasFocus():
            self.editor.setText(text)

    def saveWorld(self):
        json.dump(self.world, open(os.path.join(CWD, 'world.json'), 'w'), indent=4)

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
        if 'currentLocation' not in self.world:
            self.loadPage('menu.html')
        else:
            self.locations.load(self.world.currentLocation)

    def loadPage(self, path):
        self.template = env.get_template(path)
        self.view.setHtml(self.template.render(self.context))

    def click(self, url):
        url = url.toString().split('/')
        cmd = url[0]
        args = url[1:]
        if cmd in routing:
            objName = cmd.split('.')[0]
            if objName in ('main', 'menu'):
                obj = self
            else:
                obj = self.locations[objName]
            if args[0]:
                routing[cmd](obj, *args)
            else:
                routing[cmd](obj)

    @route('menu.play')
    def play(self):
        self.locations.load('first')

    @route('main.show')
    def showBlock(self, block):
        html = ''.join(self.template.blocks[block](self.template.new_context(self.context)))
        script = '$("#visible").append("%s")' % html.strip().replace('"', '\\"').replace("'", "\\'").replace('\n', '')
        print(script)
        self.view.page().mainFrame().evaluateJavaScript(script)

win = Window()
win.show()

if __name__ == "__main__":
    app.exec_()
