#!/usr/bin/env python3
"""
server.py — 「左蝇右脑」实时闭环演示的本地服务。

架构（全部标准库 HTTP，没有前端框架、没有 WebSocket 依赖）：

    ┌─ 仿真线程 ────────────────────────────────────────────┐
    │  Brain  : fly-arena 的 LIF，跑 MaleCNS 全量 166,700    │
    │  Arena  : MuJoCo 里的 NeuroMechFly 解剖级蝇体          │
    │  循环   : eyes → brain.step(modulation=刺激) → 身体     │
    │           → MuJoCo 离屏渲染 → JPEG                     │
    └───────────────────────────────────────────────────────┘
              │ 最新帧 + 状态（带锁）
    ┌─ HTTP 服务 ───────────────────────────────────────────┐
    │  GET  /           前端页面                            │
    │  GET  /stream     MJPEG（multipart/x-mixed-replace）  │
    │  GET  /state      遥测 + 各组放电率                    │
    │  GET  /groups     可点击的组目录                       │
    │  POST /stimulate  {"group": "...", "mv": 8, "ms": 400}│
    └───────────────────────────────────────────────────────┘

刺激走的是 fly-arena `Brain.step(..., modulation={名称: (索引, mV)})` —— 它的
原生稀疏注入通道，不是我们改出来的后门。索引来自 regions.py，与图同一顺序。

运行：
    MUJOCO_GL=cgl <arena-venv>/bin/python live/server.py
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
DEFAULT_GRAPH = REPO / "_ref" / "arena-data" / "graph"

sys.path.insert(0, str(ROOT))
import regions as REGIONS  # noqa: E402

# 卡住判定：连续这么久位移都低于这个速度，就认为被卡住
STUCK_V = 0.15        # mm/s
STUCK_S = 4.0         # 生物秒
# 离场地中心超过这个距离就回中心。必须明显小于装饰条纹的位置（放大 4 倍后在 ±79.9），
# 否则相机会贴到条纹上 —— 画面上就是一条横穿全屏的橄榄绿长条。
BOUND_MM = 55.0
# 地面（MUJoCo 的 PLANE）碰撞是无限的，但**可见范围在编译期就固定成
# size=(half_size, half_size, 1)** —— 之后再改 model.geom_size 完全无效。
# fly-arena 自己传的是 half_size=22（44×44 mm 的场地），蝇子一走出去画面就是白茫茫。
# 所以必须在 Arena 构造**之前**把 FlatGroundWorld 换掉。
GROUND_HALF = 500.0        # 渲染 1000 × 1000 mm
TILE_MM = 3.14             # 保持棋盘格大小与原版一致（44 mm / texrepeat 14）


# ======================================================================
# 仿真
# ======================================================================
class Simulation:
    """跑 fly-arena 的脑 + 身体，并把最新帧与状态发布给 HTTP 层。"""

    def __init__(self, graph_dir: Path, seed: int = 1, width: int = 720, height: int = 540):
        import mujoco as mj

        import fly_arena.arena as FA          # 先拿到模块，才能替换它引用的类
        from fly_arena.brain import Brain, BrainConfig

        # 把 fly-arena 写死的 44×44 mm 地面换成 1000×1000 mm。
        # 不改这一步的话，蝇子走出 22 mm 后地面就整个不渲染了 —— 画面只剩白底和蝇子。
        # 注意：必须在这里改，因为可见范围是编译期定下来的，之后改 model.geom_size 无效。
        _real_ground = FA.FlatGroundWorld

        def _big_ground(*a, **kw):
            kw["half_size"] = GROUND_HALF
            return _real_ground(*a, **kw)

        FA.FlatGroundWorld = _big_ground
        try:
            self.arena = FA.Arena(seed=seed)
        finally:
            FA.FlatGroundWorld = _real_ground   # 用完还原，别影响别的调用方

        self.mj = mj
        t0 = time.perf_counter()
        self.regions = REGIONS.load(graph_dir)
        self.brain = Brain(graph_dir, BrainConfig(), seed=seed)
        self.neurons = int(self.brain.voltage.size)

        # 组 → 索引；再摊平成一张 (n,) 的组号表，供每帧 O(n) 统计放电率
        self.groups = self.regions["groups"]
        group_of = np.full(self.neurons, -1, dtype=np.int32)
        self.group_ids = [g for g in self.groups if self.groups[g]["count"] > 0]
        for gi, gid in enumerate(self.group_ids):
            group_of[self.groups[gid]["indices"]] = gi
        self.group_of = group_of + 1                      # 0 = 未分组
        self.n_groups = len(self.group_ids) + 1

        self.lock = threading.Lock()
        self.frame = None
        self.frame_seq = 0
        self.state = {}
        self.stimuli = {}                                 # group id → 到期时间
        self.ever_fired = np.zeros(self.neurons, dtype=bool)

        # 左面板的相机：跟随蝇子。
        # 俯角压到 -52°：这样画面顶部仍在看地面，不会把天空/背景那道白边收进来
        # （flygym 的世界没有 skybox，背景是纯白，露出来很难看）。
        self.renderer = mj.Renderer(self.arena.sim.mj_model, height, width)
        self.camera = mj.MjvCamera()
        mj.mjv_defaultCamera(self.camera)
        self.camera.type = mj.mjtCamera.mjCAMERA_FREE
        self.camera.distance = 7.0
        self.camera.azimuth = 130
        self.camera.elevation = -52

        # 边界墙、装饰条纹/信标、那个「不可见的盖子」全部在渲染里关掉。
        # 墙挡镜头；条纹是纯装饰（rgba [.77 .72 .45] 的橄榄绿），相机一贴近就是
        # 一条横穿画面的绿色长条；盖子（invisible_lid，z=6.5）rgba 透明但相机
        # 抬高后会正好穿过去，画面上一大块白。
        model = self.arena.sim.mj_model
        self.hidden = 0
        for i in range(model.ngeom):
            name = mj.mj_id2name(model, mj.mjtObj.mjOBJ_GEOM, i) or ""
            if name.startswith(("wall_", "stripe_", "beacon_")) or name == "invisible_lid":
                model.geom_group[i] = 3
                self.hidden += 1
        self.scene_option = mj.MjvOption()
        self.scene_option.geomgroup[3] = 0

        # 把装饰几何（边界墙 / 条纹 / 信标）一起往外挪，跟放大后的场地成比例。
        # 移动 geom_pos 是运行时有效值，这条是管用的（与地面 size 不同）。
        # 墙同时还会挡人：flygym 把它们也塞进了 world.ground_geoms，于是给蝇腿和墙
        # 生成了**显式 contact pair** —— 即使 contype/conaffinity 都是 0 也照样挡。
        # 原版 fly-arena 跑 7 秒就停在 (19.35, 18.0) 不动，就是这个原因。
        self.scale = 4.0
        for i in range(model.ngeom):
            name = mj.mj_id2name(model, mj.mjtObj.mjOBJ_GEOM, i) or ""
            if name.startswith(("wall_", "stripe_", "beacon_")):
                model.geom_pos[i][0] *= self.scale
                model.geom_pos[i][1] *= self.scale

        # 棋盘格的格子大小按新地面重算（Arena 里写死的 14 是给 44 mm 场地用的）
        grid = mj.mj_name2id(model, mj.mjtObj.mjOBJ_MATERIAL, "grid")
        if grid >= 0:
            model.mat_texrepeat[grid] = [2 * GROUND_HALF / TILE_MM] * 2

        # 卡住兜底：连续 STUCK_S 秒位移小于 STUCK_V 就自动回中心。
        # 这是**演示便利**，不是蝇的行为 —— 页面上会写明。
        self.last_pos = None
        self.stuck_for = 0.0
        self.recenters = 0
        self.last_sim = 0.0

        self.wall0 = time.perf_counter()          # 必须与循环里用的同一个时钟
        self.sim0 = self.arena.physics_steps * self.arena.sim.timestep
        self.ready_s = time.perf_counter() - t0
        self.iters = 0

    # ------------------------------------------------------------------
    def _active_modulation(self):
        now = time.perf_counter()
        expired = [g for g, until in self.stimuli.items() if until < now]
        for g in expired:
            del self.stimuli[g]
        if not self.stimuli:
            return None, []
        idx_parts, val_parts, names = [], [], []
        for gid, until in self.stimuli.items():
            g = self.groups[gid]
            idx_parts.append(g["indices"])
            val_parts.append(np.full(g["count"], g["mv"], dtype=np.float32))
            names.append(gid)
        return {"click": (np.concatenate(idx_parts), np.concatenate(val_parts))}, names

    def _group_rates(self, counts, seconds):
        """每组的放电率（Hz）。bincount 一次 O(n)，30 个组也只是一个数组扫描。"""
        fired = np.bincount(self.group_of, weights=counts.astype(np.float64),
                            minlength=self.n_groups)
        return [{ "id": gid,
                  "hz": float(fired[i + 1] / max(self.groups[gid]["count"], 1) / seconds) }
                for i, gid in enumerate(self.group_ids)]

    # ------------------------------------------------------------------
    def loop(self):
        while True:
            t_wall = time.perf_counter()
            eyes = self.arena.eyes()
            with self.lock:
                modulation, active = self._active_modulation()
            command, counts = self.brain.step(self.brain.sample_eyes(eyes),
                                              modulation=modulation)
            self.arena.step(command)

            # 渲染：相机跟随蝇子
            pos = self.arena.position
            self.camera.lookat[:] = [pos[0], pos[1], max(pos[2], 0.6)]
            self.renderer.update_scene(self.arena.sim.mj_data, self.camera,
                                       scene_option=self.scene_option)
            rgb = self.renderer.render()
            buf = io.BytesIO()
            Image.fromarray(rgb).save(buf, format="JPEG", quality=72)
            jpeg = buf.getvalue()

            counts_i = counts.astype(np.int32)
            self.ever_fired |= counts_i > 0
            sim_s = self.arena.physics_steps * self.arena.sim.timestep
            wall = time.perf_counter() - self.wall0
            dt = sim_s - self.sim0

            # ---- 回中心：① 走出安全半径 ② 连续 STUCK_S 生物秒没怎么动 ----
            if abs(pos[0]) > BOUND_MM or abs(pos[1]) > BOUND_MM:
                self.recenter()
                self.stuck_for = 0.0
                self.last_pos = None
            elif self.last_pos is None:
                self.last_pos = pos[:2].copy()
                self.last_sim = sim_s
            else:
                dsim = sim_s - self.last_sim
                if dsim > 0.05:                       # 大约每 5 步判一次，够稳
                    v = float(np.hypot(pos[0] - self.last_pos[0],
                                       pos[1] - self.last_pos[1])) / dsim
                    self.stuck_for = self.stuck_for + dsim if v < STUCK_V else 0.0
                    self.last_pos = pos[:2].copy()
                    self.last_sim = sim_s
                    if self.stuck_for > STUCK_S:
                        self.recenter()
                        self.stuck_for = 0.0
                        self.last_pos = None

            state = {
                "sim_s": sim_s,
                "wall_s": wall,
                "realtime": dt / wall if wall > 0 else 0.0,
                "spikes_per_10ms": int(counts_i.sum()),
                "spikes_total": int(counts_i.sum()),
                "ever_fired": int(self.ever_fired.sum()),
                "gait": [round(float(command[0]), 3), round(float(command[1]), 3)],
                # ⚠️ fly-arena 的 arena.position 已经是毫米，不要再乘 1000
                "position_mm": [round(float(v), 2) for v in pos],
                "heading_rad": round(float(self.arena.heading), 4),
                "upright": round(float(self.arena.upright), 3),
                "active": list(active),
                "loop_ms": round((time.perf_counter() - t_wall) * 1000, 1),
                "recenters": self.recenters,
                "stuck_for": round(self.stuck_for, 2),
                "group_hz": self._group_rates(counts_i, 0.01),
                "ready_s": round(self.ready_s, 1),
                "neurons": self.neurons,
            }
            with self.lock:
                self.frame = jpeg
                self.frame_seq += 1
                self.state = state
            self.iters += 1
            if self.iters % 60 == 0:                      # 心跳，便于确认没卡住
                print(f"  sim {sim_s:6.2f}s  loop {state['loop_ms']:5.1f}ms  "
                      f"rt {state['realtime']:.3f}x  spikes {state['spikes_per_10ms']:,}  "
                      f"fired {state['ever_fired']:,}", flush=True)

    # ------------------------------------------------------------------
    def stimulate(self, gid: str, mv: float, ms: float) -> dict:
        g = self.groups.get(gid)
        if g is None or g["count"] == 0:
            raise KeyError(gid)
        g["mv"] = float(mv)
        with self.lock:
            self.stimuli[gid] = time.perf_counter() + ms / 1000.0
        return {"group": gid, "neurons": g["count"], "mv": mv, "ms": ms}

    def clear(self):
        with self.lock:
            self.stimuli.clear()

    def recenter(self):
        """把蝇子挪回场地中心（演示便利，不是蝇的行为）。"""
        d = self.arena.sim.mj_data
        ang = float(np.random.default_rng().uniform(-np.pi, np.pi))
        d.qpos[0] = 0.0
        d.qpos[1] = 0.0
        d.qpos[2] = 1.1
        d.qpos[3:7] = [np.cos(ang / 2), 0.0, 0.0, np.sin(ang / 2)]
        d.qvel[:6] = 0.0
        self.mj.mj_forward(self.arena.sim.mj_model, d)
        self.recenters += 1


# ======================================================================
# HTTP
# ======================================================================
class Handler(BaseHTTPRequestHandler):
    sim: Simulation = None
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *a):                       # 保持输出干净
        pass

    # -- 小工具 --------------------------------------------------------
    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _file(self, path: Path, ctype: str):
        if not path.is_file():
            self.send_error(404)
            return
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    # -- 路由 ----------------------------------------------------------
    def do_GET(self):
        p = self.path.split("?")[0]
        if p in ("/", "/index.html"):
            return self._file(ROOT / "web" / "index.html", "text/html; charset=utf-8")
        if p == "/app.js":
            return self._file(ROOT / "web" / "app.js", "text/javascript; charset=utf-8")
        if p == "/mcns-meshes.js":
            return self._file(REPO / "assets" / "mcns-meshes.js", "text/javascript; charset=utf-8")
        if p == "/mcns-3d.js":
            return self._file(REPO / "assets" / "mcns-3d.js", "text/javascript; charset=utf-8")
        if p == "/mcns-region-info.js":
            return self._file(REPO / "assets" / "mcns-region-info.js", "text/javascript; charset=utf-8")
        if p == "/groups":
            return self._json({"neurons": self.sim.neurons,
                               "groups": [{"id": g["id"], "zh": g["zh"], "note": g["note"],
                                           "count": g["count"], "mesh": g["mesh"],
                                           "kind": g["kind"]}
                                          for g in self.sim.groups.values()]})
        if p == "/state":
            with self.sim.lock:
                return self._json(self.sim.state or {"starting": True})
        if p == "/frame":
            # 单帧 JPEG。带 ?since=N 时长轮询：只有出现比 N 新的帧才返回，
            # 这样浏览器不会空转狂拉（直接返回缓存帧会被拉到 1000+ 次/秒）。
            since = -1
            if "?" in self.path:
                for kv in self.path.split("?", 1)[1].split("&"):
                    if kv.startswith("since="):
                        try:
                            since = int(kv[6:])
                        except ValueError:
                            pass
            deadline = time.perf_counter() + 0.25
            while True:
                with self.sim.lock:
                    seq, frame = self.sim.frame_seq, self.sim.frame
                if frame is not None and seq != since:
                    break
                if time.perf_counter() > deadline:
                    break
                time.sleep(0.004)
            if frame is None:
                self.send_error(503)
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(frame)))
            self.send_header("X-Frame-Seq", str(seq))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(frame)
            return
        if p == "/stream":
            return self._stream()
        self.send_error(404)

    def do_POST(self):
        if self.path.split("?")[0] != "/stimulate":
            self.send_error(404)
            return
        n = int(self.headers.get("Content-Length", 0))
        try:
            req = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            return self._json({"error": "bad json"}, 400)
        try:
            if req.get("action") == "clear":
                self.sim.clear()
                return self._json({"cleared": True})
            if req.get("action") == "recenter":
                self.sim.recenter()
                return self._json({"recentered": True})
            out = self.sim.stimulate(str(req["group"]),
                                     float(req.get("mv", 8.0)),
                                     float(req.get("ms", 400)))
        except KeyError as e:
            return self._json({"error": f"unknown group {e}"}, 404)
        return self._json(out)

    # -- MJPEG ---------------------------------------------------------
    def _stream(self):
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        last = -1
        try:
            while True:
                with self.sim.lock:
                    seq, frame = self.sim.frame_seq, self.sim.frame
                if frame is None or seq == last:
                    time.sleep(0.004)
                    continue
                last = seq
                self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\n")
                self.wfile.write(f"Content-Length: {len(frame)}\r\n\r\n".encode())
                self.wfile.write(frame)
                self.wfile.write(b"\r\n")
        except (BrokenPipeError, ConnectionResetError):
            return


# ======================================================================
def main():
    ap = argparse.ArgumentParser(description="左蝇右脑实时闭环演示")
    ap.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    ap.add_argument("--port", type=int, default=8099)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--width", type=int, default=720)
    ap.add_argument("--height", type=int, default=540)
    args = ap.parse_args()

    print(f"载入图与身体（MaleCNS 全量）…", flush=True)
    sim = Simulation(args.graph, seed=args.seed, width=args.width, height=args.height)
    print(f"就绪：{sim.neurons:,} 个神经元 · 预热 {sim.ready_s:.1f}s", flush=True)

    Handler.sim = sim

    # ⚠️ MuJoCo 的 GL 上下文（macOS 上是 CGL）是在**主线程**创建的，
    # 跨线程去 update_scene/render 会死锁 —— 现象是 /stream 一个字节都收不到、
    # /state 永远停在 starting。所以：主线程跑仿真与渲染，HTTP 服务放后台线程。
    # HTTP 侧只碰 self.frame / self.state（都有锁），不碰 GL。
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f"→ http://127.0.0.1:{args.port}", flush=True)
    try:
        sim.loop()
    except KeyboardInterrupt:
        print("\n停止")
    finally:
        srv.shutdown()


if __name__ == "__main__":
    main()
