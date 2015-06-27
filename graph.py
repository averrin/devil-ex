#!/usr/bin/python
# -*- coding: utf8 -*-

import sys
import os
from jinja2 import Environment
from jinja2.parser import Parser
import graphviz as gv
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout,
    QComboBox, QLabel
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
if sys.argv[1]:
    filename = os.path.split(sys.argv[1])
    filename = list(filter(lambda x: x.endswith(filename), matches))[0]
    combo.setCurrentText(filename)
    # combo.setCurrentIndex(matches.index(sys.argv[1]))


def createGraph():
    g = gv.Digraph(format='png')
    parser = Parser(env, open(combo.currentText(), 'r', encoding='utf8').read())
    nodes = parser.subparse()

    blocks = {}
    ghosted = {}

    def processNode(n):
        if type(n).__name__ == 'Call':
            if n.node.name == 'show':
                return 'links', n.args
            elif n.node.name == 'disable':
                return 'disables', n.args
            elif n.node.name == 'link':
                return 'calls', n.args
            elif n.node.name == 'set':
                return 'label', n.args
            elif n.node.name == 'checkpoint':
                return 'label', n.args


    for node in nodes:
        name = type(node).__name__
        if name == 'Block':
            subnodes = []
            conditional = []
            blocks[node.name] = {'links': [], 'disables': [], 'label': [], 'calls': [], 'conditional': []}
            for b in node.body:
                if hasattr(b, 'nodes'):
                    subnodes.extend(b.nodes)
                elif type(b).__name__ == 'If':
                    test = b.test
                    if type(test).__name__ == 'Compare':
                        conditional.append([b.body[0].nodes, test.expr.attr, '%s %s %s' % (test.expr.attr, test.ops[0].op, test.ops[0].expr.value)])
                    elif type(test).__name__ == 'Getattr':
                        conditional.append([b.body[0].nodes, test.attr, '%s == True' % test.attr])
                    elif type(test).__name__ == 'Test':
                        conditional.append([b.body[0].nodes, test.node.attr, '%s is %s' % (test.node.attr, test.name)])

            for n in subnodes:
                ret = processNode(n)
                if ret is not None:
                    key, value = ret
                    blocks[node.name][key].append(value)

            for subnode in conditional:
                for n in subnode[0]:
                    ret = processNode(n)
                    if ret is not None:
                        key, value = ret
                        if key == 'links':
                            blocks[node.name]['conditional'].append([value, subnode[1], subnode[2]])
                            ghosted[subnode[1]] = value[0].value
                        else:
                            blocks[node.name][key].append(value)

    for block in blocks.keys():
        color = None
        if blocks[block]['calls']:
            color = 'orange'
            labeltext = ', '.join(['%s -> %s' % (a[1].value, a[0].value) for a in blocks[block]['calls']])
            g.node(block, fillcolor=color, style='filled', xlabel=labeltext, fontcolor='#444488')
        elif block == 'main':
            labeltext = ''
            if blocks[block]['label']:
                labeltext = 'Checkpoint: ' + blocks[block]['label'][0][0].value
            g.node(block, fillcolor='#aaaaff', style='filled', shape='hexagon', fontcolor='black', xlabel=labeltext)
        else:
            labeltext = []
            if blocks[block]['label']:
                for s in blocks[block]['label']:
                    args = [a.value for a in s]
                    labeltext.append(args[0] + '.' + args[1] + '=' + str(args[2]))
                    if args[1] in ghosted.keys():
                        g.edge(block, ghosted[args[1]], color="blue", arrowhead="none", style='dashed', fontcolor="blue", label=args[1])

                labeltext = ', '.join(labeltext)
            if not labeltext:
                labeltext = ''
            if block in ghosted.values():
                g.node(block, style='filled', xlabel=labeltext, fillcolor="lightblue")
            else:
                g.node(block, style='filled', xlabel=labeltext)
    for block, edges in blocks.items():
        for l in edges['links']:
            g.edge(block, l[0].value, label=l[1].value, arrowhead='open')
        for l in edges['disables']:
            g.edge(block, l[0].value, label='', color="red", fontcolor="red", style='dashed')
        for l in edges['conditional']:
            g.edge(block, l[0][0].value, color="blue", fontcolor="blue", label=l[2])

    g.render(filename='result')
    pixmap = QPixmap('result.png')
    label.setPixmap(pixmap)

def tryRender():
    try:
        createGraph()
    except Exception as e:
        g = gv.Digraph(format='png')
        g.node('Error: %s' % e, style='filled', fillcolor='red', shape="rect")
        g.render(filename='result')
        pixmap = QPixmap('result.png')
        label.setPixmap(pixmap)
        raise e


win.resize(800, 600)
widget = QWidget()
widget.setLayout(QVBoxLayout())
widget.layout().addWidget(combo)
widget.layout().addWidget(label)
win.setCentralWidget(widget)
createGraph()
timer = QTimer()
timer.timeout.connect(tryRender)
timer.start(1000)
win.show()
sys.exit(app.exec_())
