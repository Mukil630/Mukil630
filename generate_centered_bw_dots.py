import os
import sys
import math
import numpy as np
import cv2
import imageio_ffmpeg
import subprocess

def create_perfect_centered_bw_dots():
    input_path = r'C:\Users\mukil\Mukil630\assets\mukil_input.jpg'
    mask_path = r'C:\Users\mukil\Mukil630\assets\mukil_person_mask.png'
    output_dir = r'C:\Users\mukil\Mukil630\assets'
    
    print("Loading image & mask...")
    img = cv2.imread(input_path)
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    H_orig, W_orig = img.shape[:2]
    
    # Calculate bounding box of Mukil
    ys, xs = np.where(mask > 128)
    min_y, max_y = int(np.min(ys)), int(np.max(ys))
    min_x, max_x = int(np.min(xs)), int(np.max(xs))
    
    cx = (min_x + max_x) / 2.0
    cy = (min_y + max_y) / 2.0
    box_size = int(max(max_y - min_y, max_x - min_x) * 1.05)
    
    # Square crop centered on Mukil
    x1 = int(cx - box_size / 2)
    y1 = int(cy - box_size / 2)
    x2 = x1 + box_size
    y2 = y1 + box_size
    
    # Pad if out of bounds
    pad_top = max(0, -y1)
    pad_bottom = max(0, y2 - H_orig)
    pad_left = max(0, -x1)
    pad_right = max(0, x2 - W_orig)
    
    img_padded = cv2.copyMakeBorder(img, pad_top, pad_bottom, pad_left, pad_right, cv2.BORDER_CONSTANT, value=[8, 12, 20])
    mask_padded = cv2.copyMakeBorder(mask, pad_top, pad_bottom, pad_left, pad_right, cv2.BORDER_CONSTANT, value=[0])
    
    crop_img = img_padded[y1 + pad_top : y2 + pad_top, x1 + pad_left : x2 + pad_left]
    crop_mask = mask_padded[y1 + pad_top : y2 + pad_top, x1 + pad_left : x2 + pad_left]
    
    # Target resolution: 480x480
    W, H = 480, 480
    crop_img = cv2.resize(crop_img, (W, H), interpolation=cv2.INTER_AREA)
    crop_mask = cv2.resize(crop_mask, (W, H), interpolation=cv2.INTER_NEAREST)
    gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
    
    # Grid sampling (step = 3)
    step = 3
    dots_y, dots_x = np.mgrid[0:H:step, 0:W:step]
    all_y = dots_y.ravel()
    all_x = dots_x.ravel()
    
    mukil_pts = crop_mask[all_y, all_x] > 128
    ty = all_y[mukil_pts].astype(np.float32)
    tx = all_x[mukil_pts].astype(np.float32)
    vals = gray[all_y[mukil_pts], all_x[mukil_pts]].astype(np.float32)
    
    N = len(tx)
    print(f"Total centered B&W dots: {N:,}")
    
    # Particles state
    px = tx.copy()
    py = ty.copy()
    vx = np.zeros(N, dtype=np.float32)
    vy = np.zeros(N, dtype=np.float32)
    
    # Contrast adjustment for clean crisp B&W
    norm_vals = np.clip((vals - 15) / 210.0, 0.0, 1.0)
    gray_shades = (120 + norm_vals * 135).astype(np.uint8)
    radii = np.where(norm_vals > 0.45, 2, 1).astype(np.int32)
    
    total_frames = 84
    fps = 16
    
    # Cursor path (sweeps smoothly over Mukil's face and jacket)
    cursor_path = []
    for f in range(total_frames):
        t = f / float(total_frames)
        if t < 0.15:
            prog = t / 0.15
            mx = -40 + prog * 240
            my = 380 - prog * 60
        elif t < 0.50:
            prog = (t - 0.15) / 0.35
            mx = 200 + math.sin(prog * math.pi) * 60
            my = 320 - prog * 190
        elif t < 0.80:
            prog = (t - 0.50) / 0.30
            mx = 240 + prog * 200
            my = 130 + math.sin(prog * math.pi) * 40
        else:
            prog = (t - 0.80) / 0.20
            mx = 440 + prog * 100
            my = 170
        cursor_path.append((mx, my))
        
    frames = []
    bg_color = np.array([8, 12, 20], dtype=np.uint8)
    
    sub_steps = 3
    dt = 1.0 / sub_steps
    repel_rad = 62.0
    
    print("Simulating physics across 84 frames...")
    for f in range(total_frames):
        mx, my = cursor_path[f]
        
        for _ in range(sub_steps):
            dx = mx - px
            dy = my - py
            dist = np.sqrt(dx * dx + dy * dy)
            
            in_range = (dist < repel_rad) & (dist > 1.0)
            if in_range.any():
                force = (repel_rad - dist[in_range]) / repel_rad
                angle = np.arctan2(dy[in_range], dx[in_range])
                vx[in_range] -= np.cos(angle) * force * 5.5 * dt
                vy[in_range] -= np.sin(angle) * force * 5.5 * dt
                
            # Spring return
            vx += (tx - px) * 0.11 * dt
            vy += (ty - py) * 0.11 * dt
            
            # Damping
            vx *= (0.86 ** dt)
            vy *= (0.86 ** dt)
            
            px += vx * dt
            py += vy * dt
            
        canvas = np.zeros((H, W, 3), dtype=np.uint8)
        canvas[:] = bg_color
        
        ix = np.clip(np.round(px).astype(np.int32), 0, W - 1)
        iy = np.clip(np.round(py).astype(np.int32), 0, H - 1)
        
        disp = np.sqrt((px - tx)**2 + (py - ty)**2)
        
        # Render dots
        for i in range(N):
            xi = ix[i]
            yi = iy[i]
            r = radii[i]
            if disp[i] > 3.0:
                # Displaced dots light up in glowing white-cyan
                cv2.circle(canvas, (xi, yi), r, (255, 245, 220), -1)
            else:
                c = int(gray_shades[i])
                cv2.circle(canvas, (xi, yi), r, (c, c, c), -1)
                
        # Draw glowing pointer
        if 0 <= mx < W and 0 <= my < H:
            cx_i = int(mx)
            cy_i = int(my)
            cv2.circle(canvas, (cx_i, cy_i), int(repel_rad), (14, 165, 233), 1, cv2.LINE_AA)
            cv2.circle(canvas, (cx_i, cy_i), 4, (0, 240, 255), -1, cv2.LINE_AA)
            pts = np.array([[cx_i, cy_i], [cx_i + 14, cy_i + 5], [cx_i + 5, cy_i + 14]], np.int32)
            cv2.polylines(canvas, [pts], True, (255, 255, 255), 1, cv2.LINE_AA)
            
        # Tech brackets
        pad = 12
        blen = 18
        col_hud = (233, 165, 14)
        for cx_c, cy_c, sx, sy in [(pad, pad, 1, 1), (W - pad, pad, -1, 1), 
                                    (pad, H - pad, 1, -1), (W - pad, H - pad, -1, -1)]:
            cv2.line(canvas, (cx_c, cy_c), (cx_c + sx * blen, cy_c), col_hud, 1)
            cv2.line(canvas, (cx_c, cy_c), (cx_c, cy_c + sy * blen), col_hud, 1)
            
        cv2.putText(canvas, "INTERACTIVE B&W MATRIX // CURSOR REACTIVE", (pad + 4, pad + 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.32, (180, 210, 240), 1, cv2.LINE_AA)
        cv2.putText(canvas, "MUKILARASU S", (pad + 4, H - pad - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(canvas, "// MOVE CURSOR TO SCATTER", (pad + 104, H - pad - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.32, (14, 165, 233), 1, cv2.LINE_AA)
                    
        frames.append(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        
    print("Writing MP4...")
    mp4_path = os.path.join(output_dir, 'centered_bw_master.mp4')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(mp4_path, fourcc, fps, (W, H))
    for fr in frames:
        writer.write(cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
    writer.release()
    
    print("Generating ultra-crisp GIF with palette...")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    gif_out = os.path.join(output_dir, 'mukil_particle_profile.gif')
    pal_tmp = os.path.join(output_dir, 'palette_centered.png')
    
    cmd_pal = [
        ffmpeg_exe, '-y', '-i', mp4_path,
        '-vf', f'fps={fps},scale={W}:{H}:flags=lanczos,palettegen=max_colors=64:stats_mode=diff',
        pal_tmp
    ]
    subprocess.run(cmd_pal, check=True)
    
    cmd_gif = [
        ffmpeg_exe, '-y', '-i', mp4_path, '-i', pal_tmp,
        '-lavfi', f'fps={fps},scale={W}:{H}:flags=lanczos [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=3',
        gif_out
    ]
    subprocess.run(cmd_gif, check=True)
    
    if os.path.exists(pal_tmp):
        os.remove(pal_tmp)
    if os.path.exists(mp4_path):
        os.remove(mp4_path)
        
    print(f"PERFECT CENTERED B&W GIF CREATED: {gif_out} ({os.path.getsize(gif_out) / (1024*1024):.2f} MB)")

if __name__ == '__main__':
    create_perfect_centered_bw_dots()
