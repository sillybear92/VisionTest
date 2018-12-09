#coding=utf8
from pyparrot.DroneVision import DroneVision
from pyparrot.Minidrone import Mambo
import numpy as np
import cv2
import tracker
from mov import drawMov

drawing = False #Mouse가 클릭된 상태 확인용
ix,iy,tx,ty,bx,by = -1,-1,-1,-1,-1,-1

class UserVision:
	def __init__(self,vision):
		self.index=0
		self.vision = vision
		self.filename=None

	def get_image(self,args):
		print("in save pictures on image %d " % self.index)
		img = self.vision.get_latest_valid_picture()
		if (img is not None):
			filename = "test_image_%06d.png" % self.index
			cv2.imwrite(filename, img)
			self.index +=1
			self.filename=filename
            #print(self.index)


# Mouse Callback함수
def draw_bbox(event, x,y, flags, param):
	global ix,iy, drawing,px,py
	if event == cv2.EVENT_LBUTTONDOWN: #마우스를 누른 상태
		drawing = True 
		if ix==-1 and iy==-1:
			tx, ty = x,y
			ix, iy = x,y
			
	elif event == cv2.EVENT_LBUTTONUP:
		drawing = False;             # 마우스를 때면 상태 변경
		bx,by=x,y
		cv2.rectangle(mask,(tx,ty),(bx,by),(0,255,0),2)
		ix,iy=-1,-1
		
def main():
	tc=tracker.createTrackerByName("KCF")
	# 일반모드에서 블루투스를 사용하여 드론을 찾는다, 드론의 연결 주소와 이름이 반환된다 
	# addr,name = findMinidrone.getMamboAddr()
	addr = None
	# 드론 객체 생성 FPV의 경우는 WIFI를 사용하며, use_wifi = True가 된다
	mambo = Mambo(addr,use_wifi=True)
	# 드론을 연결한다
	success=mambo.connect(3)
	print("Connect: %s" %success)
	mambo.smart_sleep(0.01)
	# 드론의 상태를 업데이트 한다
	mambo.ask_for_state_update()
	# 드론의 움직임 기울기를 1로 설정한다
	mambo.set_max_tilt(1)
	# 드론의 배터리를 확인 할 수 있다
	battery=mambo.sensors.battery

	# FPV 연결
	mamboVision = DroneVision(mambo, is_bebop=False, buffer_size=30)
	userVision=UserVision(mamboVision)
	mamboVision.set_user_callback_function(userVision.get_image, user_callback_args=None)
	cv2.namedWindow('Vision')
	cv2.setMouseCallback('Vision',draw_bbox)
	success = mamboVision.open_video()
	img = cv2.imread(mamboVision.filename,cv2.IMREAD_COLOR)
	mask = np.ones_like(img,dtype=np.uint8)

	tc=tracker.createTrackerByName("KCF")
	# Tracking Mode
	mode=False
	bbox=[]
	angleStack,yawTime=0,0

	mov = drawMov()
	mov.mambo=mambo
	while(True):
		# OpenCV를 바탕으로 드론을 제어 하기위해 마스킹이미지를 생성한다
		# mask = np.ones((480,600,3),dtype=np.uint8)
		img = cv2.imread(mamboVision.filename,cv2.IMREAD_COLOR)
		print(img.shape)
		# 드론과 연결이 끊기지 않기 위해 매 프레임마다 상태 확인 신호를 보낸다
		mambo.smart_sleep(0.01)
		# 드론의 배터리를 확인 할 수 있다
		battery=mambo.sensors.battery
		print("Battery: %s" %battery)
		#img=cv2.add(img,mask)
		#if mode==True:
		#	bbox=tracker.updateTracker(img,tc)
		#	angleStack,yawTime=mov.adjPos(mask,bbox,angleStack,yawTime)
		cv2.imshow("Vision",mask)
		key=cv2.waitKey(10)
		# 'q' 키를 누르면 드론을 착륙하고 프로세스를 종료한다
		if ord('q')==key:
			mambo.safe_land(5)
			mamboVision.close_video()
			exit(0)
		# 'p' 키를 누르면 드론이 이륙한다
		elif ord('p')==key:
			mambo.safe_takeoff(5)
		# 'w' 키를 누르면 드론에 앞으로 100 만큼 움직이라는 신호를 0.1초간 보낸다
		elif ord('w')==key:
			mambo.fly_direct(roll=0,pitch=100,yaw=0,vertical_movement=0,duration=0.1)
		# 's' 키를 누르면 드론에 뒤로 100 만큼 움직이라는 신호를 0.1초간 보낸다
		elif ord('s')==key:
			mambo.fly_direct(roll=0,pitch=-100,yaw=0,vertical_movement=0,duration=0.1)
		# 'a' 키를 누르면 드론에 왼쪽으로 50 만큼 움직이라는 신호를 0.1초간 보낸다
		elif ord('a')==key:
			mambo.fly_direct(roll=-50,pitch=0,yaw=0,vertical_movement=0,duration=0.1)
		# 'd' 키를 누르면 드론에 오른쪽으로 50 만큼 움직이라는 신호를 0.1초간 보낸다
		elif ord('d')==key:
			mambo.fly_direct(roll=50,pitch=0,yaw=0,vertical_movement=0,duration=0.1)
		elif ord('i')==key:
			mambo.fly_direct(roll=0,pitch=0,yaw=0,vertical_movement=50,duration=0.1)
		elif ord('k')==key:
			mambo.fly_direct(roll=0,pitch=0,yaw=0,vertical_movement=-50,duration=0.1)
		elif ord('j')==key:
			mambo.fly_direct(roll=0,pitch=0,yaw=-50,vertical_movement=0,duration=0.1)
		elif ord('l')==key:
			mambo.fly_direct(roll=0,pitch=0,yaw=50,vertical_movement=0,duration=0.1)
		elif ord('c')==key:
			mask = np.ones((480,600,3),dtype=np.uint8)
		elif ord('v')==key:
			print("tracker start")
			bbox=[tx,ty,bx-tx,by-ty]
			mode=True
			ok=tc.init(img,bbox)
			mov.setBox([tx,ty,bx,by])

if __name__=='__main__':
	main()
