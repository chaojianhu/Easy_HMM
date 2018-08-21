#! monkeyrunner
# -*- coding: utf-8 -*-

import sys, os, time, ast, signal, logging

from com.android.monkeyrunner import MonkeyRunner
from com.android.monkeyrunner import MonkeyDevice
from randdom import randint
from subprocess import *


gCurrentWorkPath = os.path.split(os.path.realpath(__file__))[0]  # current work path
os.chdir(gCurrentWorkPath)

if not('argparse' in sys.path):
    sys.path.append(os.path.join(gCurrentWorkPath, 'argparse'))  # add argparse to search path
import argparse

gDeviceID = 'emulator-5554'
gDevice = None  # Object returned by MonkeyRunner.waitForConnection
gApkPath = os.path.join(gCurrentWorkPath, 'apks')
gLogPath = os.path.join(gCurrentWorkPath, 'logs')
gAnalyzedApkFile = None
gAnalyzedApkList = []
gLoop = 3
gPerApkDuration = 2  # second
gPerActDuration = 3  # second
gPerOrdDuration = 0.3
gActNumber = 30  # Number of Activities to be tested per package

loggings.basicConfig(
    filename=os.path.join(gLogPath, 'run.log'),
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
    )


def commandParse():
    global gLogPath, gAnalyzedApkFile, gAnalyzedApkList, gLoop, gPerApkDuration, gPerActDuration, gPerOrdDuration, gActNumber
    parser = argparse.ArgumentParser()
    parser.add_argument('--loop', help='Repeated Operations number', type=int)
    parser.add_argument('--apkdur', help='Per APK testing duration', type=float)
    parser.add_argument('--actdur', help='Per Activity testing duration', type=float)
    parser.add_argument('--orddur', help='Per Order testing duration', type=float)
    parser.add_argument('--actnum', help='Number of Activities to be tested per package', type=int)
    
    args = parser.parse_args()
    if len(sys.argv) > 1:
        if sys.argv[1] == '-h' or sys.argv[1] == '--help':
            sys.exit(1)
    
    if args.loop:
        gLoop = int(args.loop)
    
    if args.apkdur:
        gApkDuration = float(args.apkdur)
    if args.actdur:
        gPerActDuration = float(args.actdur)
    if args.orddur:
        gPerOrdDuration = float(args.orddur)
    
    if args.actnum:
        gActNumber = int(args.actnum)
    
    # Record analyzed apks
    analyzedApkFilePath = os.path.join(gLogPath, 'AnalyzedList.txt')
    if os.path.isfile(analyzedApkFilePath):  # file already exist 
        gAnalyzedApkFile = open(analyzedApkFilePath, 'r+')
        gAnalyzedApkFile.seek(0, 0)
        gAnalyzedApkList = gAnalyzedApkFile.readlines()
    else:
        gAnalyzedApkFile = open(analyzedApkFilePath, 'a')
        gAnalyzedApkList = []


