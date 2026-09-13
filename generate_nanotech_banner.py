import os
import sys
import math
import numpy as np
import cv2
import imageio_ffmpeg
import subprocess

def generate_nanotech_animated_banner():
    mukil_path = r'C:\Users\mukil\Mukil630\github_banner.png'
    iron_path = r'C:\Users\mukil\Mukil630\github_banner_ironman.png'
    output_dir = r'C:\Users\mukil\Mukil630'
    
    print("Loading Mukil and Iron Man banners...")
    base_mukil = cv2.imread(mukil_path)
    base_iron = cv2.imread(iron_path)
    if base_mukil is None or base_iron is None:
        raise FileNotFoundError("Could not load banner images")
        
    H, W = base_mukil.shape[:2]
    print(f"Banners loaded: {W}x{H}")
    
    # 60 frames @ 20 fps = 3.0 second seamless loop
    total_frames = 60
    fps = 20
    
    # Key coordinates
    red_eye = (408, 151)
    cyan_eye = (486, 144)
    portal_center = (720, 310)
    portal_radius = 235
    arc_center = (652, 385)
    
    term_cursor_pos = (195, 722)
    code_cursor_pos = (832, 408)
    
    # Hero bounding region where morph happens
    hero_x1, hero_x2 = 490, 975
    hero_y1, hero_y2 = 35, 665
    
    # Pre-generate floating embers
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
    
    # Heatmap cell twinkles
    heatmap_twinkles = []
    for _ in range(12):
        hx = np.random.randint(1075, 1330)
        hy = np.random.randint(665, 730)
        speed = np.random.uniform(0.15, 0.35)
        offset = np.random.uniform(0, math.pi * 2)
        heatmap_twinkles.append((hx, hy, speed, offset))

    # Nanotech particles setup for suit-up transitions
    N_nano = 90
    nano_offsets = np.random.uniform(-1, 1, (N_nano, 2))
    nano_speeds = np.random.uniform(0.8, 2.5, N_nano)

    frames = []
    print(f"Rendering {total_frames} frames of nanotech suit-up morph banner...")
    
    for f in range(total_frames):
        t = f / float(total_frames)
        
        # Determine Morph Progress:
        # Phase 1: Mukil developer mode (f = 0..17, ~0.0 to 0.28)
        # Phase 2: Nanotech suit-up transition (f = 18..31, ~0.30 to 0.52)
        # Phase 3: Iron Man combat mode (f = 32..49, ~0.53 to 0.82)
        # Phase 4: Nanotech de-suit transition (f = 50..59, ~0.83 to 0.99)
        
        if f < 18:
            # Mukil mode
            morph_weight = 0.0
            scan_y = -1
        elif 18 <= f < 32:
            # Suiting up: radial expansion from Arc Reactor + vertical sweep
            prog = (f - 18) / 14.0 # 0.0 to 1.0
            morph_weight = prog
            # Scan line sweeps from chest upward and downward
            scan_y = int(arc_center[1] - prog * (arc_center[1] - hero_y1 + 40))
        elif 32 <= f < 50:
            # Full Iron Man mode
            morph_weight = 1.0
            scan_y = -1
        else:
            # De-suit: top to bottom scanline
            prog = (f - 50) / 10.0 # 0.0 to 1.0
            morph_weight = 1.0 - prog
            scan_y = int(hero_y1 + prog * (hero_y2 - hero_y1))

        # Blend base frame
        if morph_weight <= 0.0:
            frame = base_mukil.copy()
        elif morph_weight >= 1.0:
            frame = base_iron.copy()
        else:
            # Nanotech hybrid blend inside hero area
            frame = base_mukil.copy()
            # Radial distance from Arc Reactor
            yy, xx = np.ogrid[hero_y1:hero_y2, hero_x1:hero_x2]
            dist_from_arc = np.sqrt((xx - arc_center[0])**2 + (yy - arc_center[1])**2)
            max_dist = 380.0
            
            # Nanotech wave threshold
            wave_front = morph_weight * (max_dist + 80)
            diff = wave_front - dist_from_arc
            
            # Sigmoid transition for metallic nanotech wave
            local_alpha = 1.0 / (1.0 + np.exp(-diff / 12.0))
            local_alpha = np.clip(local_alpha, 0.0, 1.0)[:, :, np.newaxis]
            
            hero_mukil = base_mukil[hero_y1:hero_y2, hero_x1:hero_x2].astype(np.float32)
            hero_iron = base_iron[hero_y1:hero_y2, hero_x1:hero_x2].astype(np.float32)
            
            hero_blended = hero_mukil * (1.0 - local_alpha) + hero_iron * local_alpha
            
            # Add glowing cyan nanotech scanline beam at wavefront
            edge_glow = np.exp(-((diff)**2) / 150.0)
            glow_intensity = np.clip(edge_glow * 180.0, 0, 255)[:, :, np.newaxis]
            cyan_beam = np.array([255, 220, 50], dtype=np.float32) # BGR cyan
            hero_blended = np.clip(hero_blended + cyan_beam * (glow_intensity / 255.0), 0, 255)
            
            frame[hero_y1:hero_y2, hero_x1:hero_x2] = hero_blended.astype(np.uint8)
            
            # Particle sparks at the nanotech wave edge
            for p in range(N_nano):
                ang = p * (2 * math.pi / N_nano)
                pr = wave_front + nano_offsets[p, 0] * 25
                px = int(arc_center[0] + pr * math.cos(ang))
                py = int(arc_center[1] + pr * math.sin(ang) * 0.85)
                if hero_x1 <= px < hero_x2 and hero_y1 <= py < hero_y2:
                    spark_col = (255, 230, 80) if p % 2 == 0 else (50, 180, 255)
                    cv2.circle(frame, (px, py), 2, spark_col, -1)

        # 1. Arc Reactor Pulse FX (Active during suit-up and Iron Man mode)
        if morph_weight > 0.15:
            # Heartbeat power surge
            arc_pulse = math.sin(t * math.pi * 6) ** 2 # Fast high-tech pulse
            arc_rad = int(12 + arc_pulse * 10 * morph_weight)
            # Outer cyan glow
            cv2.circle(frame, arc_center, arc_rad + 15, (255, 200, 30), -1, cv2.LINE_AA)
            cv2.circle(frame, arc_center, arc_rad + 6, (255, 240, 120), -1, cv2.LINE_AA)
            cv2.circle(frame, arc_center, arc_rad, (255, 255, 255), -1, cv2.LINE_AA)
            # Horizontal beam
            beam_w = int((40 + arc_pulse * 40) * morph_weight)
            cv2.line(frame, (arc_center[0] - beam_w, arc_center[1]), 
                            (arc_center[0] + beam_w, arc_center[1]), (255, 210, 60), 2, cv2.LINE_AA)

        # 2. Beast Eyes Pulse & Anamorphic Flares
        pulse_beat = math.sin(t * math.pi * 4) ** 4
        # Red eye
        r_rad = int(3 + pulse_beat * 5)
        cv2.circle(frame, red_eye, r_rad, (50, 50, 255), -1, cv2.LINE_AA)
        cv2.circle(frame, red_eye, max(1, r_rad - 2), (200, 200, 255), -1, cv2.LINE_AA)
        streak_len = int(12 + pulse_beat * 24)
        cv2.line(frame, (red_eye[0] - streak_len, red_eye[1]), 
                        (red_eye[0] + streak_len, red_eye[1]), (30, 30, 255), 1, cv2.LINE_AA)
        # Cyan eye
        c_rad = int(3 + pulse_beat * 5)
        cv2.circle(frame, cyan_eye, c_rad, (255, 230, 0), -1, cv2.LINE_AA)
        cv2.circle(frame, cyan_eye, max(1, c_rad - 2), (255, 255, 255), -1, cv2.LINE_AA)
        cv2.line(frame, (cyan_eye[0] - streak_len, cyan_eye[1]), 
                        (cyan_eye[0] + streak_len, cyan_eye[1]), (255, 200, 0), 1, cv2.LINE_AA)

        # 3. Rotating Holographic Portal Halo Ring
        rot_deg = (f * 6) % 360
        ring_col = (200, 160, 40)
        for arc_offset in [0, 60, 120, 180, 240, 300]:
            start_a = rot_deg + arc_offset
            cv2.ellipse(frame, portal_center, (portal_radius, portal_radius), 0, start_a, start_a + 35, ring_col, 1, cv2.LINE_AA)
            
        outer_r = int(portal_radius + 15 + math.sin(t * math.pi * 2) * 5)
        cv2.ellipse(frame, portal_center, (outer_r, outer_r), -rot_deg * 0.5, 0, 40, (14, 165, 233), 1, cv2.LINE_AA)
        cv2.ellipse(frame, portal_center, (outer_r, outer_r), -rot_deg * 0.5 + 180, 0, 40, (14, 165, 233), 1, cv2.LINE_AA)

        # 4. Chrome Shimmer & Light Sweep across "MUKIL 630"
        if 0.20 <= t <= 0.70:
            sweep_prog = (t - 0.20) / 0.50
            sweep_x = int(360 + sweep_prog * (1020 - 360))
            
            text_mask = np.zeros_like(frame)
            cv2.line(text_mask, (sweep_x - 30, 520), (sweep_x + 30, 670), (255, 255, 255), 18)
            cv2.line(text_mask, (sweep_x - 20, 520), (sweep_x + 20, 670), (255, 255, 255), 6)
            beam_blur = cv2.GaussianBlur(text_mask, (21, 21), 7)
            
            text_roi = frame[525:670, 340:1040].astype(np.float32)
            flare_roi = beam_blur[525:670, 340:1040].astype(np.float32) * 0.45
            frame[525:670, 340:1040] = np.clip(text_roi + flare_roi, 0, 255).astype(np.uint8)
            
            if 0.45 <= sweep_prog <= 0.55:
                glint_x, glint_y = sweep_x, 565
                cv2.drawMarker(frame, (glint_x, glint_y), (255, 255, 255), cv2.MARKER_STAR, 14, 1, cv2.LINE_AA)

        # 5. Blinking Terminal Cursor
        cursor_on = (f // 10) % 2 == 0
        if cursor_on:
            cv2.rectangle(frame, (term_cursor_pos[0], term_cursor_pos[1] - 12), 
                                 (term_cursor_pos[0] + 8, term_cursor_pos[1] + 2), (240, 240, 240), -1)
        else:
            cv2.rectangle(frame, (term_cursor_pos[0], term_cursor_pos[1] - 12), 
                                 (term_cursor_pos[0] + 8, term_cursor_pos[1] + 2), (8, 12, 20), -1)

        # 6. Blinking Code Cursor (in main.py)
        if (f // 8) % 2 == 0:
            cv2.line(frame, (code_cursor_pos[0], code_cursor_pos[1] - 10),
                            (code_cursor_pos[0], code_cursor_pos[1] + 4), (255, 255, 255), 2)

        # 7. Heatmap Live Twinkle
        for hx, hy, spd, off in heatmap_twinkles:
            tw_val = math.sin(f * spd + off)
            if tw_val > 0.3:
                tw_col = (40, 40, 240) if (hx + hy) % 2 == 0 else (100, 230, 100)
                cv2.circle(frame, (hx, hy), 2, tw_col, -1)

        # 8. Floating Atmospheric Embers
        for i in range(N_embers):
            ey = int((emb_y[i] - f * emb_speed[i] * 1.5) % H)
            ex = int((emb_x[i] + math.sin(f * 0.12 + i) * 12) % W)
            sz = emb_size[i]
            col = emb_colors[emb_color_idx[i]]
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
    generate_nanotech_animated_banner()
