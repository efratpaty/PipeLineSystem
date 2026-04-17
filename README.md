# Video Motion Detection Pipeline

A real-time video analytics pipeline that detects and highlights motion across frames using
a multi-process architecture with zero-copy inter-process communication.

## What It Does

The pipeline reads a video file, detects moving objects frame by frame, and displays the
result in a window. Detected regions are blurred and outlined with bounding boxes; a live
timestamp is overlaid on every frame.

Three independent OS processes run concurrently in a linear chain:

```
Streamer  -->  Detector  -->  Displayer
```

| Process | Responsibility |
|---------|---------------|
| **Streamer** | Reads raw frames from the video file via OpenCV and writes them into shared memory. |
| **Detector** | Reads frames from shared memory, runs frame-differencing motion detection, and annotates detections as bounding boxes. |
| **Displayer** | Reads annotated frames from shared memory, draws overlays (blur, box, timestamp), and renders each frame to the screen at the correct playback rate. |

## Architecture: IPC Design

Each frame is a multi-megabyte numpy array. Moving that data between processes efficiently
is the central design challenge. The pipeline uses a **two-layer IPC strategy**:

| Layer | Mechanism | What travels through it |
|-------|-----------|-------------------------|
| **Frame data** | `multiprocessing.shared_memory` (OS shared memory) | Raw pixel arrays — never copied |
| **Coordination** | `multiprocessing.Queue` | Lightweight messages: slot index + frame index + detections |

### The Shared Memory Pool

At startup, `main.py` allocates a fixed pool of shared memory blocks — one block per
potential in-flight frame. Each block is sized exactly for one raw frame (`height x width x channels` bytes).

Processes communicate by passing a **slot index** (a single integer) through a Queue.
The receiving process reads or writes the frame directly from the named shared memory block
at that index. No serialization, no copies.

A separate `free_slots` Queue acts as a recycling bin: the Displayer returns a slot index
to it after it has finished rendering that frame. The Streamer blocks on `free_slots.get()`
before writing the next frame, which provides natural backpressure and bounds memory usage
to exactly `POOL_SIZE` frames at any given time.

## Why This Approach Over the Alternatives

### Option 1 — Queue with serialized frames (rejected)

The most obvious approach: pass the full numpy array through a `multiprocessing.Queue`.
Python pickles the array before putting it on the queue and unpickles it on the other side.

**Problem:** A single 1080p frame is roughly 6 MB. At 30 fps that is ~180 MB/s of pickle
overhead in each inter-process hop. With two hops (Streamer→Detector and Detector→Displayer)
the pipeline would spend more CPU time copying bytes than processing them. Real-time
playback becomes impossible on modest hardware.

This was the original implementation. The commit `Replace Queue-based frame transport with
shared memory pool` documents the measured motivation for switching.

### Option 2 — Pipes (`multiprocessing.Pipe`)

Pipes are lower-level and offer no built-in capacity limit, so a fast Streamer can flood a
slow Detector without any backpressure. They also serialize data the same way Queues do,
so the per-frame copy cost is identical. Queues are strictly better here: they add bounded
capacity (backpressure) and a thread-safe multi-producer/consumer interface at negligible
extra cost.

### Option 3 — Memory-mapped files (`mmap`)

Memory-mapped files give shared access to a file on disk mapped into each process's address
space. The OS may keep it entirely in RAM, making reads and writes fast. However:

- Requires managing a file on disk (path, cleanup, permissions).
- `multiprocessing.shared_memory` (Python 3.8+) is the same concept — OS-level shared
  memory — but with a clean Python API, no disk path required, and automatic unlinking.

There is no benefit to choosing `mmap` over `shared_memory` for this use case.

### Option 4 — External message brokers (Redis, ZeroMQ, etc.)

External brokers introduce a network stack and an out-of-process daemon even for local IPC.
They add operational complexity (the broker must be running, configured, and monitored)
and reintroduce serialization cost for binary frame data. Appropriate for distributed
systems; overkill for a single-machine pipeline.

### Chosen Approach — Shared memory pool + Queue coordination

- **Zero-copy frame transport.** Pixel data never leaves the shared memory block. The only
  thing that travels through a Queue is a slot index (one integer).
- **Bounded memory footprint.** The fixed pool size caps the number of in-flight frames.
  The `free_slots` Queue provides automatic backpressure: the Streamer cannot run ahead by
  more than `POOL_SIZE` frames.
- **Ordering and flow control come for free.** `multiprocessing.Queue` is FIFO and
  thread/process-safe. `maxsize` on the inter-stage Queues adds a second layer of
  backpressure between the Streamer→Detector and Detector→Displayer hops.
- **No external dependencies.** Everything used (`multiprocessing.shared_memory`,
  `multiprocessing.Queue`) is part of the Python standard library.

## Setup

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
# Install dependencies
uv sync

# Install with development tools (linter)
uv sync --all-extras
```

## Usage

```bash
uv run python main.py <path/to/video.mp4>
```

Press `q` in the display window to exit early.

## Development

```bash
# Lint
uv run ruff check .

# Tests
uv run pytest
```
