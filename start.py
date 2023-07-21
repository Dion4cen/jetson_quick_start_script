from pick import pick
import subprocess
import argparse
import signal
import sys
import time
from datetime import datetime
import os
import threading

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

        if size and fps:
            if i not in list_resolution:
                list_resolution.append(resolution)
            resolution = ""
            size = False
            fps = False

    return list_resolution

def get_jetvariety_resolution():
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
    return list_resolution

def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)

def get_hat_data(i2c):
    i2caddress_Hat = 0x24
    i2caddress_year = 0x05
    i2caddress_month = 0x06
    i2caddress_date = 0x07
    
    year = sh_("i2cget -y {} {} {}".format(i2c, i2caddress_Hat, i2caddress_year)).strip()
    month = sh_("i2cget -y {} {} {}".format(i2c, i2caddress_Hat, i2caddress_month)).strip()
    date = sh_("i2cget -y {} {} {}".format(i2c, i2caddress_Hat, i2caddress_date)).strip()

    year = "20" + str(int(year, 16))
    month = str(int(month, 16))
    date = str(int(date, 16))


    time = year + "-" + month + "-" + date
    return time

def get_jetvariety_hat_data():
    
    year = sh_("python3 Jetvariety/rw_sensor.py -rd 0x0503 -vd 0x48050000")
    year = sh_("python3 Jetvariety/rw_sensor.py -rd 0x0503").decode('utf-8').split(": ")[-2].split(", ")[0][-2:]
    year = int(year, 16)
    month = sh_("python3 Jetvariety/rw_sensor.py -rd 0x0503 -vd 0x48060000")
    month = sh_("python3 Jetvariety/rw_sensor.py -rd 0x0503").decode('utf-8').split(": ")[-2].split(", ")[0][-2:]
    month = int(month, 16)
    date = sh_("python3 Jetvariety/rw_sensor.py -rd 0x0503 -vd 0x48070000")
    date = sh_("python3 Jetvariety/rw_sensor.py -rd 0x0503").decode('utf-8').split(": ")[-2].split(", ")[0][-2:]
    date = int(date, 16)

    time = "20" + str(year) + "-" + str(month) + "-" + str(date)

    return time

def get_now_time():
    now = int(round(time.time()*1000))
    now = time.strftime('%Y-%m-%d-%H-%M-%S',time.localtime(now/1000))
    return now

