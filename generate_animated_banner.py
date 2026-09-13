import os
import sys
import math
import numpy as np
import cv2
import imageio_ffmpeg
import subprocess
from PIL import Image

def generate_animated_banner():
    banner_path = r'C:\Users\mukil\Mukil630\github_banner.png'
    output_dir = r'C:\Users\mukil\Mukil630'
    
    print("Loading base banner...")
    base_img = cv2.imread(banner_path)
    if base_img is None:
        raise FileNotFoundError(f"Could not load {banner_path}")
        
    H, W = base_img.shape[:2]
    print(f"Base image: {W}x{H}")
    
    # 60 frames @ 20 fps = 3.0 second seamless loop
    total_frames = 60
    fps = 20
    
    # Coordinates
    red_eye = (408, 151)
    cyan_eye = (486, 144)
    portal_center = (720, 310)
    portal_radius = 235
    
    # Terminal cursor position (at C:\Users\Mukil630> )
    # Let's detect the white block at bottom left
    sub_term = base_img[700:740, 170:220]
    term_cursor_pos = (195, 722)
    
    # Code editor cursor at line 10 build_future()
    code_cursor_pos = (832, 408)
    
    # Floating embers setup
    np.random.seed(1337)
    N_embers = 75
    emb_x = np.random.uniform(W * 0.15, W * 0.85, N_embers)
    emb_y = np.random.uniform(50, H - 50, N_embers)
    emb_speed = np.random.uniform(1.2, 3.2, N_embers)
    emb_size = np.random.choice([1, 2, 3], N_embers, p=[0.65, 0.25, 0.10])
    emb_colors = [
        (40, 40, 255),   # Vibrant red
        (255, 220, 0),   # Cyan
        (30, 180, 255),  # Amber gold
        (255, 255, 255), # White
        (220, 80, 180)   # Violet
    ]
    emb_color_idx = np.random.choice(len(emb_colors), N_embers, p=[0.35, 0.30, 0.20, 0.10, 0.05])
    
    # Heatmap cell regions for live commit twinkling
    # Bottom right heatmap is roughly x: 1070 to 1340, y: 660 to 735
    heatmap_twinkles = []
    for _ in range(12):
        hx = np.random.randint(1075, 1330)
        hy = np.random.randint(665, 730)
        speed = np.random.uniform(0.15, 0.35)
        offset = np.random.uniform(0, math.pi * 2)
        heatmap_twinkles.append((hx, hy, speed, offset))

    frames = []
    print(f"Rendering {total_frames} frames of animated banner...")
    
    for f in range(total_frames):
        t = f / float(total_frames)
        frame = base_img.copy()
        
        # 1. Beast Eyes Pulse & Anamorphic Flares
        # Heartbeat pulse cycle (2 beats per 3 seconds)
        pulse_beat = math.sin(t * math.pi * 4) ** 4 # Sharp rhythmic pulse
        
        # Red eye flare
        r_rad = int(3 + pulse_beat * 5)
        cv2.circle(frame, red_eye, r_rad, (50, 50, 255), -1, cv2.LINE_AA)
        cv2.circle(frame, red_eye, max(1, r_rad - 2), (200, 200, 255), -1, cv2.LINE_AA)
        # Horizontal anamorphic lens streak
        streak_len = int(12 + pulse_beat * 24)
        cv2.line(frame, (red_eye[0] - streak_len, red_eye[1]), 
                        (red_eye[0] + streak_len, red_eye[1]), (30, 30, 255), 1, cv2.LINE_AA)
        
        # Cyan eye flare
        c_rad = int(3 + pulse_beat * 5)
        cv2.circle(frame, cyan_eye, c_rad, (255, 230, 0), -1, cv2.LINE_AA)
        cv2.circle(frame, cyan_eye, max(1, c_rad - 2), (255, 255, 255), -1, cv2.LINE_AA)
        # Cyan streak
        cv2.line(frame, (cyan_eye[0] - streak_len, cyan_eye[1]), 
                        (cyan_eye[0] + streak_len, cyan_eye[1]), (255, 200, 0), 1, cv2.LINE_AA)
                        
        # 2. Rotating Holographic Ring around the Portal
        # Segmented arcs rotating around Mukil
        rot_deg = (f * 6) % 360 # smooth full rotation
        ring_col = (200, 160, 40) # Subtle cyan/slate glow
        for arc_offset in [0, 60, 120, 180, 240, 300]:
            start_a = rot_deg + arc_offset
            cv2.ellipse(frame, portal_center, (portal_radius, portal_radius), 0, start_a, start_a + 35, ring_col, 1, cv2.LINE_AA)
            
        # Outer thin pulse ring
        outer_r = int(portal_radius + 15 + math.sin(t * math.pi * 2) * 5)
        cv2.ellipse(frame, portal_center, (outer_r, outer_r), -rot_deg * 0.5, 0, 40, (14, 165, 233), 1, cv2.LINE_AA)
        cv2.ellipse(frame, portal_center, (outer_r, outer_r), -rot_deg * 0.5 + 180, 0, 40, (14, 165, 233), 1, cv2.LINE_AA)

        # 3. Chrome Shimmer & Light Sweep across "MUKIL 630"
        # Sweep happens between t = 0.20 and t = 0.70
        if 0.20 <= t <= 0.70:
            sweep_prog = (t - 0.20) / 0.50 # 0 to 1
            # X travels from 360 to 1020
            sweep_x = int(360 + sweep_prog * (1020 - 360))
            
            # Diagonal beam across MUKIL 630 (y: 530 to 660)
            text_mask = np.zeros_like(frame)
            cv2.line(text_mask, (sweep_x - 30, 520), (sweep_x + 30, 670), (255, 255, 255), 18)
            cv2.line(text_mask, (sweep_x - 20, 520), (sweep_x + 20, 670), (255, 255, 255), 6)
            
            # Blur the beam for soft flare
            beam_blur = cv2.GaussianBlur(text_mask, (21, 21), 7)
            
            # Restrict flare to the MUKIL 630 text bounding area (y: 530 to 660, x: 340 to 1040)
            text_roi = frame[525:670, 340:1040].astype(np.float32)
            flare_roi = beam_blur[525:670, 340:1040].astype(np.float32) * 0.45
            
            # Additive blend
            frame[525:670, 340:1040] = np.clip(text_roi + flare_roi, 0, 255).astype(np.uint8)
            
            # Star glint on the letter crest at peak
            if 0.45 <= sweep_prog <= 0.55:
                glint_x, glint_y = sweep_x, 565
                cv2.drawMarker(frame, (glint_x, glint_y), (255, 255, 255), cv2.MARKER_STAR, 14, 1, cv2.LINE_AA)

        # 4. Blinking Terminal Cursor (C:\Users\Mukil630> █)
        # Blinks every 10 frames (~0.5s)
        cursor_on = (f // 10) % 2 == 0
        if cursor_on:
            cv2.rectangle(frame, (term_cursor_pos[0], term_cursor_pos[1] - 12), 
                                 (term_cursor_pos[0] + 8, term_cursor_pos[1] + 2), (240, 240, 240), -1)
        else:
            # Erase cursor (paint background dark)
            cv2.rectangle(frame, (term_cursor_pos[0], term_cursor_pos[1] - 12), 
                                 (term_cursor_pos[0] + 8, term_cursor_pos[1] + 2), (8, 12, 20), -1)

        # 5. Blinking Code Cursor (in main.py)
        if (f // 8) % 2 == 0:
            cv2.line(frame, (code_cursor_pos[0], code_cursor_pos[1] - 10),
                            (code_cursor_pos[0], code_cursor_pos[1] + 4), (255, 255, 255), 2)

        # 6. Heatmap Live Twinkle
        for hx, hy, spd, off in heatmap_twinkles:
            tw_val = math.sin(f * spd + off)
            if tw_val > 0.3:
                tw_col = (40, 40, 240) if (hx + hy) % 2 == 0 else (100, 230, 100)
                cv2.circle(frame, (hx, hy), 2, tw_col, -1)

        # 7. Floating Atmospheric Embers
        for i in range(N_embers):
            ey = int((emb_y[i] - f * emb_speed[i] * 1.5) % H)
            ex = int((emb_x[i] + math.sin(f * 0.12 + i) * 12) % W)
            sz = emb_size[i]
            col = emb_colors[emb_color_idx[i]]
            
            # Soft glowing ember
            cv2.circle(frame, (ex, ey), sz, col, -1)

        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
    print("Writing MP4 video...")
    mp4_path = os.path.join(output_dir, 'github_banner.mp4')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(mp4_path, fourcc, fps, (W, H))
    for fr in frames:
        writer.write(cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
    writer.release()
    print(f"MP4 saved: {mp4_path} ({os.path.getsize(mp4_path) / (1024*1024):.2f} MB)")
    
    print("Generating ultra-optimized GIF with FFmpeg...")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    gif_path = os.path.join(output_dir, 'github_banner.gif')
    pal_path = os.path.join(output_dir, 'banner_palette.png')
    
    # Scale to width 1000px for lightning-fast loading on GitHub while keeping HD sharpness
    target_w = 1000
    target_h = int(H * (target_w / W))
    
    cmd_pal = [
        ffmpeg_exe, '-y', '-i', mp4_path,
        '-vf', f'fps={fps},scale={target_w}:{target_h}:flags=lanczos,palettegen=max_colors=128:stats_mode=diff',
        pal_path
    ]
    subprocess.run(cmd_pal, check=True)
    
    cmd_gif = [
        ffmpeg_exe, '-y', '-i', mp4_path, '-i', pal_path,
        '-lavfi', f'fps={fps},scale={target_w}:{target_h}:flags=lanczos [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=3',
        gif_path
    ]
    subprocess.run(cmd_gif, check=True)
    
    if os.path.exists(pal_path):
        os.remove(pal_path)
        
    print(f"ANIMATED BANNER GIF SAVED: {gif_path} ({os.path.getsize(gif_path) / (1024*1024):.2f} MB)")

if __name__ == '__main__':
    generate_animated_banner()
