#!/usr/bin/env python3
"""Test for segmentation fault in MoviePy VideoToolbox encoding"""

import logging
import signal
import sys

# Set up timeout handler
def timeout_handler(signum, frame):
    print("TIMEOUT: Process hung, terminating...")
    sys.exit(124)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(60)  # 60 second timeout

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    from moviepy.editor import ColorClip, TextClip, CompositeVideoClip
    
    print("Step 1: Creating test clip...")
    clip = ColorClip(size=(1920, 1080), color=(0,0,0), duration=2)
    txt = TextClip('Test', fontsize=50, color='white', size=(1920, 1080))
    final = CompositeVideoClip([clip, txt.set_duration(2)])
    
    print("Step 2: Attempting h264_videotoolbox render...")
    final.write_videofile(
        '/tmp/test_vt.mp4', 
        fps=30,
        codec='h264_videotoolbox',
        audio=False,
        ffmpeg_params=['-allow_sw', '1', '-pix_fmt', 'yuv420p', '-b:v', '5000k'],
        threads=1,
        logger=None,
        verbose=True
    )
    
    print("✅ SUCCESS: No segfault occurred")
    signal.alarm(0)  # Cancel alarm
    
except KeyboardInterrupt:
    print("⚠️  Interrupted by user")
    sys.exit(130)
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    signal.alarm(0)
    sys.exit(1)