class Report:
    def __init__(self, id, file):
        self._id = id
        self._cmds = []
        self._strs = []
        self._file = file

    def __run_cmd(self, cmd):
        print(f'** {cmd} **', file=self._file)
        try:
            p = subprocess.run(cmd, universal_newlines=True, check=False, shell=True,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            print(p.stdout, file=self._file)
        except RuntimeError as e:
            print(f'Error: {e}', file=self._file)

    def add_cmd(self, c):
        self._cmds.append(c)

    def add_str(self, s):
        self._strs.append(s)

    def exec(self):
        print(f'{"-"*80}\n{self._id}\n{"-"*80}', file=self._file)

        for c in self._cmds:
            self.__run_cmd(c)

        for s in self._strs:
            print(s, file=self._file)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Test choose')

    parser.add_argument('-y', help='csi port', 
                    type=int, required=False, default=10)
                    
    parser.add_argument('-d',"--device", help='device num', 
                    type=int, required=False, default=0)

    parser.add_argument('-n', "--name", help='sensor name or sku',
                    type=str, required=False)

    parser.add_argument('-o', help='Report filename',
                    type=str, default='Hat-test-report.txt')

    args = parser.parse_args()

    signal.signal(signal.SIGINT,signal_handler)

    sensor_id = args.device
    csi_port = args.y
    v4l2 = False
    gst = False
    list_resolution = []
    title = 'Please choose your camera: '
    title_resolution = 'Please choose your resolution: '

    options = ['imx477', 'imx219', 'imx519', 'imx477-stereo', 'Jetvariety', 'Hat-test']
    option = pick(options, title)[0][0]
    camera_name = option

    isp = os.path.exists("/var/nvidia/nvcam/settings/camera_overrides.isp")
    if isp:
        isp = "isp"     
    else:
        isp = "noisp"
    if args.name:
        camera_name = args.name

    if option == "imx519":
        options = get_resolution()
        option = pick(options, title_resolution)[0][0]
        gst = True
    elif option == "imx477-stereo":
        options = get_resolution()
        option = pick(options, title_resolution)[0][0]
        gst = True

    elif option == "imx219":
        options = get_resolution()
        option = pick(options, title_resolution)[0][0]
        gst = True

    elif option == "imx477":
        options = get_resolution()
        option = pick(options, title_resolution)[0][0]
        gst = True   

    elif option == "Jetvariety":
        options = get_jetvariety_resolution()
        option = pick(options, title_resolution)[0][0]
        v4l2 = True

    elif option == "Hat-test":
        if pick(["normal_camera", "Jetvariety"], title_resolution)[0][0] == "Jetvariety":
            options = get_jetvariety_resolution()
            v4l2 = True
        else:
            options = get_resolution()
            gst = True   
        option = pick(options, title_resolution)[0][0]

        v4l2_set_four_camera="i2cset -y {} 0x24 0x24 0x00".format(csi_port)
        v4l2_set_two_camera="i2cset -y {} 0x24 0x24 0x01".format(csi_port)
        v4l2_set_single_camera="i2cset -y {} 0x24 0x24 0x02".format(csi_port)

        reports = []
    
        if gst:
            option = option.split('@')
            option_ = option[0].split('x')
            
            fps = option[1].split("fps")[0]

            with open(args.o, 'wt') as file:
                title = Report('nvidia Bug Report', file)
                title.add_str(
                    f'Date: {datetime.now().strftime("%d-%m-%Y (%H:%M:%S)")}')
                title.add_str(f'Command: {" ".join(sys.argv)}\n')
                reports.append(title)

                date = Report('Hat date', file)
                date.add_str(get_hat_data(csi_port))
                reports.append(date)

                test_1 = Report('1. 四目相机是否正常出图', file)
                gst_preview = " \
                    timeout 10s gst-launch-1.0 nvarguscamerasrc sensor_id={} ! \
                        'video/x-raw(memory:NVMM),width={}, height={}, framerate={}/1, format=NV12' ! \
                        nvvidconv flip-method=0 ! \
                        'video/x-raw,width=960, height=720' !  \
                        nvvidconv ! \
                        nvegltransform ! \
                        nveglglessink -e".format(sensor_id, option_[0], option_[1], fps)
                test_1.add_cmd(v4l2_set_four_camera)
                test_1.add_cmd(gst_preview)
                reports.append(test_1)

                test_2 = Report('2. 四通道存图', file)
                now = get_now_time()
                jpg_name = "{}_{}_{}_{}_{}_{}".format(isp, camera_name, "four_camera", option_[0], option_[1], get_now_time())
                gst_save_picture = " \
                gst-launch-1.0 nvarguscamerasrc num-buffers=20 sensor_id={} ! \
                    'video/x-raw(memory:NVMM),width={}, height={}, framerate={}/1, format=NV12' ! \
                    nvjpegenc ! \
                    multifilesink location={}.jpeg".format(sensor_id, option_[0], option_[1], fps, jpg_name)
                test_2.add_cmd(v4l2_set_four_camera)
                test_2.add_cmd(gst_save_picture)
                test_2.add_cmd("ls {}.jpeg".format(jpg_name))
                reports.append(test_2)

                test_3 = Report('3. 双通道存图', file)
                now = get_now_time()
                jpg_name = "{}_{}_{}_{}_{}_{}".format(isp, camera_name, "two_camera", option_[0], option_[1], get_now_time())
                gst_save_picture = " \
                gst-launch-1.0 nvarguscamerasrc num-buffers=20 sensor_id={} ! \
                    'video/x-raw(memory:NVMM),width={}, height={}, framerate={}/1, format=NV12' ! \
                    nvjpegenc ! \
                    multifilesink location={}.jpeg".format(sensor_id, option_[0], option_[1], fps, jpg_name)
                test_3.add_cmd(v4l2_set_two_camera)
                test_3.add_cmd(gst_save_picture)
                test_3.add_cmd("ls {}.jpeg".format(jpg_name))
                reports.append(test_3)

                test_4 = Report('4. 单通道存图', file)
                now = get_now_time()
                jpg_name = "{}_{}_{}_{}_{}_{}".format(isp, camera_name, "single_camera", option_[0], option_[1], get_now_time())
                gst_save_picture = " \
                gst-launch-1.0 nvarguscamerasrc num-buffers=20 sensor_id={} ! \
                    'video/x-raw(memory:NVMM),width={}, height={}, framerate={}/1, format=NV12' ! \
                    nvjpegenc ! \
                    multifilesink location={}.jpeg".format(sensor_id, option_[0], option_[1], fps, jpg_name)
                test_4.add_cmd(v4l2_set_single_camera)
                test_4.add_cmd(gst_save_picture)
                test_4.add_cmd("ls {}.jpeg".format(jpg_name))
                reports.append(test_4)

                test_5 = Report('5. 拔掉任意一路相机，是否出图', file)
                gst_preview = " \
                    timeout 5s gst-launch-1.0 nvarguscamerasrc sensor_id={} ! \
                        'video/x-raw(memory:NVMM),width={}, height={}, framerate={}/1, format=NV12' ! \
                        nvvidconv flip-method=0 ! \
                        'video/x-raw,width=960, height=720' !  \
                        nvvidconv ! \
                        nvegltransform ! \
                        nveglglessink -e".format(sensor_id, option_[0], option_[1], fps)

                test_5.add_cmd(v4l2_set_four_camera)
                test_5.add_cmd(gst_preview)
                reports.append(test_5)

                for r in range(len(reports)):
                    print(r)
                    if r == 6:
                        if input("y/n:") == 'y':
                            reports[r].exec()
                    elif r == 2:
                        t = threading.Thread(target=reports[r].exec)
                        t.start()
                        time.sleep(3)
                        sh_(v4l2_set_two_camera)
                        time.sleep(2)
                        sh_(v4l2_set_single_camera)
                        t.join()
                    else:
                        reports[r].exec()
    
                print(f'\nBug report generated to {args.o}')
        elif v4l2:
            with open(args.o, 'wt') as file:
                title = Report('nvidia Bug Report', file)
                title.add_str(
                    f'Date: {datetime.now().strftime("%d-%m-%Y (%H:%M:%S)")}')
                title.add_str(f'Command: {" ".join(sys.argv)}\n')
                reports.append(title)

                date = Report('Hat date', file)
                date.add_str(get_jetvariety_hat_data())
                reports.append(date)

                test_1 = Report('1. 四目相机是否正常出图', file)
                test_1.add_cmd("python3 ./Jetvariety/arducam_displayer.py --save")
                reports.append(test_1)

                test_2 = Report('2. 拔掉任意一路相机是否正常出图', file)
                test_2.add_cmd("timeout 10s python3 ./Jetvariety/arducam_displayer.py")
                reports.append(test_2)

                for r in range(len(reports)):
                    print(r)
                    if r == 3:
                        if input("y/n:") == 'y':
                            reports[r].exec()
                    else:
                        reports[r].exec()

        sys.exit(0)
    
    option_mode = pick(["perview", "save"], title_resolution)[0][0]

    if gst == True:
        option = option.split('@')
        option_ = option[0].split('x')
        fps = option[1].split("fps")[0]
        now = get_now_time()
        gst_preview = " \
            gst-launch-1.0 nvarguscamerasrc sensor_id={} ! \
                'video/x-raw(memory:NVMM),width={}, height={}, framerate={}/1, format=NV12' ! \
                nvvidconv flip-method=0 ! \
                'video/x-raw,width=960, height=720' !  \
                nvvidconv ! \
                fpsdisplaysink -e".format(sensor_id, option_[0], option_[1], fps)

        gst_save_picture = " \
            gst-launch-1.0 nvarguscamerasrc num-buffers=30 sensor_id={} ! \
                'video/x-raw(memory:NVMM),width={}, height={}, framerate={}/1, format=NV12' ! \
                nvjpegenc ! \
                multifilesink location={}_{}_{}_{}_{}.jpeg".format(sensor_id, option_[0], option_[1], fps, isp, camera_name, option_[0], option_[1], now)

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

