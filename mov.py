#coding=utf8
import cv2
import numpy as np
import math
from pyparrot.Minidrone import Mambo

class drawMov:
	def __init__(self):
		self.tx,self.ty,self.bx,self.by = None,None,None,None
		self.top=None
		self.bottom = None
		self.left = None
		self.right = None
		self.width = None
		self.height = None
		self.center = None
		self.mambo = None
		self.inBox=(220,300) #(130,300)->(250,300)->(260,380) width height
		self.outBox=(340,370) #(200,380)->(330,380)->(330,450) width height
		self.inBoxPos=[]
		self.outBoxPos=[]

	def setBox(self,target):
		width=target[2]-target[0]
		height=target[3]-target[1]
		self.inBox=(width-50,height-35)
		self.outBox=(width+50,height+35)
		
	# 이미지의 크기를 기준으로 드론 움직임의 기준이 되는 InBOX, OutBOX 표현
	def getInOutBoxPos(self,img):
		standardCenter=getStandardCenter(img)
		self.inBoxPos=[int(standardCenter[0]-self.inBox[0]/2),int(standardCenter[1]-self.inBox[1]/2),
			int(standardCenter[0]+self.inBox[0]/2),int(standardCenter[1]+self.inBox[1]/2)]
		self.outBoxPos=[int(standardCenter[0]-self.outBox[0]/2),int(standardCenter[1]-self.outBox[1]/2),
			int(standardCenter[0]+self.outBox[0]/2),int(standardCenter[1]+self.outBox[1]/2)]
		return standardCenter


	def getCenter(self,bbox):
		return [int((bbox[2]+bbox[0])/2),int((bbox[3]+bbox[1])/2)]

	def drawLine(self,img):
		#moveCenter=self.getCenter(bbox)
		moveCenter=self.getStandardCenter(img)
		cv2.line(img,(self.center[0],self.center[1]),(moveCenter[0],moveCenter[1]),(255,0,0),2)

	# 타겟의 위치와 이미지의 중앙점을 선으로 잇고 -Y축 기준으로 드론의 회전 각을 계산한다
	def getAngle(self,img):
		moveCenter=self.getStandardCenter(img)
		distance=math.sqrt((moveCenter[0]-self.center[0])**2+(moveCenter[1]-self.center[1])**2)
		cTheta=(moveCenter[1]-self.center[1])/(distance+10e-5)
		angle=math.degrees(math.acos(cTheta))
		return angle

	def drawCenter(self,img):
		cv2.circle(img,tuple(self.center),2,(255,0,0),-1)

	# 드론의 수직이동 값 계산
	def adjustVertical(self):
		vertical=0
		ih=self.inBoxPos[1]
		oh=self.outBoxPos[1]
		vt=self.top
		if vt < oh:
			vertical = 10
		elif vt > ih :
			vertical = -10
		return vertical

	# 드론의 수평이동, Yaw, Yaw 횟수 계산
	def adjustCenter(self,img,stack,yawTime):
		# right + , front +, vertical
		roll, yaw = 0,0
		angle=0
		yawCount=yawTime
		stackLR=stack
		standardCenter=self.getStandardCenter(img)
		#cv2.putText(img,"center",tuple(standardCenter),cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(0,0,255),2)
		roll=self.center[0]-standardCenter[0]
		if roll < -1 :
			roll = -20
			stackLR -= 1
		elif roll > 1 :
			roll = 20
			stackLR += 1
		if yawCount <-1:
			yaw=-50
			yawCount += 1
		elif yawCount >1 :
			yaw = 50
			yawCount -= 1
		if stackLR > 20 :
			angle = self.getAngle(img)
			stackLR = 0
			print('angle: ', angle)
			yawCount=int(angle/7)
		elif stackLR < -20:
			angle = -(self.getAngle(img))
			stackLR = 0
			print('angle: ', angle)
			yawCount=int(angle/7)
		return roll,yaw,stackLR,yawCount

	def getStandardCenter(self,img):
		return [int(img.shape[1]/2),int(img.shape[0]/2+120)]
		#80->150->0->80

	def drawStandardBox(self,img):
		standardCenter=self.getInOutBoxPos(img)
		cv2.circle(img,tuple(standardCenter),2,(0,0,255),-1)
		cv2.rectangle(img,(self.inBoxPos[0],self.inBoxPos[1]),
			(self.inBoxPos[2],self.inBoxPos[3]),(0,0,255),1)
		cv2.rectangle(img,(self.outBoxPos[0],self.outBoxPos[1]),
			(self.outBoxPos[2],self.outBoxPos[3]),(0,0,255),1)

	def adjustBox(self,img):
		pitch = 0
		if self.width*self.height<self.inBox[0]*self.inBox[1]:
			pitch = 30
		elif self.width*self.height>self.outBox[0]*self.outBox[1]:
			pitch = -30
		return pitch

	# 타겟의 위치에 따른 드론의 직접적인 움직임 제어
	def adjPos(self,img,target,angleStack,yawTime):
		roll,pitch,yaw,vertical,duration=0,0,0,0,0.1
		angle=0
		self.drawStandardBox(img)
		stack=angleStack
		cv2.putText(img, "Following The Target", (5,60), cv2.FONT_HERSHEY_SIMPLEX, 0.75,(0,0,255),2)
		self.setTarget(target)
		vertical=self.adjustVertical()
		if vertical == 0:
			pitch = self.adjustBox(img)
			roll,yaw,stack,yawTime=self.adjustCenter(img,stack,yawTime)
		pos=[roll,pitch,yaw,vertical]
		if pos==[0,0,0,0]:
			stack=0
		else:
			self.mambo.fly_direct(roll=roll, pitch=pitch, yaw=yaw, vertical_movement=vertical, duration=duration)
			print('Roll:',roll,' Pitch:',pitch,' Yaw:',yaw,' Vertical:',vertical)

		return stack,yawTime
