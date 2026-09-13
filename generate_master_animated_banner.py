import os
import sys
import math
import numpy as np
import cv2
import imageio_ffmpeg
import subprocess

def generate_master_animated_banner():
    banner_path = r'C:\Users\mukil\Mukil630\github_banner.png'
    output_dir = r'C:\Users\mukil\Mukil630'
    
    print("Loading base banner...")
    base_img = cv2.imread(banner_path)
    if base_img is None:
        raise FileNotFoundError(f"Could not load {banner_path}")
        
    H, W = base_img.shape[:2]
    print(f"Base canvas: {W}x{H}")
    
    # 60 frames @ 20 FPS = 3.0 second seamless mathematical loop
    total_frames = 60
    fps = 20
    
    # Coordinates
    red_eye = (408, 151)
    cyan_eye = (486, 144)
    portal_center = (720, 310)
    portal_radius = 235
    
    term_cursor_pos = (195, 722)
    code_cursor_pos = (832, 408)
    
    # Tech stack icon bounding regions (3 rows x 4 cols)
    # Row 1: y: 280..380
    # Row 2: y: 410..510
    # Row 3: y: 540..640
    tech_rows = [
        (280, 380, 15, 255),
        (410, 510, 15, 255),
        (540, 640, 15, 255)
    ]
    
    # Arch progress bar region:
    # y: 585..605, x: 1000..1340
    prog_y1, prog_y2 = 582, 608
    prog_x1, prog_x2 = 1000, 1340
    
    # Heatmap cell region:
    # y: 660..745, x: 1060..1355
    np.random.seed(42)
    heatmap_twinkles = []
    for _ in range(16):
        hx = np.random.randint(1075, 1345)
        hy = np.random.randint(665, 735)
        speed = np.random.uniform(0.18, 0.38)
        offset = np.random.uniform(0, math.pi * 2)
        heatmap_twinkles.append((hx, hy, speed, offset))
        
    # Floating atmospheric embers
    N_embers = 85
    emb_x = np.random.uniform(W * 0.10, W * 0.90, N_embers)
    emb_y = np.random.uniform(40, H - 40, N_embers)
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
    
    frames = []
    print(f"Rendering {total_frames} frames of complete multi-object animation...")
    
    for f in range(total_frames):
        t = f / float(total_frames)
        frame = base_img.copy()
        
        # -------------------------------------------------------------
        # 1. CYBER PANTHER BEAST EYES: Dual Pulse & Anamorphic Flares
        # -------------------------------------------------------------
        pulse_beat = math.sin(t * math.pi * 4) ** 4 # Sharp rhythmic double-heartbeat
        streak_len = int(14 + pulse_beat * 28)
        
        # Red eye (left)
        r_rad = int(3 + pulse_beat * 5)
        cv2.circle(frame, red_eye, r_rad, (50, 50, 255), -1, cv2.LINE_AA)
        cv2.circle(frame, red_eye, max(1, r_rad - 2), (200, 200, 255), -1, cv2.LINE_AA)
        cv2.line(frame, (red_eye[0] - streak_len, red_eye[1]), 
                        (red_eye[0] + streak_len, red_eye[1]), (30, 30, 255), 1, cv2.LINE_AA)
        cv2.line(frame, (red_eye[0] - streak_len//2, red_eye[1]), 
                        (red_eye[0] + streak_len//2, red_eye[1]), (180, 180, 255), 1, cv2.LINE_AA)
        
        # Cyan eye (right)
        c_rad = int(3 + pulse_beat * 5)
        cv2.circle(frame, cyan_eye, c_rad, (255, 230, 0), -1, cv2.LINE_AA)
        cv2.circle(frame, cyan_eye, max(1, c_rad - 2), (255, 255, 255), -1, cv2.LINE_AA)
        cv2.line(frame, (cyan_eye[0] - streak_len, cyan_eye[1]), 
                        (cyan_eye[0] + streak_len, cyan_eye[1]), (255, 200, 0), 1, cv2.LINE_AA)
        cv2.line(frame, (cyan_eye[0] - streak_len//2, cyan_eye[1]), 
                        (cyan_eye[0] + streak_len//2, cyan_eye[1]), (255, 255, 255), 1, cv2.LINE_AA)
                        
        # Center circle around Mukil remains 100% clean and static as in original artwork

        # -------------------------------------------------------------
        # 4. TECH STACK: Sequential Circuit Pulse Wave
        # -------------------------------------------------------------
        # Wave cycles through row 0, 1, 2 every 20 frames
        wave_pos = (f % 30) / 30.0 * 3.0 # 0.0 to 3.0
        for r_idx, (ry1, ry2, rx1, rx2) in enumerate(tech_rows):
            dist = abs(wave_pos - r_idx)
            if dist < 0.8:
                glow_int = (1.0 - dist / 0.8) * 0.28
                tech_roi = frame[ry1:ry2, rx1:rx2].astype(np.float32)
                tech_tint = np.array([45, 30, 0], dtype=np.float32) # Cyan tint
                frame[ry1:ry2, rx1:rx2] = np.clip(tech_roi + tech_tint * glow_int, 0, 255).astype(np.uint8)

        # -------------------------------------------------------------
        # 5. TOP-LEFT TERMINAL: Glowing Pulsing Prompt & Cursor
        # -------------------------------------------------------------
        # Red glowing pulse on "> Reason. Build. Automate. Scale." (y: 125..150, x: 25..360)
        reason_pulse = (math.sin(t * math.pi * 4) + 1.0) * 0.5 # 0 to 1
        reason_roi = frame[120:155, 25:350].astype(np.float32)
        red_flare = np.array([0, 10, 45], dtype=np.float32) * reason_pulse
        frame[120:155, 25:350] = np.clip(reason_roi + red_flare, 0, 255).astype(np.uint8)
        
        # Blinking cyan cursor at git push command line
        if (f // 8) % 2 == 0:
            cv2.line(frame, (230, 102), (230, 114), (255, 220, 0), 2)

        # -------------------------------------------------------------
        # 6. CODE EDITOR (`main.py`): Blinking Cursor & Execution Indicator
        # -------------------------------------------------------------
        # Blinking cursor at line 10
        if (f // 8) % 2 == 0:
            cv2.line(frame, (code_cursor_pos[0], code_cursor_pos[1] - 10),
                            (code_cursor_pos[0], code_cursor_pos[1] + 4), (255, 255, 255), 2)
            
        # Running play icon pulse (around x: 720, y: 550 or near line 10)
        play_pulse = (math.sin(t * math.pi * 6) + 1.0) * 0.5
        # Soft cyan energy glow around code window borders
        code_roi = frame[215:240, 715:750].astype(np.float32)
        frame[215:240, 715:750] = np.clip(code_roi + np.array([30, 20, 0]) * play_pulse, 0, 255).astype(np.uint8)

        # -------------------------------------------------------------
        # 7. ARCH LINUX VITALS: Animated Progress Bar Scan
        # -------------------------------------------------------------
        # Energy highlight moving across "Loading greatness" progress bar (x: 1000 to 1340)
        prog_scan_x = int(prog_x1 + (t * (prog_x2 - prog_x1)))
        cv2.line(frame, (prog_scan_x - 15, prog_y1), (prog_scan_x + 15, prog_y2), (255, 100, 100), 2, cv2.LINE_AA)
        cv2.circle(frame, (prog_scan_x, (prog_y1 + prog_y2) // 2), 4, (255, 255, 255), -1, cv2.LINE_AA)

        # -------------------------------------------------------------
        # 8. METALLIC 3D "MUKIL 630": Chrome Shimmer & Star Glint Sweep
        # -------------------------------------------------------------
        if 0.15 <= t <= 0.75:
            sweep_prog = (t - 0.15) / 0.60
            sweep_x = int(360 + sweep_prog * (1020 - 360))
            
            text_mask = np.zeros_like(frame)
            cv2.line(text_mask, (sweep_x - 32, 520), (sweep_x + 32, 670), (255, 255, 255), 20)
            cv2.line(text_mask, (sweep_x - 18, 520), (sweep_x + 18, 670), (255, 255, 255), 6)
            beam_blur = cv2.GaussianBlur(text_mask, (21, 21), 7)
            
            text_roi = frame[525:670, 340:1040].astype(np.float32)
            flare_roi = beam_blur[525:670, 340:1040].astype(np.float32) * 0.48
            frame[525:670, 340:1040] = np.clip(text_roi + flare_roi, 0, 255).astype(np.uint8)
            
            # Star glints at letter crests
            if 0.40 <= sweep_prog <= 0.60:
                cv2.drawMarker(frame, (sweep_x, 565), (255, 255, 255), cv2.MARKER_STAR, 16, 1, cv2.LINE_AA)
                cv2.circle(frame, (sweep_x, 565), 3, (255, 255, 255), -1, cv2.LINE_AA)

        # -------------------------------------------------------------
        # 9. BOTTOM-LEFT TERMINAL: Blinking Command Cursor (C:\Users\Mukil630> █)
        # -------------------------------------------------------------
        cursor_on = (f // 10) % 2 == 0
        if cursor_on:
            cv2.rectangle(frame, (term_cursor_pos[0], term_cursor_pos[1] - 12), 
                                 (term_cursor_pos[0] + 8, term_cursor_pos[1] + 2), (240, 240, 240), -1)
        else:
            cv2.rectangle(frame, (term_cursor_pos[0], term_cursor_pos[1] - 12), 
                                 (term_cursor_pos[0] + 8, term_cursor_pos[1] + 2), (8, 12, 20), -1)

        # -------------------------------------------------------------
        # 10. GITHUB CONTRIBUTIONS HEATMAP: Real-Time Commit Twinkles
        # -------------------------------------------------------------
        for hx, hy, spd, off in heatmap_twinkles:
            tw_val = math.sin(f * spd + off)
            if tw_val > 0.25:
                tw_col = (40, 40, 250) if (hx + hy) % 2 == 0 else (100, 240, 120)
                cv2.circle(frame, (hx, hy), 2, tw_col, -1)
                cv2.circle(frame, (hx, hy), 4, tw_col, 1, cv2.LINE_AA)

        # -------------------------------------------------------------
        # 11. ATMOSPHERIC EMBERS: 85 Cosmic Floating Particles
        # -------------------------------------------------------------
        for i in range(N_embers):
            ey = int((emb_y[i] - f * emb_speed[i] * 1.5) % H)
            ex = int((emb_x[i] + math.sin(f * 0.12 + i) * 14) % W)
            sz = emb_size[i]
            col = emb_colors[emb_color_idx[i]]
            cv2.circle(frame, (ex, ey), sz, col, -1)

        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
    print("Encoding Full HD MP4...")
    mp4_path = os.path.join(output_dir, 'github_banner.mp4')
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(mp4_path, fourcc, fps, (W, H))
    for fr in frames:
        writer.write(cv2.cvtColor(fr, cv2.COLOR_RGB2BGR))
    writer.release()
    print(f"MP4 saved: {mp4_path} ({os.path.getsize(mp4_path) / (1024*1024):.2f} MB)")
    
    print("Generating ultra-optimized GIF with FFmpeg lanczos palette...")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    gif_path = os.path.join(output_dir, 'github_banner.gif')
    pal_path = os.path.join(output_dir, 'master_palette.png')
    
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
        
    print(f"MASTER ANIMATED BANNER GIF SAVED: {gif_path} ({os.path.getsize(gif_path) / (1024*1024):.2f} MB)")

if __name__ == '__main__':
    generate_master_animated_banner()
