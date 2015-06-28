#!/usr/bin/python
# -*- coding: utf8 -*-

import sys
import os
from PyQt5.QtCore import QTimer, QObject, pyqtSlot, Qt
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QTabWidget, QTextEdit, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton
)
from PyQt5.QtWebKit import QWebSettings
from PyQt5.QtWebKitWidgets import QWebView, QWebPage
import json
from attrdict import AttrDict
from jinja2 import Environment, FileSystemLoader, BaseLoader, TemplateNotFound
import requests
import semver
from datetime import datetime, timedelta

from locations import Locations

VERSION = semver.format_version(0, 2, 0, 'alpha')

CWD = os.path.abspath(os.path.split(sys.argv[0])[0])
app = QApplication(sys.argv)

if 'DEBUG' in os.environ:
    DEBUG = os.environ['DEBUG'].lower() in ('true', 'yes', '1')
else:
    DEBUG = False
DEBUG = True


class TemplateLoader(BaseLoader):
    def __init__(self, base_url):
        self.base_url = base_url
        self.cache = {}

    def get_source(self, environment, template):
        url = self.base_url + template
        url = url.replace('\\', '/')
        r = requests.get(url)
        print(url)
        if r.status_code != 200:
            raise TemplateNotFound(template)
        # print(r.text.encode('utf8'))
        content = r.text
        self.cache[url] = datetime.now()
        return content, url, lambda: (datetime.now() - self.cache[url]).seconds > 60*60

env = Environment(loader=TemplateLoader('http://diaboli.averr.in/'))


class BasicLocation(QObject, object):
    method = pyqtSlot

    def __init__(self, name, app, world):
        self.__app = app
        self.view = app.view
        self.world = world
        self.name = name
        QObject.__init__(self, objectName=name)
        if self.name not in self.world.locations:
            self.world.locations += {self.name: {'visited': True}}

    def set(self, key, value):
        self.world.locations[self.name][key] = value

    def load(self):
        pass

    def loadPage(self, path, args=None):
        if args is None:
            args = {}
        path = os.path.join('locations', self.name, path)
        self.__app.loadPage(path)

    def js(self, script):
        self.view.page().mainFrame().evaluateJavaScript(script)

    @pyqtSlot(str)
    def goTo(self, location):
        self.__app.goTo(location)
        self.world.checkpoint = ''
        self.__app.saveWorld()

    def __getattr__(self, key):
        if key in self.__dict__:
            return self.__getattribute__(key)
        else:
            if key not in self.world.locations[self.name]:
                self.world.locations[self.name][key] = None
            return self.world.locations[self.name][key]

    @pyqtSlot(str, str)
    def notify(self, title, text):
        script = u'new PNotify({title: "%s", text: "%s", delay: 800})' % (
            title, text
        )
        self.js(script)

    @pyqtSlot(str)
    def achieve(self, aid):
        achievement = self.__app.achievements[aid]
        if aid not in self.world['achievements']:
            self.world['achievements'].append(aid)
            self.notify(achievement['name'], achievement['description'])

    @pyqtSlot(str)
    def checkpoint(self, label):
        self.world['checkpoint'] = label
        self.__app.saveWorld()
        self.notify(u'Контрольная точка', u'Игра сохранена.')


