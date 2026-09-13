import os
import sys
import math
import numpy as np
import cv2
import imageio_ffmpeg
import subprocess

def create_bw_cursor_dots_animation():
    input_path = r'C:\Users\mukil\Mukil630\assets\mukil_input.jpg'
    mask_path = r'C:\Users\mukil\Mukil630\assets\mukil_person_mask.png'
    output_dir = r'C:\Users\mukil\Mukil630\assets'
    
    print("Loading image & person mask for B&W cursor simulation...")
    raw_img = cv2.imread(input_path)
    raw_mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    
    W, H = 460, 460
    img = cv2.resize(raw_img, (W, H), interpolation=cv2.INTER_AREA)
    mask = cv2.resize(raw_mask, (W, H), interpolation=cv2.INTER_NEAREST)
    
    # Grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    step = 3
    dots_y, dots_x = np.mgrid[0:H:step, 0:W:step]
    all_y = dots_y.ravel()
    all_x = dots_x.ravel()
    
    # Filter ONLY Mukil's pixels
    mukil_mask = mask[all_y, all_x] > 128
    ty = all_y[mukil_mask].astype(np.float32)
    tx = all_x[mukil_mask].astype(np.float32)
    
    vals = gray[all_y[mukil_mask], all_x[mukil_mask]].astype(np.float32)
    
    N = len(tx)
    print(f"Total B&W dots of Mukil: {N:,}")
    
    # Current positions and velocities
    px = tx.copy()
    py = ty.copy()
    vx = np.zeros(N, dtype=np.float32)
    vy = np.zeros(N, dtype=np.float32)
    
    # Radius & brightness for each dot
    # Contrast stretch for crisp black & white appearance
    vals_norm = np.clip((vals - 20) / 200.0, 0.0, 1.0)
    dot_radius = (1.0 + vals_norm * 1.5).astype(np.float32)
    # Brightness in B&W (pure grayscale: 140 to 255)
    gray_shades = (130 + vals_norm * 125).astype(np.uint8)
    
    # Cursor trajectory path (curves across Mukil's torso, hand, chin, and eyes)
    total_frames = 90
    fps = 18
    
    # Path waypoints: [t, x, y]
    # Smooth spline/bezier cursor movement
    cursor_positions = []
    for f in range(total_frames):
        t = f / float(total_frames)
        # Mouse cursor sweeps in a smooth S-curve across Mukil's face and jacket
        # 0.0 to 0.15: offscreen to hand
        # 0.15 to 0.45: across hand up to chin and lips
        # 0.45 to 0.70: across cheek, eyes, and hair
        # 0.70 to 0.90: moves to the right edge and exits
        # 0.90 to 1.00: rests off-screen while particles settle
        
        if t < 0.15:
            # Entering from left towards chest/hand
            prog = t / 0.15
            mx = -50 + prog * 260
            my = 380 - prog * 50
        elif t < 0.50:
            # Upwards across hand, chin, and beard
            prog = (t - 0.15) / 0.35
            mx = 210 + math.sin(prog * math.pi) * 35
            my = 330 - prog * 180
        elif t < 0.80:
            # Across eyes, temple, and hair towards right
            prog = (t - 0.50) / 0.30
            mx = 230 + prog * 200
            my = 150 + math.sin(prog * math.pi) * 40
        else:
            # Offscreen right
            prog = (t - 0.80) / 0.20
            mx = 430 + prog * 100
            my = 190
            
        cursor_positions.append((mx, my))

    frames = []
    print("Simulating cursor physics and rendering frames...")
    
    bg_color = np.array([8, 12, 20], dtype=np.uint8) # Deep void
    
    # Simulation sub-steps for smooth spring physics
    sub_steps = 3
    dt = 1.0 / sub_steps
    repel_radius = 55.0
    
    for f in range(total_frames):
        mx, my = cursor_positions[f]
        
        for _ in range(sub_steps):
            # Distance from cursor
            dx = mx - px
            dy = my - py
            dist = np.sqrt(dx * dx + dy * dy)
            
            # Repulsion force
            in_range = (dist < repel_radius) & (dist > 1.0)
            if in_range.any():
                force = (repel_radius - dist[in_range]) / repel_radius
                angle = np.arctan2(dy[in_range], dx[in_range])
                vx[in_range] -= np.cos(angle) * force * 5.0 * dt
                vy[in_range] -= np.sin(angle) * force * 5.0 * dt
                
            # Spring force back to origin (tx, ty)
            spring_x = tx - px
            spring_y = ty - py
            vx += spring_x * 0.12 * dt
            vy += spring_y * 0.12 * dt
            
            # Damping
            vx *= (0.86 ** dt)
            vy *= (0.86 ** dt)
            
            # Position update
            px += vx * dt
            py += vy * dt
            
        # Render canvas
        canvas = np.zeros((H, W, 3), dtype=np.uint8)
        canvas[:] = bg_color
        
        # Round coords
        ix = np.clip(np.round(px).astype(np.int32), 0, W - 1)
        iy = np.clip(np.round(py).astype(np.int32), 0, H - 1)
        
        # Draw B&W dots
        # Displacement distance for extra glow on displaced dots
        disp = np.sqrt((px - tx)**2 + (py - ty)**2)
        
        # Base B&W colors
        shades = gray_shades.copy()
        shades = np.clip(shades.astype(np.float32) + disp * 12.0, 0, 255).astype(np.uint8)
        
        # Draw dots
        for i in range(N):
            x_i = ix[i]
            y_i = iy[i]
            c_val = int(shades[i])
            r_val = 1 if dot_radius[i] < 1.8 else 2
            if disp[i] > 3.0:
                # Displaced dot glows electric cyan-silver
                cv2.circle(canvas, (x_i, y_i), r_val, (255, 240, 200), -1) # bright silver
            else:
                cv2.circle(canvas, (x_i, y_i), r_val, (c_val, c_val, c_val), -1)
                
        # Draw the virtual cursor pointer if on screen
        if 0 <= mx < W and 0 <= my < H:
            cx_int = int(mx)
            cy_int = int(my)
            # Glowing cursor circle
            cv2.circle(canvas, (cx_int, cy_int), int(repel_radius), (14, 165, 233), 1, cv2.LINE_AA)
            cv2.circle(canvas, (cx_int, cy_int), 4, (0, 240, 255), -1, cv2.LINE_AA)
            # Cursor arrow pointer
            pts = np.array([[cx_int, cy_int], [cx_int + 14, cy_int + 6], [cx_int + 6, cy_int + 14]], np.int32)
            cv2.polylines(canvas, [pts], True, (255, 255, 255), 1, cv2.LINE_AA)
            
        # Clean HUD elements
        pad = 12
        cv2.putText(canvas, "INTERACTIVE B&W DOT MATRIX // CURSOR REACTIVE", (pad + 4, pad + 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.32, (180, 200, 220), 1, cv2.LINE_AA)
                    
        cv2.putText(canvas, "MUKILARASU S", (pad + 4, H - pad - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(canvas, "// MOVE CURSOR TO INTERACT", (pad + 104, H - pad - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.32, (14, 165, 233), 1, cv2.LINE_AA)
                    
        frames.append(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        
    print("Writing MP4 master...")
    mp4_path = os.path.join(output_dir, 'bw_cursor_master.mp4')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(mp4_path, fourcc, fps, (W, H))
    for fr in frames:
        writer.write(cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
    writer.release()
    
    print("Generating optimized B&W GIF...")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    gif_out = os.path.join(output_dir, 'mukil_particle_profile.gif')
    pal_tmp = os.path.join(output_dir, 'bw_palette.png')
    
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
        
    sz_mb = os.path.getsize(gif_out) / (1024*1024)
    print(f"B&W CURSOR ANIMATION SAVED: {gif_out} ({sz_mb:.2f} MB)")

if __name__ == '__main__':
    create_bw_cursor_dots_animation()
