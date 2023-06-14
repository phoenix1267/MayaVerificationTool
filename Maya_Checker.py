from maya import cmds 
import maya.api.OpenMaya as om 
from PySide2 import QtWidgets as qw
from pymel.core import *
from pymel.core.datatypes import *

class MayaChecker(qw.QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Verification Tool")
        self.setMinimumWidth(500)
        self.draw_ui()
        self.bind_ui()   

    def draw_ui(self):
        self.layout = qw.QGridLayout(self)
        self.btnVerifyUV = qw.QPushButton("Verify UV")
        self.btnVerifyUV.setFixedWidth(400)
        self.btn_ClearLog = qw.QPushButton("Clear Log")
        self.btnVerifyScale = qw.QPushButton("Verify Scale")
        self.btnVerifyPivot = qw.QPushButton("Verify Pivot")
        self.btnVerifyVertextOverlap = qw.QPushButton("Verify Vertex overlaping")
        self.btnVerifyAll = qw.QPushButton("Verify All")
        self.autoClear = qw.QCheckBox("Auto Clear")
        self.canSetScale = qw.QCheckBox("Replace Scale")
        self.canFlipFaces = qw.QCheckBox("Flip Faces")
        self.canRepositionPivot = qw.QCheckBox("Set Pivot To 0,0,0")
        self.canMoveObjectWithPivot = qw.QCheckBox("Move object with pivot")
        self.canDeleteOverlapingPivot = qw.QCheckBox("Remove overlaping vertexes")
        self.canSkipCheck = qw.QCheckBox("Skip Checking overlap")
        self.log = qw.QPlainTextEdit()
        self.log.setReadOnly(True)

        self.addAllWidget()

    def addAllWidget(self):
        self.layout.addWidget(self.btnVerifyUV,0,0)
        self.layout.addWidget(self.btnVerifyScale,1,0)
        self.layout.addWidget(self.btnVerifyPivot,2,0)
        self.layout.addWidget(self.btnVerifyVertextOverlap,3,0)
        self.layout.addWidget(self.btnVerifyAll,4,0,1,4)
        self.layout.addWidget(self.log,5,0,1,4)
        self.layout.addWidget(self.autoClear,6,0)
        self.layout.addWidget(self.canSetScale,1,1)
        self.layout.addWidget(self.canFlipFaces,0,1)
        self.layout.addWidget(self.canRepositionPivot,2,1)
        self.layout.addWidget(self.canMoveObjectWithPivot,2,2,1,2)
        self.layout.addWidget(self.canDeleteOverlapingPivot,3,1,1,2)
        self.layout.addWidget(self.canSkipCheck,3,3,1,1)
        self.layout.addWidget(self.btn_ClearLog,7,0,1,4)

    def bind_ui(self):
        self.btnVerifyUV.clicked.connect(self.verify_UV)
        self.btnVerifyScale.clicked.connect(self.verifyScale)
        self.btn_ClearLog.clicked.connect(self.clear_Log)
        self.btnVerifyPivot.clicked.connect(self.verifyPivot)
        self.btnVerifyVertextOverlap.clicked.connect(self.verifyOverlapingVertexs)
        self.btnVerifyAll.clicked.connect(self.verifyAll)

    def clear_Log(self):
        self.log.setPlainText("")

    '''
    verify if UV are all exterior sided, can also flip them if needed, use the flip with caution and at your
    own risk, if you are sure that you want all your faces facing outside
    '''
    def verify_UV(self):
        if self.autoClear.isChecked():
            self.log.setPlainText("")
        else:
            self.log.appendPlainText("*---------------------------*")

        face_template = '{0}.f[{1}]'
        sel = om.MGlobal.getActiveSelectionList()
        if not sel.length():
            return self.log.appendPlainText('Nothing Selected')
        
        for selected in range(sel.length()):
            obj = cmds.ls(sl=True)[selected]
            flips = []
            dag = sel.getDagPath(selected)
            face_iter = om.MItMeshPolygon(dag)
            for i in range(face_iter.count()):
                face_iter.setIndex(i)
                a = (face_iter.getUVs()[0][0],face_iter.getUVs()[1][0])#uvs[0]
                b = (face_iter.getUVs()[0][1],face_iter.getUVs()[1][1])#uvs[1]
                c = (face_iter.getUVs()[0][2],face_iter.getUVs()[1][2])#uvs[2]
                uv_ab = om.MVector(b[0] - a[0], b[1] - a[1])
                uv_bc = om.MVector(c[0] - b[0], c[1] - b[1])
                if (uv_ab ^ uv_bc) * om.MVector(0, 0, 1) <= 0:
                    flips.append(face_template.format(obj, i))
            
            if flips and self.canFlipFaces.isChecked():
                self.log.appendPlainText("{} faces on the wrong side for \"{}\", they have now been fliped !".format(flips.__len__(),obj))
                cmds.polyFlipUV(flips, flipType=0, local=True)
            elif flips and not self.canFlipFaces.isChecked():
                self.log.appendPlainText("{} faces on the wrong side for \"{}\"".format(flips.__len__(),obj))
            else:
                self.log.appendPlainText("Faces ok for \"{}\"".format(obj))

    '''
    verify if the scale of the object is 1,1,1 and fix it if needed
    '''
    def verifyScale(self):
        if self.autoClear.isChecked():
            self.log.setPlainText("")
        else:
            self.log.appendPlainText("*---------------------------*")

        Objs = cmds.ls(sl = True)
        if list(Objs).__len__() <= 0:
            return self.log.appendPlainText('Nothing Selected')
        for o in Objs:
            Sca = cmds.getAttr(o+'.s')[0]
            if Sca != (1,1,1):
                self.log.appendPlainText("Scale is not at (1,1,1) for \"{}\"".format(o))
                if self.canSetScale.isChecked():
                    cmds.setAttr(o+'.s',1,1,1)
            else:
                self.log.appendPlainText("Scale ok for \"{}\"".format(o))

    '''
    verify if the pivot point is in 0,0,0 and can recenter it, can also move the object with the pivot or
    leave it in place
    '''
    def verifyPivot(self):
        if self.autoClear.isChecked():
            self.log.setPlainText("")
        else:
            self.log.appendPlainText("*---------------------------*")

        Objs = cmds.ls(sl = True)
        if list(Objs).__len__() <= 0:
            return self.log.appendPlainText('Nothing Selected')
        for o in Objs:
            pivotPointScale = cmds.getAttr(o+'.scalePivot')[0]
            pivotPointRot = cmds.getAttr(o+'.rotatePivot')[0]
            translate = cmds.getAttr(o+'.translate')[0]
            print(pivotPointScale)
            print(pivotPointRot)
            print(translate)
            if pivotPointScale != (0,0,0) or pivotPointRot != (0,0,0): 
                self.log.appendPlainText("Pivot for \"{}\" is not at (0,0,0)".format(o))
                if self.canRepositionPivot.isChecked():
                    cmds.setAttr(o+'.scalePivot',0,0,0)
                    cmds.setAttr(o+'.rotatePivot',0,0,0)
                    if self.canMoveObjectWithPivot.isChecked():
                        cmds.setAttr(o+'.translate',pivotPointScale[0],pivotPointScale[1],pivotPointScale[2])
            else:
                self.log.appendPlainText("Pivot ok for \"{}\"".format(o))

    '''
    Check if a vertex overlap an other one, may be slow for big object,
    you can remove the checking part if you are sure about what you want to do, it will speedup the process
    '''
    def verifyOverlapingVertexs(self):
        if self.autoClear.isChecked():
            self.log.setPlainText("")
        else:
            self.log.appendPlainText("*---------------------------*")

        if not self.canDeleteOverlapingPivot.isChecked() and self.canSkipCheck.isChecked():
            self.log.appendPlainText('Verify Overlap did nothing, verify checkbox if not wanted')
            return
        
        Objs = cmds.ls(sl = True)
        sel = om.MGlobal.getActiveSelectionList()
        if not sel.length():
            return self.log.appendPlainText('Nothing Selected')
        for selected in range(sel.length()):
            if not self.canSkipCheck.isChecked():
                dag = sel.getDagPath(selected)
                vertex_iter = om.MItMeshVertex(dag)
                indexTested = []
                for i in range(vertex_iter.count()):
                    vertex_iter.setIndex(i)
                    currentPos = vertex_iter.position()
                    for j in range(vertex_iter.count()):
                        if i == j:continue
                        if indexTested.__contains__(i) or indexTested.__contains__(j) : continue
                        vertex_iter.setIndex(j)
                        otherPos = vertex_iter.position()

                        if currentPos == otherPos:
                            indexTested.append(j)
                            indexTested.append(i)
                            self.log.appendPlainText('OVERLAPING VERTEX, {} with {}'.format(i,j))
                if(indexTested.__len__() == 0):
                    self.log.appendPlainText('No Overlap for {}'.format(dag))
                    return
            if self.canDeleteOverlapingPivot.isChecked():
                o = Objs[selected]
                cmds.select(o+'.vtx[*]')
                polyMergeVertex(d = .01)

    def verifyAll(self):
        sel = om.MGlobal.getActiveSelectionList()
        if not sel.length():
            return self.log.appendPlainText('Nothing Selected')
        
        self.verifyScale()
        self.verify_UV()
        self.verifyPivot()
        self.verifyOverlapingVertexs()
###
app = MayaChecker()
app.show()