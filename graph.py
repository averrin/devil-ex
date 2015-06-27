#!/usr/bin/python
# -*- coding: utf8 -*-

import sys
import os
from jinja2 import Environment, FileSystemLoader
from jinja2.parser import Parser
import graphviz as gv
from PyQt5.QtGui import *
from PyQt5.QtCore import QTimer, QObject, pyqtSlot
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout,
    QHBoxLayout, QComboBox, QLabel
)
import fnmatch

CWD = os.path.abspath(os.path.split(sys.argv[0])[0])
env = Environment()
app = QApplication(sys.argv)
win = QMainWindow()
label = QLabel()

matches = []
for root, dirnames, filenames in os.walk('locations'):
  for filename in fnmatch.filter(filenames, '*.html'):
    matches.append(os.path.join(root, filename))
combo = QComboBox()
combo.addItems(matches)


def createGraph():
    g = gv.Digraph(format='png')
    parser = Parser(env, open(combo.currentText(), 'r', encoding='utf8').read())
    nodes = parser.subparse()

    blocks = {}
    important = []

    for node in nodes:
        name = type(node).__name__
        if name == 'Block':
            blocks[node.name] = {'links': [], 'disables': [], 'label': [], 'calls': []}
            subnodes = []
            for b in node.body:
                if hasattr(b, 'nodes'):
                    subnodes.extend(b.nodes)
            for n in subnodes:
                if type(n).__name__ == 'Call':
                    if n.node.name == 'show':
                        blocks[node.name]['links'].append(n.args)
                    elif n.node.name == 'disable':
                        blocks[node.name]['disables'].append(n.args)
                    elif n.node.name == 'link':
                        blocks[node.name]['calls'].append(n.args)
                        important.append(node.name)
                    elif n.node.name == 'set':
                        blocks[node.name]['label'].append(n.args)

    for block in blocks.keys():
        color = None
        if block in important:
            color = 'orange'
            labeltext = ', '.join(['%s -> %s' % (a[1].value, a[0].value) for a in blocks[block]['calls']])
            g.node(block, fillcolor=color, style='filled', xlabel=labeltext, fontcolor='#444488')
        elif block == 'main':
            g.node(block, fillcolor='#444488', style='filled', shape='hexagon', fontcolor='white')
        else:
            labeltext = []
            if blocks[block]['label']:
                for s in blocks[block]['label']:
                    args = [a.value for a in s]
                    labeltext.append(args[0] + '.' + args[1] + '=' + str(args[2]))
                labeltext = ', '.join(labeltext)
            if not labeltext:
                labeltext = ''
            g.node(block, style='filled', xlabel=labeltext)
    for block, edges in blocks.items():
        for l in edges['links']:
            g.edge(block, l[0].value, label=l[1].value, arrowhead='open')
        for l in edges['disables']:
            g.edge(block, l[0].value, label='', color="red", fontcolor="red", style='dashed')

    g.render(filename='result')
    pixmap = QPixmap('result.png')
    label.setPixmap(pixmap)

win.resize(800, 600)
widget = QWidget()
widget.setLayout(QVBoxLayout())
widget.layout().addWidget(combo)
widget.layout().addWidget(label)
win.setCentralWidget(widget)
createGraph()
timer = QTimer()
timer.timeout.connect(createGraph)
timer.start(1000)
win.show()
sys.exit(app.exec_())
