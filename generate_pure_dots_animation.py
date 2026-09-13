import os
import sys
import math
import numpy as np
import cv2
import imageio_ffmpeg
import subprocess

def create_pure_dots_animation():
    input_path = r'C:\Users\mukil\Mukil630\assets\mukil_input.jpg'
    output_dir = r'C:\Users\mukil\Mukil630\assets'
    
    print("Loading image...")
    raw_img = cv2.imread(input_path)
    W, H = 480, 480
    img = cv2.resize(raw_img, (W, H), interpolation=cv2.INTER_AREA)
    
    # Grid step = 2 (gives 240x240 grid = ~57,600 points)
    step = 2
    dots_y, dots_x = np.mgrid[0:H:step, 0:W:step]
    ty = dots_y.ravel()
    tx = dots_x.ravel()
    
    # Filter out pure void/pitch black if any, keep all colored dots
    colors = img[ty, tx].astype(np.float32)
    brightness = 0.114 * colors[:, 0] + 0.587 * colors[:, 1] + 0.299 * colors[:, 2]
    
    # Boost contrast and saturation slightly for punchy dot matrix look
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.25, 0, 255) # Increase saturation for glowing colors
    vibrant_img = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
    vibrant_colors = vibrant_img[ty, tx]
    
    N = len(ty)
    print(f"Total dots in matrix: {N:,}")
    
    # Initial dispersed positions (Vortex + Explosion)
    np.random.seed(42)
    cx, cy = W / 2.0, H / 2.0
    
    angles = np.random.uniform(0, 2 * np.pi, N)
    radii = np.random.exponential(scale=160, size=N) + 50
    radii = np.clip(radii, 30, 450)
    
    start_x = cx + radii * np.cos(angles + radii * 0.015) + np.random.normal(0, 15, N)
    start_y = cy + radii * np.sin(angles + radii * 0.015) + np.random.normal(0, 15, N)
    
    # Per-particle arrival stagger
    dist = np.sqrt((tx - cx)**2 + (ty - cy)**2)
    stagger = (dist / 300.0) * 0.25 + np.random.uniform(-0.06, 0.06, N)
    
    total_frames = 90
    fps = 18
    
    frames = []
    print(f"Rendering {total_frames} frames of pure dot matrix animation...")
    
    bg_color = np.array([8, 12, 20], dtype=np.uint8) # Deep cyber dark
    
    for f in range(total_frames):
        t = f / float(total_frames)
        
        # Phases:
        # 0.00 - 0.30 (frames 0-27): Swirling dots assemble into face
        # 0.30 - 0.75 (frames 27-67): Pure Dot Matrix portrait held, with holographic energy wave & gentle breathing
        # 0.75 - 1.00 (frames 67-90): Dots disperse back to vortex (seamless loop)
        
        if t < 0.30:
            gt = t / 0.30
            # Ease out cubic into place
            prog = 1.0 - (1.0 - gt) ** 3
            swirl = (1.0 - gt) * 1.5
            wave_active = False
        elif t < 0.75:
            prog = 1.0
            swirl = 0.0
            wave_active = True
            wave_prog = (t - 0.30) / 0.45 # 0.0 to 1.0
        else:
            gt = (t - 0.75) / 0.25
            # Ease in quad out
            prog = 1.0 - (gt ** 2.5)
            swirl = -gt * 1.0
            wave_active = False
            
        # Rotate start positions during swirl
        if abs(swirl) > 1e-4:
            cos_s = math.cos(swirl)
            sin_s = math.sin(swirl)
            cur_sx = cx + (start_x - cx) * cos_s - (start_y - cy) * sin_s
            cur_sy = cy + (start_x - cx) * sin_s + (start_y - cy) * cos_s
        else:
            cur_sx = start_x
            cur_sy = start_y
            
        # Particle progress
        p_prog = np.clip(prog - stagger * (1.0 - prog) * prog * 3.5, 0.0, 1.0)
        
        # Position interpolation
        cur_x = cur_sx * (1.0 - p_prog) + tx * p_prog
        cur_y = cur_sy * (1.0 - p_prog) + ty * p_prog
        
        # Dot colors:
        cur_bgr = vibrant_colors.copy()
        
        # When wave is active, add holographic shimmer / wave pulse
        if wave_active:
            # Wave front traveling diagonally from top-left to bottom-right
            wave_pos = wave_prog * (W + H + 100) - 50
            dot_dist_wave = np.abs((tx + ty) - wave_pos)
            wave_influence = np.exp(-(dot_dist_wave ** 2) / (2 * (45 ** 2))) # Gaussian beam
            
            # Subtle breathing ripple (micro-displacement)
            ripple_y = np.sin(tx * 0.08 + f * 0.2) * 0.8
            cur_y += ripple_y
            
            # Wave illumination: brighten and add slight cyan tint along wave front
            boost = (wave_influence[:, None] * 80).astype(np.float32)
            cur_bgr = np.clip(cur_bgr + boost, 0, 255)
        elif t < 0.30 or t >= 0.75:
            # During dispersion, brighten dots for glowing spark effect
            cur_bgr = np.clip(cur_bgr * 1.15, 0, 255)
            
        # Render canvas
        canvas = np.zeros((H, W, 3), dtype=np.uint8)
        canvas[:] = bg_color
        
        # Convert coords to int
        ix = np.clip(np.round(cur_x).astype(np.int32), 0, W - 1)
        iy = np.clip(np.round(cur_y).astype(np.int32), 0, H - 1)
        
        # Draw dots onto canvas
        # Center pixel
        canvas[iy, ix] = cur_bgr.astype(np.uint8)
        
        # Draw 1px cross for dots with brightness > 40 to give them volume/circular look
        bright_mask = brightness > 40
        if bright_mask.any():
            b_ix = ix[bright_mask]
            b_iy = iy[bright_mask]
            b_cols = (cur_bgr[bright_mask] * 0.75).astype(np.uint8)
            
            canvas[np.clip(b_iy + 1, 0, H - 1), b_ix] = b_cols
            canvas[np.clip(b_iy - 1, 0, H - 1), b_ix] = b_cols
            canvas[b_iy, np.clip(b_ix + 1, 0, W - 1)] = b_cols
            canvas[b_iy, np.clip(b_ix - 1, 0, W - 1)] = b_cols
            
        # Draw tech corner brackets & labels
        pad = 14
        blen = 22
        hud_col = (233, 165, 14) # 0EA5E9
        # Corner lines
        for cx_c, cy_c, sx, sy in [(pad, pad, 1, 1), (W - pad, pad, -1, 1), 
                                    (pad, H - pad, 1, -1), (W - pad, H - pad, -1, -1)]:
            cv2.line(canvas, (cx_c, cy_c), (cx_c + sx * blen, cy_c), hud_col, 1)
            cv2.line(canvas, (cx_c, cy_c), (cx_c, cy_c + sy * blen), hud_col, 1)
            
        # Top Left Tech Tag
        cv2.putText(canvas, "NEURAL DOT MATRIX // 57.6K NODES", (pad + 4, pad + 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.32, (160, 200, 240), 1, cv2.LINE_AA)
                    
        # Top Right Tag
        if wave_active:
            status_tag = "ACTIVE DIGITAL AVATAR"
            tag_col = (0, 230, 200)
        else:
            status_tag = "SYNTHESIZING MATRIX"
            tag_col = (0, 180, 255)
        cv2.putText(canvas, status_tag, (W - pad - 145, pad + 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.30, tag_col, 1, cv2.LINE_AA)
                    
        # Bottom Name Bar
        cv2.putText(canvas, "MUKILARASU S", (pad + 4, H - pad - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(canvas, "// AI SYSTEMS ARCHITECT", (pad + 106, H - pad - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.32, (14, 165, 233), 1, cv2.LINE_AA)
                    
        frames.append(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        
    print("Writing MP4 master...")
    mp4_path = os.path.join(output_dir, 'pure_dots_master.mp4')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(mp4_path, fourcc, fps, (W, H))
    for fr in frames:
        writer.write(cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
    writer.release()
    
    print("Generating optimized crystal GIF...")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    gif_out = os.path.join(output_dir, 'mukil_particle_profile.gif')
    palette_tmp = os.path.join(output_dir, 'dots_palette.png')
    
    cmd_pal = [
        ffmpeg_exe, '-y', '-i', mp4_path,
        '-vf', f'fps={fps},scale={W}:{H}:flags=lanczos,palettegen=max_colors=128:stats_mode=diff',
        palette_tmp
    ]
    subprocess.run(cmd_pal, check=True)
    
    cmd_gif = [
        ffmpeg_exe, '-y', '-i', mp4_path, '-i', palette_tmp,
        '-lavfi', f'fps={fps},scale={W}:{H}:flags=lanczos [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=3',
        gif_out
    ]
    subprocess.run(cmd_gif, check=True)
    
    if os.path.exists(palette_tmp):
        os.remove(palette_tmp)
        
    sz_mb = os.path.getsize(gif_out) / (1024*1024)
    print(f"SUCCESS! Pure dots animation generated: {gif_out} ({sz_mb:.2f} MB)")

if __name__ == '__main__':
    create_pure_dots_animation()
