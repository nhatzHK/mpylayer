#!/usr/bin/python

# to play sounds
import simpleaudio as saudio
# to invoke the video player
import subprocess

from pythonosc import dispatcher as osc_dispatcher
from pythonosc import osc_server

# map of wav files paths
soundsPath = {"medieval": "medieval.wav",
        "futur": "futur.wav",
        "effet1": "effet1.wav"}

# map of video file paths
videosPath = {"francais": "videoFr.mp4",
        "anglais": "videoEn.mp4"}

# map to contain the audio data once loaded in memory
soundObjects = {}

# current sound data
currentSound = None
# handle to manage the sound player
soundPlayerHandle = None

# current video path
videoSource = None
# handle to manage the child process (the video player)
videoProcessHandle = None

# path to the video player to be invoked to play video files
VIDEO_PLAYER = "/bin/mpv"

oscDispatcher = osc_dispatcher.Dispatcher()
# ip to listen to
neoIP = "127.0.0.1"
port = 9999
oscServer = osc_server.ThreadingOSCUDPServer((neoIP, port), oscDispatcher)

def setup():
    global oscDispatcher
    global soundObjects
    global videoProcessHandle

    # map osc labels to methods
    oscDispatcher.map("/francais", setSource)
    oscDispatcher.map("/anglais", setSource)
    oscDispatcher.map("/medieval", changeMusic)
    oscDispatcher.map("/futur", changeMusic)
    oscDispatcher.map("/effet1", playEffect)
    oscDispatcher.map("/video", playVideo)
    oscDispatcher.map("/reset", reset)

    # read audio data in memory
    soundObjects = {path: saudio.WaveObject.from_wave_file(soundsPath[path]) for path in soundsPath}

    # run a no-op option to set the initial value of the handle
    videoProcessHandle = subprocess.Popen("true")
    while videoProcessHandle.poll() is None:
        videoProcessHandle.kill()

def main():
    global soundPlayerHandle
    global soundObjects
    global currentSound
    global videoSource

    videoSource = videosPath["francais"]
    currentSound = soundObjects["futur"]
    soundPlayerHandle = currentSound.play()
    oscServer.serve_forever() # start server

def reset(addr):
    # stop video if playing
    while videoProcessHandle.poll() is None:
        videoProcessHandle.kill()

    # stop all audio
    saudio.stop_all()

    # normal boot process
    setup()
    main()

def setSource(addr):
    global videoSource
    global videosPath
    global videoProcessHandle

    # video is already playing, do nothing
    # TODO: (DISCUSS) set the source anyway for next time it's played??
    if videoProcessHandle.poll() is None:
        report_error("Video is already playing")
        return

    lang = addr.split("/")[1]
    if lang in videosPath:
        videoSource = videosPath[lang]
        report_success(f"Language set to {lang}")
    else:
        report_error(f"No path to set for language: {lang}")

def playVideo(addr):
    global videosPath
    global videoProcessHandle
    global videoSource
    global VIDEO_PLAYER
    global soundPlayerHandle

    # while it's None the video is still playing
    if videoProcessHandle.poll() is None:
        report_error("Video is already playing")
        return

    # play all sound before playing
    if soundPlayerHandle.is_playing():
        soundPlayerHandle.stop()
        soundPlayerHandle.wait_done()

    print(VIDEO_PLAYER)
    print(videoSource)
    videoProcessHandle = subprocess.Popen([VIDEO_PLAYER, videoSource])
    videoProcessHandle.wait() # play video to the end

    # restart sound after the video
    soundPlayerHandle = currentSound.play()

def changeMusic(addr):
    global soundObjects
    global soundPlayerHandle
    global currentSound

    # video is playing do nothing
    # TODO: (DISCUSS) set new audio target anyway for next time to play
    if videoProcessHandle.poll() is None:
        report_error("Video is playing")
        return

    sound = addr.split("/")[1] 
    if sound in soundObjects:
        if soundPlayerHandle.is_playing():
            soundPlayerHandle.stop()
        currentSound = soundObjects[sound]
        soundPlayerHandle = currentSound.play()
    else:
        report_error("No such sound")

def playEffect(addr):
    global soundPlayerHandle
    global currentSound

    effect = addr.split("/")[1]
    if effect not in soundObjects:
        report_error("No such effect")
        return

    if videoProcessHandle.poll() is None:
        report_error("Video is playing")
        return

    # stop music before playing effect
    if soundPlayerHandle.is_playing():
        soundPlayerHandle.stop()
        soundPlayerHandle.wait_done() # wait until it's really stopped

    # play effect to the end
    effectHandle = soundObjects[effect].play()
    effectHandle.wait_done()

    # restart playing music after teh effect
    soundPlayerHandle = currentSound.play()

# report an error occured while doing an operation
def report_error(str):
    print(str)

# report an operation was performed successfully
def report_success(str):
    print(str)
 
if __name__ == '__main__':
    setup()
    main()
