import os
import sys
import time
import math
import subprocess
import numpy as np
import cv2
from PIL import Image

def generate_hologram_animation():
    input_path = r'C:\Users\mukil\Mukil630\assets\mukil_input.jpg'
    output_dir = r'C:\Users\mukil\Mukil630\assets'
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Loading image from {input_path}...")
    raw_img = cv2.imread(input_path)
    if raw_img is None:
        raise FileNotFoundError(f"Cannot open {input_path}")
        
    # Resolution for GitHub profile
    W, H = 520, 520
    img = cv2.resize(raw_img, (W, H), interpolation=cv2.INTER_AREA)
    
    # 1. Edge & Feature Detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 40, 120)
    
    # Extract points:
    # A) Dense regular grid (every 2 pixels): 260 x 260 = 67,600 points
    yg, xg = np.mgrid[0:H:2, 0:W:2]
    grid_pts = np.column_stack([yg.ravel(), xg.ravel()])
    
    # B) Extra edge points to give razor-sharp facial contours and silhouette
    edge_coords = np.argwhere(edges > 0)
    if len(edge_coords) > 20000:
        edge_sub = edge_coords[np.random.choice(len(edge_coords), 20000, replace=False)]
    else:
        edge_sub = edge_coords
        
    all_target_pts = np.vstack([grid_pts, edge_sub]).astype(np.float32)
    N = len(all_target_pts)
    print(f"Total simulated quantum particles: {N:,}")
    
    ty = np.clip(all_target_pts[:, 0].astype(int), 0, H - 1)
    tx = np.clip(all_target_pts[:, 1].astype(int), 0, W - 1)
    target_bgr = img[ty, tx].astype(np.float32) # [N, 3]
    
    # 2. Particle starting dispersed positions (Vortex + Cosmic Field)
    np.random.seed(101)
    cx, cy = W / 2.0, H / 2.0
    
    # 3D spherical / vortex dispersion
    angles = np.random.uniform(0, 2 * np.pi, N)
    radii = np.random.exponential(scale=180, size=N) + 60
    radii = np.clip(radii, 40, 480)
    
    # Add spiral swirl
    swirl_angles = angles + (radii * 0.02)
    start_x = cx + radii * np.cos(swirl_angles) + np.random.normal(0, 20, N)
    start_y = cy + radii * np.sin(swirl_angles) + np.random.normal(0, 20, N)
    
    # Per-particle arrival delay / stagger (edges snap slightly earlier, center follows)
    dist_from_center = np.sqrt((tx - cx)**2 + (ty - cy)**2)
    is_edge_pt = np.zeros(N, dtype=bool)
    is_edge_pt[len(grid_pts):] = True
    
    # Stagger factor: -0.15 to +0.15
    stagger = (dist_from_center / 350.0) * 0.2 + np.random.uniform(-0.08, 0.08, N)
    if is_edge_pt.any():
        stagger[is_edge_pt] -= 0.1 # Edges arrive first!
        
    # Dispersed glowing cyber colors:
    # Sunset warm particles get golden glow, dark suit gets electric cyan/violet
    brightness = (target_bgr[:, 0] * 0.114 + target_bgr[:, 1] * 0.587 + target_bgr[:, 2] * 0.299)
    is_warm = (target_bgr[:, 2] > 120) & (target_bgr[:, 0] < 100) # Sunset orange/reds
    
    neon_cyan = np.array([255, 220, 0], dtype=np.float32)     # BGR
    electric_gold = np.array([0, 180, 255], dtype=np.float32)  # BGR
    neon_purple = np.array([255, 60, 160], dtype=np.float32)   # BGR
    core_white = np.array([255, 255, 255], dtype=np.float32)
    
    dispersed_bgr = np.zeros_like(target_bgr)
    for i in range(N):
        if is_warm[i]:
            dispersed_bgr[i] = electric_gold if np.random.rand() > 0.3 else core_white
        elif brightness[i] < 60:
            dispersed_bgr[i] = neon_cyan if np.random.rand() > 0.4 else neon_purple
        else:
            dispersed_bgr[i] = neon_cyan if np.random.rand() > 0.5 else core_white

    # Ambient floating particles
    N_amb = 80
    amb_x = np.random.uniform(0, W, N_amb)
    amb_y = np.random.uniform(0, H, N_amb)
    amb_spd = np.random.uniform(0.8, 2.2, N_amb)
    amb_sz = np.random.choice([1, 2], N_amb, p=[0.7, 0.3])
    
    total_frames = 100 # 100 frames @ 20 fps = 5.0 seconds
    fps = 20
    
    frames = []
    print("Simulating particle trajectories and rendering frames...")
    
    for f in range(total_frames):
        t = f / float(total_frames)
        
        # Timeline:
        # 0.00 - 0.30: Deep space vortex swirl, inward magnetic acceleration
        # 0.30 - 0.52: Particles snap into place forming the luminous dot cloud of Mukil
        # 0.52 - 0.68: Laser scanline sweeps, dots crystallize into sharp photo
        # 0.68 - 0.88: Ultra-crisp photo hero display with living HUD and embers
        # 0.88 - 1.00: Smooth quantum dissipation back to vortex (seamless loop)
        
        # Base global convergence progress
        if t < 0.30:
            gt = t / 0.30
            # Quad ease in
            global_prog = 0.45 * (gt ** 2.2)
            swirl_rot = (1.0 - gt) * 1.2
        elif t < 0.52:
            gt = (t - 0.30) / 0.22
            # Cubic ease out to lock points
            global_prog = 0.45 + 0.55 * (1.0 - (1.0 - gt) ** 3)
            swirl_rot = (1.0 - gt) * 0.3
        elif t < 0.88:
            global_prog = 1.0
            swirl_rot = 0.0
        else:
            gt = (t - 0.88) / 0.12
            # Dissolve back
            global_prog = 1.0 - (gt ** 2)
            swirl_rot = -gt * 0.8

        # Swirl rotation
        if abs(swirl_rot) > 1e-4:
            cos_s = math.cos(swirl_rot)
            sin_s = math.sin(swirl_rot)
            cur_sx = cx + (start_x - cx) * cos_s - (start_y - cy) * sin_s
            cur_sy = cy + (start_x - cx) * sin_s + (start_y - cy) * cos_s
        else:
            cur_sx = start_x
            cur_sy = start_y

        # Per particle progress with stagger
        part_prog = np.clip(global_prog - stagger * (1.0 - global_prog) * global_prog * 3.0, 0.0, 1.0)
        part_prog_2d = part_prog[:, None]

        # Current particle coordinates
        px = cur_sx[:, None] * (1.0 - part_prog_2d) + all_target_pts[:, 1:2] * part_prog_2d
        py = cur_sy[:, None] * (1.0 - part_prog_2d) + all_target_pts[:, 0:1] * part_prog_2d
        
        ix = np.clip(np.round(px.ravel()).astype(int), 0, W - 1)
        iy = np.clip(np.round(py.ravel()).astype(int), 0, H - 1)
        
        # Color transition: cyber neon -> photo colors
        c_prog = np.clip((global_prog - 0.25) / 0.65, 0.0, 1.0)
        cur_colors = (dispersed_bgr * (1.0 - c_prog) + target_bgr * c_prog).astype(np.uint8)
        
        # Build frame canvas
        canvas = np.zeros((H, W, 3), dtype=np.uint8)
        
        # Subtle cyber grid background
        grid_step = 32
        canvas[::grid_step, :] = (12, 16, 24)
        canvas[:, ::grid_step] = (12, 16, 24)
        
        # Draw particles onto canvas
        canvas[iy, ix] = cur_colors
        
        # When particles are dispersed, apply glowing bloom
        if global_prog < 0.95:
            # Downsample and blur for optical glow
            low_res = cv2.resize(canvas, (W // 4, H // 4), interpolation=cv2.INTER_LINEAR)
            blur_res = cv2.GaussianBlur(low_res, (7, 7), 2.5)
            bloom = cv2.resize(blur_res, (W, H), interpolation=cv2.INTER_LINEAR)
            canvas = cv2.addWeighted(canvas, 0.85, bloom, 0.55, 0)

        # Laser Scanline & Photo Reveal Phase
        if t >= 0.52 and t < 0.90:
            scan_ratio = (t - 0.52) / 0.16 # sweeps across in 0.16 of time (~16 frames)
            scan_y = int(scan_ratio * (H + 30)) - 15
            
            if scan_y > 0:
                # Top part up to scan_y becomes the full-resolution photo!
                revealed = min(scan_y, H)
                mask = np.zeros((H, W), dtype=np.float32)
                mask[:revealed, :] = 1.0
                
                # Soft blend ramp at the laser edge
                ramp_len = 16
                if revealed - ramp_len > 0:
                    ramp = np.linspace(1.0, 0.0, ramp_len)
                    mask[revealed - ramp_len:revealed, :] = ramp[:, None]
                    
                blended = (img.astype(np.float32) * mask[:, :, None] + 
                           canvas.astype(np.float32) * (1.0 - mask[:, :, None])).astype(np.uint8)
                canvas = blended
                
                # Draw the glowing holographic laser scanline
                if 0 <= scan_y < H:
                    # Bright laser core
                    cv2.line(canvas, (0, scan_y), (W, scan_y), (255, 240, 50), 2)
                    # Ambient flare around laser
                    glow_layer = canvas.copy()
                    cv2.line(glow_layer, (0, scan_y), (W, scan_y), (255, 255, 255), 6)
                    cv2.addWeighted(canvas, 0.65, glow_layer, 0.35, 0, dst=canvas)
        elif t >= 0.68 and t < 0.88:
            # During full lock hold, show full photo with subtle glowing breathing
            pulse = 1.0 + 0.03 * math.sin(f * 0.3)
            # Full photo
            canvas = img.copy()

        # Ambient quantum embers floating up
        for a_idx in range(N_amb):
            ay = int((amb_y[a_idx] - f * amb_spd[a_idx] * 1.5) % H)
            ax = int((amb_x[a_idx] + math.sin(f * 0.08 + a_idx) * 12) % W)
            sz = amb_sz[a_idx]
            spark_col = (255, 210, 80) if a_idx % 2 == 0 else (0, 220, 255)
            cv2.circle(canvas, (ax, ay), sz, spark_col, -1)
            
        # HUD Interface (Futuristic Recruiter / Cyberpunk Aesthetics)
        pad = 16
        b_len = 28
        hud_cyan = (233, 165, 14) # 0EA5E9
        
        # 1. Corner Tech Brackets
        for corner in [(pad, pad), (W - pad, pad), (pad, H - pad), (W - pad, H - pad)]:
            cx_c, cy_c = corner
            sx = 1 if cx_c == pad else -1
            sy = 1 if cy_c == pad else -1
            cv2.line(canvas, (cx_c, cy_c), (cx_c + sx * b_len, cy_c), hud_cyan, 2)
            cv2.line(canvas, (cx_c, cy_c), (cx_c, cy_c + sy * b_len), hud_cyan, 2)
            
        # 2. Reticle around face
        face_x, face_y = int(W * 0.48), int(H * 0.33)
        ret_rad = 85
        rot_deg = (f * 4) % 360
        # 4 arcs
        for arc in [0, 90, 180, 270]:
            cv2.ellipse(canvas, (face_x, face_y), (ret_rad, ret_rad), rot_deg + arc, 0, 40, hud_cyan, 1)
        # Center crosshair
        cv2.circle(canvas, (face_x, face_y), 4, (0, 240, 255), 1)
        cv2.line(canvas, (face_x - 10, face_y), (face_x + 10, face_y), (0, 240, 255), 1)
        cv2.line(canvas, (face_x, face_y - 10), (face_x, face_y + 10), (0, 240, 255), 1)

        # 3. Clean, NON-OVERLAPPING Header Text
        # Left Header
        cv2.putText(canvas, "JARVIS NEURAL CORE", (pad + 6, pad + 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180, 220, 255), 1, cv2.LINE_AA)
        
        # Right Header (Status)
        if t < 0.52:
            pct = int((t / 0.52) * 100)
            status_str = f"ASSEMBLING: {pct}% [87.6K DOTS]"
            s_col = (0, 230, 255)
        elif t < 0.88:
            status_str = "STATUS: SYNTHESIZED [100%]"
            s_col = (50, 255, 140)
        else:
            status_str = "QUANTUM FLUX // RE-ORCHESTRATING"
            s_col = (0, 190, 255)
            
        cv2.putText(canvas, status_str, (W - pad - 195, pad + 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, s_col, 1, cv2.LINE_AA)

        # 4. Clean Footer Bar
        # Identity
        cv2.putText(canvas, "MUKILARASU S", (pad + 6, H - pad - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.44, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(canvas, "| AI ENGINEER", (pad + 122, H - pad - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (14, 165, 233), 1, cv2.LINE_AA)

        # Bottom Right Telemetry
        tele_str = f"FRAME {f:03d}/100 | LIVE HUD"
        cv2.putText(canvas, tele_str, (W - pad - 150, H - pad - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.34, (140, 160, 180), 1, cv2.LINE_AA)

        # Audio / Equalizer bars
        eq_base_x = pad + 6
        eq_base_y = H - pad - 22
        for bar in range(12):
            h_bar = int(2 + 8 * abs(math.sin(f * 0.25 + bar * 0.5)))
            cv2.line(canvas, (eq_base_x + bar * 4, eq_base_y), 
                     (eq_base_x + bar * 4, eq_base_y - h_bar), (0, 220, 255), 1)

        # Convert to RGB
        frames.append(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB))
        
        if f % 20 == 0:
            print(f"Rendered {f}/{total_frames} frames")
            
    print("All frames rendered! Writing MP4 master...")
    mp4_master = os.path.join(output_dir, 'mukil_particle_master.mp4')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(mp4_master, fourcc, fps, (W, H))
    for fr in frames:
        writer.write(cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
    writer.release()
    print(f"Master MP4 saved: {os.path.getsize(mp4_master) / (1024*1024):.2f} MB")
    
    # Generate ultra-compressed, gorgeous GIF using ffmpeg palette
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    gif_out = os.path.join(output_dir, 'mukil_particle_profile.gif')
    palette_tmp = os.path.join(output_dir, 'temp_palette.png')
    
    print("Generating optimized 128-color palette...")
    cmd_pal = [
        ffmpeg_exe, '-y', '-i', mp4_master,
        '-vf', f'fps={fps},scale={W}:{H}:flags=lanczos,palettegen=max_colors=128:reserve_transparent=0:stats_mode=diff',
        palette_tmp
    ]
    subprocess.run(cmd_pal, check=True)
    
    print("Generating final crystal GIF...")
    cmd_gif = [
        ffmpeg_exe, '-y', '-i', mp4_master, '-i', palette_tmp,
        '-lavfi', f'fps={fps},scale={W}:{H}:flags=lanczos [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=3',
        gif_out
    ]
    subprocess.run(cmd_gif, check=True)
    
    if os.path.exists(palette_tmp):
        os.remove(palette_tmp)
        
    gif_size_mb = os.path.getsize(gif_out) / (1024*1024)
    print(f"FINAL GIF CREATED: {gif_out} ({gif_size_mb:.2f} MB)")
    
    # Also create a high efficiency webm/mp4 copy for index.html or video tag
    h264_out = os.path.join(output_dir, 'mukil_particle_profile.mp4')
    cmd_h264 = [
        ffmpeg_exe, '-y', '-i', mp4_master,
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '22', '-preset', 'fast',
        h264_out
    ]
    subprocess.run(cmd_h264, check=True)
    print(f"H.264 MP4 created: {h264_out} ({os.path.getsize(h264_out) / (1024*1024):.2f} MB)")

if __name__ == '__main__':
    generate_hologram_animation()
