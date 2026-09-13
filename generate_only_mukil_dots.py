import os
import sys
import math
import numpy as np
import cv2
import imageio_ffmpeg
import subprocess

def create_only_mukil_dots_animation():
    input_path = r'C:\Users\mukil\Mukil630\assets\mukil_input.jpg'
    mask_path = r'C:\Users\mukil\Mukil630\assets\mukil_person_mask.png'
    output_dir = r'C:\Users\mukil\Mukil630\assets'
    
    print("Loading image and person mask...")
    raw_img = cv2.imread(input_path)
    raw_mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    
    W, H = 480, 480
    img = cv2.resize(raw_img, (W, H), interpolation=cv2.INTER_AREA)
    mask = cv2.resize(raw_mask, (W, H), interpolation=cv2.INTER_NEAREST)
    
    # Grid step = 2 (fine dot density)
    step = 2
    dots_y, dots_x = np.mgrid[0:H:step, 0:W:step]
    all_y = dots_y.ravel()
    all_x = dots_x.ravel()
    
    # Filter ONLY Mukil's pixels using the person mask!
    mukil_mask = mask[all_y, all_x] > 128
    ty = all_y[mukil_mask]
    tx = all_x[mukil_mask]
    
    # Extract colors from Mukil's pixels
    colors = img[ty, tx].astype(np.float32)
    brightness = 0.114 * colors[:, 0] + 0.587 * colors[:, 1] + 0.299 * colors[:, 2]
    
    # Boost color saturation and rim-light glow for an ultra-attractive look
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.30, 0, 255) # 30% more color pop
    vibrant_img = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
    vibrant_colors = vibrant_img[ty, tx]
    
    N = len(ty)
    print(f"Total dots of ONLY Mukil: {N:,}")
    
    # Dispersed starting positions (Cosmic Swarm centered on Mukil's torso)
    np.random.seed(42)
    cx, cy = float(np.mean(tx)), float(np.mean(ty)) # Center of Mukil's body
    
    angles = np.random.uniform(0, 2 * np.pi, N)
    radii = np.random.exponential(scale=150, size=N) + 60
    radii = np.clip(radii, 40, 420)
    
    # Swirl trajectory
    start_x = cx + radii * np.cos(angles + radii * 0.02) + np.random.normal(0, 15, N)
    start_y = cy + radii * np.sin(angles + radii * 0.02) + np.random.normal(0, 15, N)
    
    # Per-dot stagger so face and head snap first, followed by suit
    dist_from_head = np.sqrt((tx - cx)**2 + (ty - (cy - 60))**2)
    stagger = (dist_from_head / 280.0) * 0.22 + np.random.uniform(-0.05, 0.05, N)
    
    # Ambient floating particles in the dark space around him
    N_amb = 60
    amb_x = np.random.uniform(20, W - 20, N_amb)
    amb_y = np.random.uniform(20, H - 20, N_amb)
    amb_spd = np.random.uniform(0.6, 1.8, N_amb)
    
    total_frames = 84
    fps = 16
    
    frames = []
    print(f"Rendering {total_frames} frames of ONLY Mukil in dots...")
    
    bg_color = np.array([8, 12, 20], dtype=np.uint8) # Deep cyber void
    
    for f in range(total_frames):
        t = f / float(total_frames)
        
        # Timeline:
        # 0.00 - 0.28 (frames 0-23): Swirling dots converge to form Mukil
        # 0.28 - 0.74 (frames 23-62): ONLY MUKIL holds in pure dot matrix with wave shimmer & breathing
        # 0.74 - 1.00 (frames 62-84): Dots disperse into vortex (seamless loop)
        
        if t < 0.28:
            gt = t / 0.28
            prog = 1.0 - (1.0 - gt) ** 3 # Cubic ease out
            swirl = (1.0 - gt) * 1.4
            wave_active = False
        elif t < 0.74:
            prog = 1.0
            swirl = 0.0
            wave_active = True
            wave_prog = (t - 0.28) / 0.46 # 0.0 to 1.0
        else:
            gt = (t - 0.74) / 0.26
            prog = 1.0 - (gt ** 2.2) # Smooth ease out
            swirl = -gt * 0.9
            wave_active = False
            
        # Rotate starting positions during swirl
        if abs(swirl) > 1e-4:
            cos_s = math.cos(swirl)
            sin_s = math.sin(swirl)
            cur_sx = cx + (start_x - cx) * cos_s - (start_y - cy) * sin_s
            cur_sy = cy + (start_x - cx) * sin_s + (start_y - cy) * cos_s
        else:
            cur_sx = start_x
            cur_sy = start_y
            
        # Individual particle progress
        p_prog = np.clip(prog - stagger * (1.0 - prog) * prog * 3.5, 0.0, 1.0)
        
        # Current dot coordinates
        cur_x = cur_sx * (1.0 - p_prog) + tx * p_prog
        cur_y = cur_sy * (1.0 - p_prog) + ty * p_prog
        
        # Base colors
        cur_bgr = vibrant_colors.copy()
        
        # When fully formed, apply subtle living holographic shimmer wave & micro-breath
        if wave_active:
            # Diagonal energy pulse
            wave_pos = wave_prog * (W + H + 80) - 40
            dot_dist_wave = np.abs((tx + ty) - wave_pos)
            wave_infl = np.exp(-(dot_dist_wave ** 2) / (2 * (38 ** 2)))
            
            # Subtle vertical breathing oscillation
            breath = math.sin(f * 0.22) * 0.9
            cur_y += breath
            
            # Shimmer illumination along wave front
            boost = (wave_infl[:, None] * 75).astype(np.float32)
            cur_bgr = np.clip(cur_bgr + boost, 0, 255)
        elif t < 0.28 or t >= 0.74:
            # Extra brightness during swirl
            cur_bgr = np.clip(cur_bgr * 1.2, 0, 255)
            
        # Create pure clean dark void canvas (NO BACKGROUND IMAGE)
        canvas = np.zeros((H, W, 3), dtype=np.uint8)
        canvas[:] = bg_color
        
        # Subtle ambient quantum embers floating in background
        for a in range(N_amb):
            ay = int((amb_y[a] - f * amb_spd[a] * 1.2) % H)
            ax = int((amb_x[a] + math.sin(f * 0.1 + a) * 8) % W)
            col_spark = (255, 200, 80) if a % 2 == 0 else (0, 220, 255)
            cv2.circle(canvas, (ax, ay), 1, col_spark, -1)
            
        # Coords
        ix = np.clip(np.round(cur_x).astype(np.int32), 0, W - 1)
        iy = np.clip(np.round(cur_y).astype(np.int32), 0, H - 1)
        
        # Render Mukil's dots
        canvas[iy, ix] = cur_bgr.astype(np.uint8)
        
        # Give brightness-weighted dots a 1px cross to give rich volume to facial features and rim-light
        bright_mask = brightness > 50
        if bright_mask.any():
            b_ix = ix[bright_mask]
            b_iy = iy[bright_mask]
            b_cols = (cur_bgr[bright_mask] * 0.70).astype(np.uint8)
            canvas[np.clip(b_iy + 1, 0, H - 1), b_ix] = b_cols
            canvas[np.clip(b_iy - 1, 0, H - 1), b_ix] = b_cols
            canvas[b_iy, np.clip(b_ix + 1, 0, W - 1)] = b_cols
            canvas[b_iy, np.clip(b_ix - 1, 0, W - 1)] = b_cols
            
        # Cybernetic HUD Framing
        pad = 14
        blen = 20
        hud_col = (233, 165, 14) # Electric sky blue (0EA5E9)
        for cx_c, cy_c, sx, sy in [(pad, pad, 1, 1), (W - pad, pad, -1, 1), 
                                    (pad, H - pad, 1, -1), (W - pad, H - pad, -1, -1)]:
            cv2.line(canvas, (cx_c, cy_c), (cx_c + sx * blen, cy_c), hud_col, 1)
            cv2.line(canvas, (cx_c, cy_c), (cx_c, cy_c + sy * blen), hud_col, 1)
            
        # Clean Top Label
        cv2.putText(canvas, "NEURAL DOT MATRIX // ONLY MUKILARASU", (pad + 4, pad + 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.32, (160, 210, 255), 1, cv2.LINE_AA)
                    
        # Status Label
        if wave_active:
            status_text = "STATUS: SYNTHESIZED [33K NODES]"
            s_col = (0, 240, 180)
        else:
            status_text = "CONVERGING MATRIX..."
            s_col = (0, 200, 255)
        cv2.putText(canvas, status_text, (W - pad - 180, pad + 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.30, s_col, 1, cv2.LINE_AA)
                    
        # Bottom Identity Bar
        cv2.putText(canvas, "MUKILARASU S", (pad + 4, H - pad - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(canvas, "// AI SYSTEMS ARCHITECT", (pad + 106, H - pad - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.32, (14, 165, 233), 1, cv2.LINE_AA)
                    
        frames.append(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        
    print("Writing MP4 master...")
    mp4_master = os.path.join(output_dir, 'only_mukil_master.mp4')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(mp4_master, fourcc, fps, (W, H))
    for fr in frames:
        writer.write(cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
    writer.release()
    
    print("Generating ultra-optimized GIF with ffmpeg palette...")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    gif_out = os.path.join(output_dir, 'mukil_particle_profile.gif')
    pal_tmp = os.path.join(output_dir, 'mukil_pal.png')
    
    # 440x440, 16fps, 96 colors for smooth playback and low bandwidth
    cmd_pal = [
        ffmpeg_exe, '-y', '-i', mp4_master,
        '-vf', f'fps={fps},scale=440:440:flags=lanczos,palettegen=max_colors=96:stats_mode=diff',
        pal_tmp
    ]
    subprocess.run(cmd_pal, check=True)
    
    cmd_gif = [
        ffmpeg_exe, '-y', '-i', mp4_master, '-i', pal_tmp,
        '-lavfi', f'fps={fps},scale=440:440:flags=lanczos [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=3',
        gif_out
    ]
    subprocess.run(cmd_gif, check=True)
    
    if os.path.exists(pal_tmp):
        os.remove(pal_tmp)
    if os.path.exists(mp4_master):
        os.remove(mp4_master)
        
    sz_mb = os.path.getsize(gif_out) / (1024*1024)
    print(f"ONLY MUKIL DOTS GIF CREATED: {gif_out} ({sz_mb:.2f} MB)")

if __name__ == '__main__':
    create_only_mukil_dots_animation()
