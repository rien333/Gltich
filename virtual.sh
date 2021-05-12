#!/usr/bin/sh

if [ "$1" = '-h' ]
then
   echo "virtual.sh video_file [/dev/videox]"
   echo "video_file will automatically be resized to 1280x720"
   exit
fi

if [ -z "$2" ]
then
    cam_out="/dev/video2"
else
    cam_out="$2"
fi

# This glitches things out immensily
# v4l2loopback-ctl set-caps "video/x-raw, format=UYVY, width=1280, height=720" "$cam_out"
# v4l2loopback-ctl set-timeout-image kinker-r.gif "$cam_out"  # doesn't work (I think)
# ffmpeg -loglevel error  -re -stream_loop -1  -i "$1" -pix_fmt yuv420p -vf scale=1280x720 -f v4l2 "$cam_out"
ffmpeg -loglevel error  -re -stream_loop -1  -i "$1" -pix_fmt yuv420p -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2" -f v4l2 "$cam_out"
