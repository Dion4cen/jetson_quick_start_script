from pick import pick
import subprocess
import signal
import sys
import time
import os

def sh_(cmd):
    """ Execute shell commands """
    p = subprocess.check_output(cmd, shell=True)
    return p

def get_resolution():

    size = False
    fps = False
    resolution = ""

    try:
        str_v4l2 = sh_("v4l2-ctl --list-formats-ext")
    except:
        sh_("sudo apt install v4l-utils")
        str_v4l2 = sh_("v4l2-ctl --list-formats-ext")
    
    str_v4l2 = str_v4l2.decode("utf-8").replace('\t', '').split('\n')
    for i in str_v4l2:
        if "Size" in i:
            i = i.split(" ")[-1]
            size = True
            resolution += i 
        elif "fps" in i:
            i = i.split("(")[-1].split("fps)")
            fps = True
            resolution = resolution + "@" + str(int(float(i[0].strip())))
            # print(resolution)

        if size and fps:
            if i not in list_resolution:
                list_resolution.append(resolution)
            resolution = ""
            size = False
            fps = False

    return list_resolution

def signal_handler(signal,frame):
    print('You pressed Ctrl+C!')
    stop = True
    sys.exit(0)

signal.signal(signal.SIGINT,signal_handler)

stop = False
v4l2 = False
gst = False
list_resolution = []
title = 'Please choose your camera: '
title_resolution = 'Please choose your resolution: '
sensor_id = sys.argv[1]


options = ['imx477', 'imx219', 'imx519', 'imx477-stereo', 'jetvariety']
option = pick(options, title)[0][0]

if option == "imx519":
    camera_name = option
    # options = ['4656x3496@10fps', '3840x2160@21fps', '1920x1080@60fps', '1280x720@120fps']
    options = get_resolution()
    option = pick(options, title_resolution)[0][0]
    gst = True
elif option == "imx477-stereo":
    camera_name = option
    # options = ['4056x3040@10fps', '2028x1520@30fps', '2028x1080@30fps']
    options = get_resolution()
    option = pick(options, title_resolution)[0][0]
    gst = True

elif option == "imx219":
    camera_name = option
    # options = ['3264x2464@15fps', '3264x1848@28fps', '1920x1080@30fps', '1640x1232@30fps', '1280x720@60fps']
    options = get_resolution()
    option = pick(options, title_resolution)[0][0]
    gst = True

elif option == "imx477":
    camera_name = option
    # options = ['4032x3040@30fps', '3840x2160@21fps', '1920x1080@60fps']
    options = get_resolution()
    option = pick(options, title_resolution)[0][0]
    gst = True   

elif option == "jetvariety":
    v4l2 = True
    # try:
    #     str_v4l2 = sh_("v4l2-ctl --list-formats-ext")
    # except:
    #     sh_("sudo apt install v4l-utils")
    #     str_v4l2 = sh_("v4l2-ctl --list-formats-ext")
    
    # str_v4l2 = str_v4l2.decode("utf-8").replace('\t', '').split('\n')
    # for i in str_v4l2:
    #     if "Size" in i:
    #         i = i.split(" ")[-1]
    #         if i not in list_resolution:
    #             list_resolution.append(i)
    options = get_resolution()
    option = pick(options, title_resolution)[0][0]

option_mode = pick(["perview", "save"], title_resolution)[0][0]

try:
    camera_name = sys.argv[2]
except:
    pass

isp = os.path.exists("/var/nvidia/nvcam/settings/camera_overrides.isp")
if isp:
    isp = "isp"     
else:
    isp = "noisp"

if gst == True:
    option = option.split('@')
    option_ = option[0].split('x')
    now = int(round(time.time()*1000))
    now = time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(now/1000))
    gst_preview = " \
        gst-launch-1.0 nvarguscamerasrc sensor_id={} ! \
            'video/x-raw(memory:NVMM),width={}, height={}, framerate={}/1, format=NV12' ! \
            nvvidconv flip-method=0 ! \
            'video/x-raw,width=960, height=720' !  \
            nvvidconv ! \
            nvegltransform ! \
            nveglglessink -e".format(sensor_id, option_[0], option_[1], option[1].split("fps")[0])

    gst_save_picture = " \
        gst-launch-1.0 nvarguscamerasrc num-buffers=30 sensor_id={} ! \
            'video/x-raw(memory:NVMM),width={}, height={}, framerate={}/1, format=NV12' ! \
            nvjpegenc ! \
            multifilesink location={}_{}_{}_{}_{}.jpeg".format(sensor_id, option_[0], option_[1], option[1].split("fps")[0], isp, camera_name, option_[0], option_[1], now)

    try:
        if option_mode == "perview":
            sh_(gst_preview)
        elif option_mode == "save":
            sh_(gst_save_picture)
    except:
        print("Open camera error.")
elif v4l2 == True:
    option = option.split('x')
    try:
        sh_("cd MIPI_Camera/Jetson/Jetvariety/example/ && python3 arducam_displayer.py --width {} --height {}".format(option[0], option[1]))  
    except KeyboardInterrupt:
        pass
    else:
        sh_("sudo apt-get update && sudo apt install nvidia-opencv")
        sh_("sudo apt install python3-pip && pip3 install v4l2-fix")
        sh_("cd MIPI_Camera/Jetson/Jetvariety/example/ && python3 arducam_displayer.py -width {} --height {}".format(option[0], option[1]))

