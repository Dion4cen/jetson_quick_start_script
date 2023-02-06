from pick import pick
import subprocess
import signal
import sys

def sh_(cmd):
    """ Execute shell commands """
    p = subprocess.check_output(cmd, shell=True)
    return p

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

options = ['imx477', 'imx219', 'imx519', 'imx477-stereo', 'jetvariety']
option = pick(options, title)[0][0]

if option == "imx519":
    options = ['4656x3496@8fps', '3840x2160@18fps', '1920x1080@60fps', '1280x720@120fps']
    option = pick(options, title_resolution)[0][0]
    gst = True
elif option == "imx477-stereo":
    options = ['4056x3040@10fps', '2028x1520@30fps', '2028x1080@30fps']
    option = pick(options, title_resolution)[0][0]
    gst = True

elif option == "imx219":
    options = ['3264x2464@21fps', '3264x1848@28fps', '1920x1080@30fps', '1640x1232@30fps', '1280x720@60fps']
    option = pick(options, title_resolution)[0][0]
    gst = True

elif option == "imx477":
    options = ['4032x3040@30fps', '3840x2160@30fps', '1920x1080@60fps']
    option = pick(options, title_resolution)[0][0]
    gst = True   

elif option == "jetvariety":
    v4l2 = True
    try:
        str_v4l2 = sh_("v4l2-ctl --list-formats-ext")
    except:
        sh_("sudo apt install v4l-utils")
        str_v4l2 = sh_("v4l2-ctl --list-formats-ext")
    
    str_v4l2 = str_v4l2.decode("utf-8").replace('\t', '').split('\n')
    for i in str_v4l2:
        if "Size" in i:
            i = i.split(" ")[-1]
            if i not in list_resolution:
                list_resolution.append(i)
    options = list_resolution
    option = pick(options, title_resolution)[0][0]

if gst == True:
    option = option.split('@')
    option_ = option[0].split('x')
    str_gst = " \
    gst-launch-1.0 nvarguscamerasrc sensor_id=0 ! \
        'video/x-raw(memory:NVMM),width={}, height={}, framerate={}/1, format=NV12' ! \
        nvvidconv flip-method=0 ! \
        'video/x-raw,width=960, height=720' !  \
        nvvidconv ! \
        nvegltransform ! \
        nveglglessink -e".format(option_[0], option_[1], option[1].split("fps")[0])

    try:
        print(str_gst)
        subprocess.check_call(str_gst, shell=True)
        # print(output_str_gst.decode("utf-8"))
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
