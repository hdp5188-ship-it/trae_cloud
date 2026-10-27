#!/bin/bash
set -e
cd /workspace/dishuihu-future
mkdir -p ep02_build
FONT=/usr/share/fonts/opentype/noto-cjk-otf/NotoSansCJKsc-Bold.otf

SUB="drawtext=fontfile=$FONT:fontsize=38:fontcolor=white:x=(w-text_w)/2:y=h-120:box=1:boxcolor=black@0.5:boxborderw=16"
# 顶部字幕版：用于原图底部自带新闻标题条的镜头，避免文字重叠
SSUB="drawtext=fontfile=$FONT:fontsize=38:fontcolor=white:x=(w-text_w)/2:y=76:box=1:boxcolor=black@0.5:boxborderw=16"

# S1 全球坠落点 —— 缓慢推近
ffmpeg -y -loop 1 -i ep02-global-sites.jpg -vf "scale=3840:2160,zoompan=z='min(1+0.0008*on,1.14)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=150:s=1280x720:fps=25,vignette=PI/5,noise=alls=5:allf=t+u,format=yuv420p" -frames:v 150 -c:v libx264 -crf 20 -preset veryfast ep02_build/s1.mp4 2>/dev/null

# S2 北太平洋黑斑 —— 推近
ffmpeg -y -loop 1 -i ep02-pacific-blackspot.jpg -vf "scale=3840:2160,zoompan=z='min(1.04+0.0009*on,1.22)':x='iw/2-(iw/zoom/2)':y='(ih-ih/zoom)*0.55':d=150:s=1280x720:fps=25,${SUB}:text='北太平洋　·　没有陨石坑，只有一片黑色的海',vignette=PI/5,noise=alls=5:allf=t+u,format=yuv420p" -frames:v 150 -c:v libx264 -crf 20 -preset veryfast ep02_build/s2.mp4 2>/dev/null

# S3 撒哈拉侦察队抵达 —— 拉远
ffmpeg -y -loop 1 -i ep02-sahara-landing.jpg -vf "scale=3840:2160,zoompan=z='max(1.18-0.0010*on,1.0)':x='(iw-iw/zoom)*0.55':y='ih/2-(ih/zoom/2)':d=150:s=1280x720:fps=25,${SUB}:text='撒哈拉无人区　·　首支侦察队抵达',vignette=PI/5,noise=alls=5:allf=t+u,format=yuv420p" -frames:v 150 -c:v libx264 -crf 20 -preset veryfast ep02_build/s3.mp4 2>/dev/null

# S4 黑水特写 —— 强推近
ffmpeg -y -loop 1 -i ep02-sahara-landing.jpg -vf "crop=iw*0.52:ih*0.52:iw*0.24:ih*0.42,scale=3840:2160,zoompan=z='min(1+0.0018*on,1.35)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=150:s=1280x720:fps=25,${SUB}:text='黑水静止如镜　·　然后，泛起涟漪',vignette=PI/4.5,noise=alls=8:allf=t+u,format=yuv420p" -frames:v 150 -c:v libx264 -crf 20 -preset veryfast ep02_build/s4.mp4 2>/dev/null

# S5 卫星云图闪烁 —— 推近
ffmpeg -y -loop 1 -i ep02-satellite-night.jpg -vf "scale=3840:2160,zoompan=z='min(1+0.0010*on,1.18)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=150:s=1280x720:fps=25,${SUB}:text='卫星显示：所有黑点，同时开始闪烁',vignette=PI/5,noise=alls=6:allf=t+u,format=yuv420p" -frames:v 150 -c:v libx264 -crf 20 -preset veryfast ep02_build/s5.mp4 2>/dev/null

# S6 片尾字卡
ffmpeg -y -f lavfi -i color=c=black:s=1280x720:d=2.5:r=25 -vf "drawtext=fontfile=$FONT:fontsize=54:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2-30:text='《东海壁垒》',drawtext=fontfile=$FONT:fontsize=30:fontcolor=white@0.75:x=(w-text_w)/2:y=(h-text_h)/2+50:text='第 2 集　·　多点坠落',format=yuv420p" -c:v libx264 -crf 20 -preset veryfast ep02_build/s6.mp4 2>/dev/null

# xfade 拼接
ffmpeg -y -i ep02_build/s1.mp4 -i ep02_build/s2.mp4 -i ep02_build/s3.mp4 -i ep02_build/s4.mp4 -i ep02_build/s5.mp4 -i ep02_build/s6.mp4 -filter_complex "\
[0][1]xfade=transition=fade:duration=0.7:offset=5.3[a1];\
[a1][2]xfade=transition=fade:duration=0.7:offset=10.6[a2];\
[a2][3]xfade=transition=fade:duration=0.7:offset=15.9[a3];\
[a3][4]xfade=transition=fade:duration=0.7:offset=21.2[a4];\
[a4][5]xfade=transition=fadeblack:duration=0.8:offset=26.5[v]" -map "[v]" -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p -movflags +faststart ep02_build/video_only.mp4 2>/dev/null

# 环境音：低沉 drone + 棕噪声
ffmpeg -y -f lavfi -i "aevalsrc=0.09*sin(2*PI*52*t)+0.05*sin(2*PI*78*t)*(0.5+0.5*sin(2*PI*0.13*t)):s=48000:d=29" -f lavfi -i "anoisesrc=color=brown:amplitude=0.05:d=29" -filter_complex "[0][1]amix=inputs=2:duration=first,lowpass=f=320,afade=t=in:st=0:d=1.5,afade=t=out:st=27:d=2,volume=1.6[a]" -map "[a]" -c:a aac -b:a 128k ep02_build/audio.m4a 2>/dev/null

# 合并
ffmpeg -y -i ep02_build/video_only.mp4 -i ep02_build/audio.m4a -c:v copy -c:a copy -shortest ep02-duodian-zhuiluo-v1.mp4 2>/dev/null

echo "DONE"
ls -lh ep02-duodian-zhuiluo-v1.mp4