class Window(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.resize(800, 600)
        self.setWindowTitle('Diaboli Ex')

        home = os.path.expanduser('~')
        self.worldPath = os.path.join(home, '.diaboli-ex.json')

        if os.path.isfile(self.worldPath):
            world = json.load(open(self.worldPath, 'r'))
            if 'version' not in world:
                world['version'] = '0.0.0'
            if semver.compare(VERSION, world['version']) > 0:
                v1 = world['version'].split('.')
                v0 = VERSION.split('.')
                if v0[0] != v1[0] or v0[1] != v1[1]:
                    self.initNewWorld()
                    world = json.load(open(self.worldPath, 'r'))
        else:
            self.initNewWorld()
            world = json.load(open(self.worldPath, 'r'))

        world['launches'] += 1
        world['version'] = VERSION
        self.world = AttrDict(world)
        self.saveWorld()
        self.achievements = json.load(open(os.path.join(CWD, 'data', 'achievements.json'), 'r', encoding='utf8'))

        self.tabs = QTabWidget()
        self.view = QWebView(self)
        # self.view.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        # self.view.page().linkClicked.connect(self.click)

        self.view.page().mainFrame().javaScriptWindowObjectCleared.connect(self.injectObjects)

        self.editor = QTextEdit()

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

        if DEBUG:
            self.updateEditor()
            self.timer = QTimer()
            self.timer.timeout.connect(self.updateEditor)
            self.timer.start(1000)

            self.tabs.addTab(self.view, 'Game')
            self.tabs.addTab(editPanel, 'Editor')

            self.view.page().settings().setAttribute(
                QWebSettings.DeveloperExtrasEnabled,
                True
            )
            self.setCentralWidget(self.tabs)
        else:
            self.setCentralWidget(self.view)

        def link(action, *args):
            if args:
                text = args[-1]
            else:
                text = ''
            if action.split('.')[0] == 'main':
                script = 'app'
                action = action.split('.')[1]
            else:
                script = 'currentLocation'
            script += '.%s(%s)' % (action, ','.join(["'%s'" % a for a in args[:-1]]))
            if args:
                args = '/' + '/'.join(args[:-1])
            else:
                args = ''
            script = ('$("a[href=\'%s%s\']").on("click", function(e)' % (action, args)) + \
                '{e.preventDefault();%s;' % (script) + \
                '$("a[href=\'" + e.target + "\']").addClass("visited");return false;})'
            return '<a href=\'%s%s\'>%s</a><script>$(document).ready(function(){%s});</script>' % (
                action, args, text, script
            )

        def action(action, *args):
            a = link(action, *args)
            script = 'currentLocation.%s(%s);' % (action, ",".join(["'%s'" % a for a in args]))
            script = '<script>$(document).ready(function(){%s});</script>' % script
            return script

        def achieve(aid):
            return action('achieve', aid)

        def checkpoint(label):
            return action('checkpoint', label)

        def show(block, text):
            return link('main.showBlock', block, text)

        def disable(*names):
            script = ''
            for name in names:
                if '.' not in name:
                    self.displayedBlocks.append(name)
                    name = 'showBlock/%s' % name
                script += '$("a[href=\'%s\']")' % name
                script += '.addClass("disabled").attr("href", "#");'
            script = '<script>%s</script>' % script
            return script

        def set(section, key, value):
            if section == 'player':
                self.world[section][key] = value
            elif section == 'location':
                self.world.locations[self.world.currentLocation][key] = value
            return '<!--//-->'

        self.context = {
            'world': self.world,
            'link': link,
            'show': show,
            'disable': disable,
            'set': set,
            'action': action,
            'achieve': achieve,
            'checkpoint': checkpoint
        }
        self.loadWorld()

    def initNewWorld(self):
        with open(self.worldPath, 'w') as wf:
            json.dump({
                "player": {},
                'locations': {},
                'achievements': [],
                'persons': {},
                'launches': 0,
                'checkpoint': '',
                'version': VERSION
            }, wf)

    def updateEditor(self):
        text = json.dumps(self.world, indent=4)
        if text != self.editor.toPlainText() and not self.editor.hasFocus():
            self.editor.setText(text)

    def saveWorld(self):
        json.dump(
            self.world, open(self.worldPath, 'w'),
            indent=4
        )

    def applyWorld(self):
        try:
            world = json.loads(self.editor.toPlainText())
            with open(self.worldPath, 'w') as f:
                f.write(self.editor.toPlainText())
        except Exception as e:
            print(e)
            return
        self.world = AttrDict(world)

    def reloadWorld(self):
        self.applyWorld()
        self.loadWorld()

    def loadWorld(self):
        self.locations = Locations(self, self.world, BasicLocation)
        if 'currentLocation' not in self.world:
            self.loadPage('data/menu.html')
        else:
            self.goTo(self.world.currentLocation)

    def goTo(self, location):
        self.locations.load(location)

    def loadPage(self, path, context=None):
        self.displayedBlocks = []
        if 'currentLocation' in self.world:
            if self.world.currentLocation in self.world.locations:
                self.context['location'] = self.world.locations[
                    self.world.currentLocation
                ]
            else:
                self.context['location'] = {}
        self.context['player'] = self.world.player
        self.template = env.get_template(path)
        if context is None:
            context = {}
        context.update(self.context)
        self.injectObjects()
        content = self.template.render(context)
        # print(content)
        self.view.setContent(content, "text/html; charset=utf-8")

    def injectObjects(self):
        self.view.page().mainFrame().addToJavaScriptWindowObject('app', self)
        if hasattr(self, 'currentLocation'):
            self.view.page().mainFrame().addToJavaScriptWindowObject('currentLocation', self.currentLocation)
        self.view.page().mainFrame().evaluateJavaScript('console.log(app)')

    @pyqtSlot()
    def play(self):
        self.locations.load('first')

    @pyqtSlot()
    def finish(self):
        if self.world.launches == 1:
            self.world['achievements'].append('one_launch')
        context = {
            "done": [],
            "last": []
        }
        for aid, a in self.achievements.items():
            if aid in self.world.achievements:
                context['done'].append(a)
            else:
                context['last'].append(a)
        self.loadPage('finish.html', context=context)

    @pyqtSlot()
    def exit(self):
        sys.exit()

    @pyqtSlot(str)
    def showBlock(self, block):
        self.context['player'] = self.world.player
        if block in self.displayedBlocks:
            return
        else:
            self.displayedBlocks.append(block)
        html = ''.join(
            self.template.blocks[block](
                self.template.new_context(self.context)
            )
        ).replace('"', '\\"').replace("'", "\\'").replace('\n', '')
        script = '$("#visible").append("%s");' % html.strip()
        self.view.page().mainFrame().evaluateJavaScript(script)
        script = '$("a[href=\'main.show/%s\']").addClass("visited");' % block
        # self.view.setContent('<script>%s</script>' % script, "text/html; charset=utf-8")
        self.view.page().mainFrame().evaluateJavaScript(script)
        self.view.page().mainFrame().setScrollBarValue(Qt.Vertical, self.view.page().mainFrame().scrollBarMaximum(Qt.Vertical));


if __name__ == "__main__":
    win = Window()
    win.show()
    app.exec_()
