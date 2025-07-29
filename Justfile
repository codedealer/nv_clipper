set shell := ["powershell.exe", "-c"]

default:
  just --list

fetch_tags:
  git fetch origin --tags --force

poetry_sync:
  poetry lock --no-update && poetry install --sync

pr pr_number:
    git fetch -fu origin refs/pull/{{pr_number}}/head:pr/{{pr_number}}
    git checkout pr/{{pr_number}}

pretty-ts:
  npx prettier "src/**/*.{ts,js,json}" --write
pretty-py:
  uv run ruff check --select I --fix src/clipper && uv run ruff format src/clipper
pretty-py-check:
  uv run ruff format --check src/clipper

test-py:
  uv run pytest src/clipper -s --cov=src/clipper --cov-report=html -m "not slow"
test-py-slow:
  uv run pytest src/clipper --cov=src/clipper --cov-report=html

lint-py:
  uv run ruff check src/clipper
lint-py-fix:
  uv run ruff check src/clipper --fix

poetry-sync:
  poetry lock --no-update && poetry install --sync

# GUI Development Workflow:
# 1. Terminal 1: just gui-vite    (starts Vite dev server)
# 2. Terminal 2: just gui-dev     (starts GUI in dev mode)
#
# GUI Production Workflow:
# 1. just gui-build               (builds frontend)
# 2. just gui-prod                (starts GUI in prod mode)
gui-dev:
  Write-Host "🎬 Starting NV Clipper GUI in development mode..." -ForegroundColor Blue
  uv run yt_clipper_gui_dev

gui-vite:
  Write-Host "🚀 Starting Vite development server..." -ForegroundColor Green
  cd src/gui-frontend; pnpm run dev

gui-build:
  Write-Host "🏗️ Building frontend for production..." -ForegroundColor Yellow
  cd src/gui-frontend; pnpm run build

gui-prod:
  Write-Host "🎬 Starting NV Clipper GUI in production mode..." -ForegroundColor Blue
  uv run yt_clipper_gui

build-ts:
  npx tsc --watch
build-ts-ne:
  npx tsc --noEmit --watch
build-ts-p:
  run-s -c build-ts pretty

# Build single-file executable (standard approach, ~2GB)
build-py $UV_PREVIEW="1":
  uv run pyinstaller ./src/clipper/yt_clipper.py --icon=../../../assets/image/pepe-clipper.gif --onefile --workpath ./dist/py/work/ --distpath ./dist/py/ --specpath ./dist/py/spec --additional-hooks-dir ./hooks --noconfirm
  just _copy-cuda-libs "./dist/py"

# Build single-file with runtime GPU loading (small executable + separate DLLs, ~300MB + 1.9GB)
build-py-runtime $UV_PREVIEW="1":
  if (-not (Test-Path "./cache/gpu-libs/.cache_complete")) { Write-Host "Creating GPU library cache..."; just cache-gpu-libs; }
  $env:RUNTIME_GPU_LIBS = "1"; uv run pyinstaller ./src/clipper/yt_clipper.py --icon=../../../assets/image/pepe-clipper.gif --onefile --workpath ./dist/py/work/ --distpath ./dist/py/ --specpath ./dist/py/spec --additional-hooks-dir ./hooks --noconfirm

# Build single-file with cached libraries (~2.6GB)
build-py-cached $UV_PREVIEW="1":
  if (-not (Test-Path "./cache/gpu-libs/.cache_complete")) { Write-Host "Creating GPU library cache..."; just cache-gpu-libs; }
  $env:CACHED_GPU_LIBS = "1"; uv run pyinstaller ./src/clipper/yt_clipper.py --icon=../../../assets/image/pepe-clipper.gif --onefile --workpath ./dist/py/work/ --distpath ./dist/py/ --specpath ./dist/py/spec --additional-hooks-dir ./hooks --noconfirm

# Build CPU-only version for users without NVIDIA GPUs (~30MB)
build-py-cpu-fast $UV_PREVIEW="1":
  $env:SKIP_GPU_LIBS = "1"; uv run pyinstaller ./src/clipper/yt_clipper.py --icon=../../../assets/image/pepe-clipper.gif --onefile --workpath ./dist/py/work-cpu/ --distpath ./dist/py-cpu/ --specpath ./dist/py/spec-cpu --additional-hooks-dir ./hooks --exclude-module onnxruntime --noconfirm

# Cache NVIDIA libraries separately for reuse across builds
cache-gpu-libs:
  $env:CACHED_GPU_LIBS = "1"; uv run pyinstaller ./src/clipper/yt_clipper.py --icon=../../../assets/image/pepe-clipper.gif --onefile --workpath ./dist/py/work-cache/ --distpath ./dist/py-cache/ --specpath ./dist/py/spec-cache --additional-hooks-dir ./hooks --name yt_clipper-cache --noconfirm

# Create deployment package (uses runtime loading for small executable)
package-release:
  just build-py-runtime
  Write-Host "Created yt_clipper.exe (~73MB) + lib-cuda/ folder with GPU DLLs"

# Clean the GPU library cache
clean-cache:
  if (Test-Path "./cache/gpu-libs") { Remove-Item "./cache/gpu-libs" -Recurse -Force; }

build-all:
  run-s -c build-ts-p build-py
bundle-w:
  npx parcel watch src/markup/yt_clipper.ts --dist-dir dist/js --target userscript
bundle-tc-w:
  run-p -c build-ts-ne bundle-w
bundle-prod:
  npx parcel build --no-scope-hoist --no-optimize

clean-dist:
  rm -r ./dist/*
clean-sandbox:
  rm -r ./sandbox/*

version-patch:
  uv run bumpit -p patch
version-minor:
  uv run bumpit -p minor
version-major:
  uv run bumpit -p major
pigar:
  pigar -P ./src/clipper -p ./src/clipper/requirements.txt --without-referenced-comments

# Internal helper: Copy CUDA DLLs to deployment directory
_copy-cuda-libs target_dir:
  if (Test-Path "./cache/gpu-libs") { $lib_cuda_dir = "{{target_dir}}/lib-cuda"; if (-not (Test-Path $lib_cuda_dir)) { New-Item -ItemType Directory -Path $lib_cuda_dir -Force | Out-Null }; Get-ChildItem "./cache/gpu-libs" -Recurse -Filter "*.dll" | Copy-Item -Destination $lib_cuda_dir -Force; $dll_count = (Get-ChildItem $lib_cuda_dir -Filter "*.dll").Count; Write-Host "Copied $dll_count required CUDA DLLs to $lib_cuda_dir" } else { Write-Host "Warning: No GPU library cache found. Run 'just cache-gpu-libs' first for GPU support." }
