#!/usr/bin/python

# TODO
# Do a benchmark over the CPU/GPU
# checkout YUV versus MJPEG video (see v4l2-ctl --list-formats-ext)
# MJPEG seems better?
# Test torch native filters (e.g. lowpass_biquad)

import torch
import torchaudio
import numpy as np

# https://github.com/pytorch/audio/issues/1408
# from torchaudio.functional import lowpass_biquad
import cv2
import effects

class TensorGlitch:
    def __init__(self, webcam):
        # device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        # model = model.to(device)

        # convert from path to idea
        self.cap = cv2.VideoCapture(int(webcam[-1]), cv2.CAP_V4L2)

        # print(webcam_id)
        # ret, frame = self.cap.read()
        # print(ret, frame)
        # Supported resolutions
        # width=1280, height=720
        # width=960, height=540
        # width=848, height=480
        # width=640, height=480
        # width=640, height=360

        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        # self.cap.set(cv2.CAP_PROP_CONVERT_RGB, 0)
        self.xres = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.yres = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))


    def __del__(self):
        self.cap.release()

    # sample rate doesn't matter 
    def glitch(self, effect):
        ret, frame = self.cap.read()

        o, _ = torchaudio.sox_effects.apply_effects_tensor(
            torch.from_numpy(frame).view(1, 2764800), 16000, [effect])
        return o[0][:2764800].numpy()
        # frame = frame.reshape(1, 27=64800)
        # frame = torch.from_numpy(frame)
        # o, _ = torchaudio.sox_effects.apply_effects_tensor(
        #     frame, 16000, [effect])
        # return np.fliplr(o.numpy()[0][:2764800].reshape(720, 1280, 3))

    def benchmark(self):
        import time
        import gi
        gi.require_version("Gtk", "3.0")
        gi.require_version('GdkPixbuf', '2.0')
        from gi.repository import GLib, GdkPixbuf

        frames = [self.cap.read()[1] for i in range(120)]
        e = effects.Effect('reverb').torch_rep
        t0 = time.monotonic()
        for f in frames:
            o, _ = torchaudio.sox_effects.apply_effects_tensor(
                torch.from_numpy(f).view(1, 2764800), 16000, [e])
            
            # ___ Test numpy flip ___
            # o = np.fliplr(o[0][:2764800].view(720, 1280, 3).numpy())
            # b = GLib.Bytes.new(o.tobytes())
            # pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(b, GdkPixbuf.Colorspace.RGB, False, 8, 1280, 720, 3840)
            
            # ___ Test Pixbuf flip ___
            # b = GLib.Bytes.new(o.numpy().tobytes())
            # pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(b, GdkPixbuf.Colorspace.RGB, False, 8, 1280, 720, 3840)
            # s = pixbuf.flip(True)
            
            # ___ Test Torch ___
            # frame = torch.from_numpy(f.reshape(1, 2764800))
            # o, _ = torchaudio.sox_effects.apply_effects_tensor(
            #     frame, 16000, [e])
            # o = np.fliplr(o.numpy()[0][:2764800].reshape(720, 1280, 3))

        print('seconds:', time.monotonic() - t0)

if __name__ == '__main__':
    glitcher = TensorGlitch('/video/dev0')
    glitcher.benchmark()
    
    


