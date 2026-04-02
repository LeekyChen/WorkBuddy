# 赛博摸鱼搭子（Cyber Slacker）- Windows MVP（Python + Qt）

这是一个桌面级“赛博反卷”桌宠 MVP：
- **Windows 优先**
- **进程嗅探**（不截屏）
- **随机主动搭话**（可配置频率，支持勿扰时段）
- **点击输入对话**（勿扰时不主动，但允许被动回复）
- **人格可编辑**：`AGENT.md`（上面字段 + 下面自由设定）
- **模型可配置**：`.env` + `config.yaml`（默认 Ollama + qwen3.5）

> 注：默认建议用本地 Ollama；如果你把 `BASE_URL` 指向云端，那就不再是“无需联网”。

## 目录结构

- `src/` 代码
- `assets/` 动图/素材（占位）
- `.env.example` 环境变量示例
- `config.example.yaml` 配置示例（说话频率、勿扰、进程分类、UI 行为等）
- `AGENT.md` 人格设定（可由用户自行修改）

## 快速开始（开发态）

1. 复制配置：
   - `.env.example` → `.env`
   - `config.example.yaml` → `config.yaml`

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 运行：

```bash
python -m src.main
```

## Docker（Linux 宿主机 X11）

> 说明：这是 Qt 桌面程序，Docker 里跑需要宿主机提供显示（X11）。
> Ollama 不打进镜像里：请用 `BASE_URL` 指向你自己的 Ollama（本机/局域网/远端）。

### 1) 构建镜像

```bash
docker build -t cyber-slacker-pet:latest .
```

### 2) 运行（最简单：host 网络 + X11）

```bash
xhost +local:docker

docker run --rm -it \
  --net=host \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -e BASE_URL=http://127.0.0.1:11434 \
  -e MODEL_NAME=qwen3.5:0.8b \
  -e LLM_ADAPTER=ollama_chat \
  -e OLLAMA_THINK=0 \
  cyber-slacker-pet:latest
```

也可以参考 `docker-compose.example.yml`。

## 下一步（建议优先级）

- P0：托盘菜单（退出/勿扰/穿透开关/频率调整）完善
- P0：Windows 点击穿透（Win32 扩展样式）稳定性
- P1：动图状态机（待机/敲键盘/生气/睡觉）
- P1：模型适配层（Ollama / OpenAI-compatible）更稳健的错误处理与超时
- P2：更多感知（history/保存频率）
