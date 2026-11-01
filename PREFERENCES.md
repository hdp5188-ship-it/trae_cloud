# 用户偏好（写公众号推文时先读这个）

## 写作
- 中文，上海本地生活口吻，接地气，不要 AI 腔
- 长短句交错，一两句一段，少用过渡词
- 结构：开头引入 → 分论点（小标题 + 信息卡）→ 结尾互动引导
- 标题要有信息量，不用标题党

## 素材
- 图片必须是真实照片/官方发布，来源在图下标注
- 效果图可以用，但必须写明出处；AI 生成图必须标注"AI 生成，非官方效果图"
- 封面优先用效果图（用户近期偏好）
- 素材存 `/workspace/wechat-articles/assets/`，文件名用小写英文短横线
- 抖音视频用浏览器取 video.currentSrc，再 curl 带 Referer 下载，ffmpeg 抽帧

## 排版
- 公众号兼容：所有样式写成行内 `style=""`，禁止 `class` 和 `<style>` 标签
- 图片：`<img src="..." style="max-width:100%;width:100%;">`

## 交付与发布
- HTML 存 `/workspace/wechat-articles/article-YYYY-MM-DD-<slug>.html`
- 能走 API 就直接进草稿箱，不要让我手动复制
- 账号：未认证订阅号，只能建草稿，发布我手动点
- 凭据在 `/workspace/.wechat.json`，不要在回复里回显

## 沟通
- 已经给过的素材、已经确认过的设定，不要反复确认
- 回复简短，先给结论