def getPackageNameAndActivity(apkName):
    # Obtain package name and activities of apk
    global gCurrentWorkPath, gApkPath
    script_path = os.path.join(gCurrentWorkPath, 'apk_parse3', 'parse.py')
    p = Popen(['python', script_path, os.path.join(gApkPath, apkName)], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    context = p.stdout.read().split('\n')
    if context[0] == 'Usage: parse.py [apk_path]':
        print('Error-getPackageNameAndActivity: incorrect arguments to parse.py')
        sys.exit(1)
    if len(context) < 3:
        print('Error-getPackageNameAndActivity: APK parse error')
        return '', '', ''
    pkgName = context[0].strip()
    mainActivity = context[1].strip()
    allActivities = context[2].strip()
    if len(allActivities) > 0:
        allActivities = ast.literal_eval(allActivities)
    else:
        allActivities = [mainActivity, ]
    return pkgName, mainActivity, allActivities


def checkDeviceConnect():
    # check whether the device is connected
    global gDeviceID, gDevice
    count_try = 0
    while gDevice is None:
        # Try to connect
        if count_try > 30:
            print('Exceed maximum number of tries for connecting device')
            sys.exit(1)
        try:
            count_try += 1
            print('Trying %d times to connect device' % count_try)
            gDevice = MonkeyRunner.waitForConnection(2, gDeviceID)
        except:
            time.sleep(2)
            continue
        
        # Check whether connected
        try: 
            prop_result = gDevice.getProperty('build.device')
        except:
            prop_result = None
        if prop_result is None:
            gDevice = None
        else:
            print('Successfully Connected to device %s' % gDeviceID)
            break
    return


def checkPkgRunning(pkgName):
    # Check whehter package is running
    global gDevice
    info = gDevice.shell('dumpsys activity activities | grep TaskRecord')
    if info and info.find(pkgName) == -1:
        return False
    else:
        return True


def triggerActivity(pkgName, mainActivity, act):
    global gDevice, gDeviceID, gPerOrdDuration, gPerActDuration, gApkDuration
    
    # Start the mainActivity of the package
    componentName = pkgName + '/' + mainActivity
    print('Start mainActivity %s of %s' % (componentName, pkgName))
    gDevice.startActivity(component=componentName)
    checkDeviceConnect()
    time.sleep(gPerApkDuration)
    
    # Start an activity of the package
    componentName = pkgName + '/' + act
    print('Start Activity %s of %s' % (componentName, pkgName))
    gDevice.startActivity(componentName)
    checkDeviceConnect()
    time.sleep(gPerActDuration)
    
    for _ in range(0, gLoop):
        gDevice.touch(randint(0, 1078), randint(70, 1780), MonkeyDevice.DOWN_AND_UP)
        checkPkgRunning(pkgName)
        time.sleep(gPerOrdDuration)
        for var_x in range(100, 901, 400):
            gDevice.touch(var_x, 160, MonkeyDevice.DOWN_AND_UP)
            checkPkgRunning(pkgName)
            time.sleep(gPerOrdDuration)
        gDevice.drag((500, randint(70, 1078)), (500, randint(70, 1780)), 0.3)
        checkPkgRunning(pkgName)
        time.sleep(gPerOrdDuration)
        gDevice.touch(randint(0, 1078), randint(70, 1780), MonkeyDevice.DOWN_AND_UP)
        checkPkgRunning(pkgName)
        time.sleep(gPerOrdDuration)
        gDevice.touch(550, 950, MonkeyDevice.DOWN_AND_UP)
        checkPkgRunning(pkgName)
        time.sleep(gPerOrdDuration)
        for var_x in range(250, 851, 300):
            gDevice.touch(var_x, 1700, MonkeyDevice.DOWN_AND_UP)
            checkPkgRunning(pkgName)
            time.sleep(gPerOrdDuration)
        gDevice.drag((1000, 1720), (500, 1720), 0.3)
        checkPkgRunning(pkgName)
        time.sleep(gPerOrdDuration)
        gDevice.drag((1000, 150), (500, 150), 0.3)
        checkPkgRunning(pkgName)
        time.sleep(gPerOrdDuration)
        gDevice.press('KEYCODE_BACK', MonkeyDevice.DOWN_AND_UP)
        checkPkgRunning(pkgName)
        time.sleep(gPerOrdDuration)
    
    gDevice.press('KEYCODE_HOME', MonkeyDevice.DOWN_AND_UP)
    checkPkgRunning(pkgName)
    time.sleep(gPerOrdDuration)
    
    return True


def stopPkg(pkgName):
    global gDevice
    print('Kill all activities associated with %s' % pkgName)
    gDevice.shell('am kill %s' % pkgName)


def installAPK(apkName):
    global gDevice, gApkPath
    installRslt = gDevice.installPackage(os.path.join(gApkPath, apkName))
    if installRslt:
        return 1  # Success,  installRslt is boolean
    else:
        return 0


def getPkgUID(pkgName):
    global gDevice
    pkgUID = ''
    pkgInfoLine = gDevice.shell('su 0 cat /data/system/packages.list | grep %s' % pkgName)
    if pkgInfoLine and len(pkgInfoLine) > 0:
        pkgInfoList = pkgInfoLine.split()
        if len(pkgInfoList) > 1:
            pkgUID = pkgInfoList[1]
    return pkgUID


def testAPK(apkName):
    global gDevice, gDeviceID, gPerOrdDuration, gPerActDuration, gApkDuration
    pkgName, mainActivity, allActivities = getPackageNameAndActivity(apkName)
    if len(pkgName) == 0 or len(allActivities) == 0:
        print('error-testAPK: package name or activities of %s is empty' %apkName)
        return 0
    
    # Check whether apk was analyzed
    for analyzedApk in gAnalyzedApkList:
        if analyzedApk.startswith(apkName + '_' + pkgName + '_'):
            print('%s with pkg %s has ayalyzed before, pass' % (apkName, pkgName))
            return 0  # already analyzed

    if mainActivity not in allActivities:
        mainActivity = allActivities[0]
    
    # Trunck activities
    if len(allActivities) > 30:
        allActivities = allActivities[:gActNumber]
    
    # Insert traffic flag 
    gDevice.shell('pkill ping')
    print('ping -c 1 -w 2 6a9c428b47.%s' %pkgName)
    gDevice.shell('ping -c 1 -w 2 6a9c428b47.%s' %pkgName)
    time.sleep(2)
    
    # Install apk
    installRslt = installAPK(apkName)
    if installRslt == 1:
        print('successfully installed %s' % apkName)
    else:
        print('failed install %s' % apkName)
        return 0
    
    # Get UID of the package
    pkgUID = getPkgUID(pkgName)
    if len(pkgUID) == 0:
        print('Error-analyzedApk: UID of %s is not found' % pkgName)
        return 0
    
    # Start the mainActivity of the package
    componentName = pkgName + '/' + mainActivity
    checkDeviceConnect()
    time.sleep(gPerApkDuration)
    
    for x in range(770, 900, 50):
        for y in range(970, 1100, 50):
            gDevice.touch(x, y, MonkeyDevice.DOWN_AND_UP)
            time.sleep(gPerOrdDuration)
    
    for act in allActivities:
        checkDeviceConnect()
        try:
            triggerActivities(pkgName, mainActivity, act)
        except:
            pass
        stopPkg(pkgName)
    
    checkDeviceConnect()
    
    # Remove the package
    if gDevice.removePackage(pkgName):
        print('successfully removed %s' % apkName)
    else:
        print('failed to remove %s' % apkName)
    
    # Record analyzed package
    gAnalyzedApkList.append(apkName + '_' + pkgName + '_' + pkgUID + '\n')
    gAnalyzedApkFile.seek(0, 2)
    gAnalyzedApkFile.write(apkName + '_' + pkgName + '_' + pkgUID + '\n')
    gAnalyzedApkFile.flush()
    
    return len(allActivities)


def startEmulator():
    cmd = os.path.join('~/Android/Sdk/emulator/', 'emulator  -avd Nexus_5X_API_25x86 -tcpdump %s' % time.strftime('%Y-%m-%d-%H-%M-%S.pcap', time.localtime()))
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    time.sleep(30)


def execute():
    global gDeviceID, gDevice
    startEmulator()
    commandParse()
    checkDeviceConnect()
    for apkName in os.listdir(gApkPath):
        testAPK(apkName)
    
    # Shutdown device and stop emulator
    gDevice.shell('reboot -p')


def exitGracefully(signum, frame):
    global gDevice, gAnalyzedApkFile
    if gDevice:
        gDevice.shell('killall com.android.commands.monkey')
    if gAnalyzedApkFile:
        gAnalyzedApkFile.close()
    sys.exit(1)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, exitGracefully)
    execute()
