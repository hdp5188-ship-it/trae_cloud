#!/bin/bash
set -e
cd /workspace/人间一碗_第1集

ffmpeg -y \
 -i clips/ep1_01_kitchen_00001_.mp4 \
 -i clips/ep1_02_linwan_taste_00001_.mp4 \
 -i clips/ep1_03_xiaozhou_00001_.mp4 \
 -i clips/ep1b_01_laozhao_00001_.mp4 \
 -i clips/ep1_04_press_00001_.mp4 \
 -i clips/ep1_05_suman_toast_00001_.mp4 \
 -i clips/ep1b_02_packet_00001_.mp4 \
 -i clips/ep1b_03_reporters_00001_.mp4 \
 -i clips/ep1_07_linwan_stand_00001_.mp4 \
 -i clips/ep1_08_suman_cold_00001_.mp4 \
 -i clips/ep1b_04_suman_save_00001_.mp4 \
 -i clips/ep1_06_chen_00001_.mp4 \
 -i clips/ep1b_05_badge_00001_.mp4 \
 -i clips/ep1_09_street_00001_.mp4 \
 -i clips/ep1_10_phone_00001_.mp4 \
 -i clips/ep1b_06_hotel_00001_.mp4 \
 -i tts/l1.mp3 -i tts/l2.mp3 -i tts/n1.mp3 -i tts/l3.mp3 -i tts/n2.mp3 \
 -i tts/l5.mp3 -i tts/l7.mp3 -i tts/l8.mp3 -i tts/n3.mp3 -i tts/l4.mp3 \
 -i tts/n4.mp3 -i tts/n5.mp3 \
 -filter_complex "\
[0:v]scale=640:1152,setsar=1,fps=24[v0];\
[1:v]scale=640:1152,setsar=1,fps=24[v1];\
[2:v]scale=640:1152,setsar=1,fps=24[v2];\
[3:v]scale=640:1152,setsar=1,fps=24[v3];\
[4:v]scale=640:1152,setsar=1,fps=24[v4];\
[5:v]scale=640:1152,setsar=1,fps=24[v5];\
[6:v]scale=640:1152,setsar=1,fps=24[v6];\
[7:v]scale=640:1152,setsar=1,fps=24[v7];\
[8:v]scale=640:1152,setsar=1,fps=24[v8];\
[9:v]scale=640:1152,setsar=1,fps=24[v9];\
[10:v]scale=640:1152,setsar=1,fps=24[v10];\
[11:v]scale=640:1152,setsar=1,fps=24[v11];\
[12:v]scale=640:1152,setsar=1,fps=24[v12];\
[13:v]scale=640:1152,setsar=1,fps=24[v13];\
[14:v]scale=640:1152,setsar=1,fps=24[v14];\
[15:v]scale=640:1152,setsar=1,fps=24[v15];\
[v0][v1][v2][v3][v4][v5][v6][v7][v8][v9][v10][v11][v12][v13][v14][v15]concat=n=16:v=1:a=0,subtitles=字幕_128s.ass:fontsdir=/usr/share/fonts[vout];\
[0:a][1:a][2:a][3:a][4:a][5:a][6:a][7:a][8:a][9:a][10:a][11:a][12:a][13:a][14:a][15:a]concat=n=16:v=0:a=1,volume=0.10[amb];\
[16:a]adelay=8400|8400,volume=1.9[t0];\
[17:a]adelay=16300|16300,volume=1.9[t1];\
[18:a]adelay=24300|24300,volume=1.9[t2];\
[19:a]adelay=40300|40300,volume=1.9[t3];\
[20:a]adelay=48400|48400,volume=1.9[t4];\
[21:a]adelay=56300|56300,volume=1.9[t5];\
[22:a]adelay=64300|64300,volume=1.9[t6];\
[23:a]adelay=72300|72300,volume=1.9[t7];\
[24:a]adelay=80300|80300,volume=1.9[t8];\
[25:a]adelay=88300|88300,volume=1.9[t9];\
[26:a]adelay=96300|96300,volume=1.9[t10];\
[27:a]adelay=120400|120400,volume=1.9[t11];\
[amb][t0][t1][t2][t3][t4][t5][t6][t7][t8][t9][t10][t11]amix=inputs=13:normalize=0:duration=first[aout]" \
 -map "[vout]" -map "[aout]" -t 128 \
 -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p -r 24 \
 -c:a aac -b:a 160k -ar 48000 -movflags +faststart \
 人间一碗_第1集_128秒正片.mp4

ffprobe -v error -show_entries format=duration,size -of default=nw=1 人间一碗_第1集_128秒正片.mp4
