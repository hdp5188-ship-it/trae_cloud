# 第一集《黑色来客》关键帧 → 镜头映射表

- 版本：v1（2026-11-02）
- 对应生产表：[ep01_shotlist.md](file:///workspace/donghai-bibao/production/ep01_shotlist.md)
- 关键帧目录：`/workspace/donghai-bibao/keyframes/ep01/clean/`
- 总时长：75 秒 / 13 镜 / 24fps / 9:16

## 使用规则

1. 同名多版本按 **v3 > v2 > v1** 取用；无版本号即唯一版本。
2. 表格中的「首帧锚点」是图生视频时**第 1 张参考图**，决定起幅构图；「辅助参考」只提供屏幕内容、人物长相或材质，不决定起幅。
3. 所有关键帧是 1440×2560 或 1440×2445。2445 高的图不是标准 9:16，生成前需统一（见下节）。
4. 关键帧只用于**单镜头首帧/参考**，不得把多张关键帧直接拼成视频当补帧使用。

## 首帧预处理（重要）

| 原尺寸 | 问题 | 处理 |
|---|---|---|
| 1440×2560 | 标准 9:16 | 直接使用 |
| 1440×2445 / 1440×2450 | 比 9:16 略宽 | 左右各裁 32–33px 至 1375×2445，再等比放大到 1440×2560；不要上下补黑边 |
| 任何带白边的旧图 | 非 clean 版 | 不使用，只用 `clean` 目录 |

统一输出：`1440×2560`、JPEG 质量 92、sRGB。

## 逐镜映射

| 镜号 | 时间 | 首帧锚点 | 辅助参考 | 用途 | 备注 |
|---|---|---|---|---|---|
| S01 | 0–15s | `kf01_radar_clean.jpg` | `kf03a_su_xiao_closeup_v2_clean.jpg`、`kf02_black_sphere_clean.jpg` | 环厅全景 → 推近苏晓 → 屏幕内黑球 → 转头 | kf01 已有红色轨道弧与苏晓前景，适合起幅；kf02 只作屏幕内插入，不作实体景 |
| S02 | 15–21s | `kf03b_station_commander_clean.jpg` | `kf03a_su_xiao_closeup_v2_clean.jpg`、`kf03_decision_clean.jpg` | 站长半身起幅，横移带出环桌与多国视频窗 | **kf03 只取背景与环桌，不取其中人物**（其中苏晓长发、站长肩章版与锁定设定不符） |
| S03 | 21–25s | `kf04d_launch_officer_hand_v2_clean.jpg` | `kf04_launch_lock_clean.jpg` | 戴黑手套的手按下红色发射钮，背景地球全息与发射序列 | kf04 提供地球全息与桌面构成；手部优先 v2 |
| S04 | 25–31s | `kf04a_silo_pov_v2_clean.jpg` | 无 | 井内仰拍：井盖开、导弹抬头、准星里针尖黑点 | 无人物，首批测试镜 |
| S05 | 31–36s | `kf04b_missile_pov_v2_clean.jpg` | `kf04a_silo_pov_v2_clean.jpg`（准星样式） | 导引头视角逼近，黑球保持针尖大小 | 不得把黑球放大成行星 |
| S06 | 36–41s | `kf04c_silo_salvo_v2_clean.jpg` | 无 | 荒漠多井齐射，导弹垂直上升、尾焰向下 | 低角度大场面，首批可测 |
| S07 | 41–46s | `kf05_launch_clean.jpg` | `kf05b_convergence_v2_clean.jpg` | 舷窗起幅 → 导弹从多方向汇入 → 苏晓窗前侧影 | 合围图仅作尾段参考；导弹尾焰朝外即正确 |
| S08 | 46–52s | `kf06b_multi_impact_v2_clean.jpg` | `kf06_impact_clean.jpg` | 多向命中：白光、裂纹、碎片云、冲击环 | 无烟柱、无翻滚火球；碎片为暗色 |
| S09 | 52–56s | `kf07b_crew_cheering_wide_v3_clean.jpg` | `kf07_empty_radar_v2_clean.jpg` | 全舱欢呼，前景苏晓不动 | **不用 kf07_false_victory 作首帧**：其中苏晓为低马尾、制服蓝边，与锁定形象不符；仅可裁掉人物作空镜 |
| S10 | 56–60s | `kf07a_su_xiao_false_victory_v2_clean.jpg` | `kf07c_crew_cheering_closeup_v3_clean.jpg` | 苏晓近景，背景欢呼虚化，盯空白雷达 | 台词可选；如保留需单独配音 |
| S11 | 60–66s | `kf08_second_wave_v3_clean.jpg` | `kf08_second_wave_v2_clean.jpg`（目标分布） | 舷窗/主屏：十几个登陆舱亮起并修正姿态 | 采用 v3 人物制服与发型版本 |
| S12 | 66–71s | `kf03a_su_xiao_closeup_v2_clean.jpg` | `kf09_trajectories_clean.jpg` | 苏晓侧脸起幅 → 焦点转到全息地球轨迹 → 上海红锁 → 回侧脸 | **kf09 只取屏幕部分，不取人物**：其中苏晓穿深色指挥服、低马尾，违反制服体系 |
| S13 | 71–75s | `kf10a_lin_zheng_closeup_v2_clean.jpg` | `kf10_shanghai_evacuation_clean.jpg` | 林铮雨夜近景 → 拉出疏散人群 → 急停切黑 | 雨夜人群作尾段参考；林铮以 v2 锁定 |

## 十三个镜头的关键帧覆盖率

| 状态 | 镜头 | 说明 |
|---|---|---|
| 完整 | S01、S04、S05、S06、S07、S08、S09、S10、S11、S13 | 首帧+辅助参考齐全 |
| 需绕开人物 | S02、S12 | 背景/屏幕可用，人物必须以锁定图另传参考 |
| 需本地合成 | S03、S08、S12 | 发射序列 UI、闪白/碎片、轨迹锁定线建议在剪辑里叠加，不依赖 AI 生成文字 |
| 缺口 | S01 起幅警报逐层亮起 | 关键帧是静态红灯，需在剪辑里做逐层亮度动画或叠红色扫光 |
| 缺口 | S08 滤光板降下半秒 | 无对应关键帧，建议用 kf07b 的舱内顶部结构裁切+压暗+液压音效代替 |
| 缺口 | S13 远景人群 | kf10 可作背景板，前景林铮用 kf10a 抠像合成 |

## 首帧之外的建议尾帧

| 镜号 | 建议尾帧 | 目的 |
|---|---|---|
| S01 | `kf03a_su_xiao_closeup_v2_clean.jpg` | 保证转头落点与下一镜人物一致 |
| S07 | `kf05b_convergence_v2_clean.jpg` | 合围完成，接 S08 命中 |
| S08 | `kf06b_multi_impact_v2_clean.jpg` | 碎片云扩散状态，接 S09 空雷达 |
| S11 | `kf08_second_wave_v3_clean.jpg` | 登陆舱姿态修正，接 S12 轨迹计算 |
| S13 | 黑场 | 钩子收尾 |

## 旧版与禁用清单

- `kf03a_su_xiao_closeup_clean.jpg`（v1）：脸型与 v2 不一致，禁用。
- `kf04a_*_clean.jpg`、`kf04b_*_clean.jpg`、`kf04c_*_clean.jpg`（v1）：导弹方向/构图未修正，禁用。
- `kf04d_launch_officer_hand_clean.jpg`（v1）：手部结构弱，禁用。
- `kf07a_su_xiao_false_victory_clean.jpg`（v1）：表情与 v2 不一致，禁用。
- `kf07b_crew_cheering_wide_v2`、`kf07c_crew_cheering_closeup_v2`：被 v3 取代，禁用。
- `kf08_second_wave_clean`、`kf08_second_wave_v2`：被 v3 取代，S11 禁用（可作目标分布参考）。
- `kf10a_lin_zheng_closeup_clean.jpg`：被 v2 取代，禁用。
- `kf07_false_victory_clean.jpg`：环境光好，但人物发型/制服边色不符；只可裁人物后作空镜。
- `kf09_trajectories_clean.jpg`：只取全息地球与轨迹 UI；人物禁用。
- `kf03_decision_clean.jpg`：只取环桌、视频窗与背景；人物禁用。

## 资产自检

- [x] 13 镜全部有可用首帧锚点
- [x] 每镜至少 1 张辅助参考（S04/S06 除外，单独参考足够）
- [x] 旧版已标注禁用
- [x] 尺寸统一方案已给出
- [ ] 需人工确认：S02/S12 的锁定人物合成方案（见角色一致性包）
