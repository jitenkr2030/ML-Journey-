#!/usr/bin/env python3
"""
ReconcileAI — Master Sync Script
=================================
Usage: python3 sync_deploy.py [direction]

Directions:
  to-deploy   : Copy from source (backend/ + root) → deploy/  [DEFAULT]
  from-deploy : Copy from deploy/ → source (catch up)
  both        : Sync both ways (ensures identical)

Workflow:
  1. Develop in backend/ + root files
  2. Run: python3 sync_deploy.py to-deploy
  3. cd deploy && git add . && git commit && git push
  4. Deploy on Deplexo
"""

import os
import sys
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
DEPLOY = os.path.join(ROOT, "deploy")
BACKEND = os.path.join(ROOT, "backend")

# Files/dirs to sync from ROOT → DEPLOY (source of truth)
ROOT_FILES = [
    'index.html', 'admin.html', 'dashboard.html', 'tools.html',
    'robots.txt', 'sitemap.xml', 'favicon.svg', 'favicon.ico',
    'price_migration.sql',
]

ROOT_DIRS = [
    'blog', 'free-tools', 'templates', 'extensions',
]

# Files/dirs to sync from BACKEND → DEPLOY/backend
BACKEND_SKIP = ['__pycache__', '.git', 'node_modules', '*.pyc']

def should_skip(name):
    return any(skip in name for skip in BACKEND_SKIP)


def sync_backend(src_base, dst_base, direction="to-deploy"):
    """Sync backend directory."""
    if direction == "from-deploy":
        src_base, dst_base = dst_base, src_base

    count = 0
    for root, dirs, files in os.walk(src_base):
        dirs[:] = [d for d in dirs if not should_skip(d)]
        for fname in files:
            if should_skip(fname):
                continue
            src = os.path.join(root, fname)
            rel = os.path.relpath(src, src_base)
            dst = os.path.join(dst_base, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            count += 1
    return count


def sync_root_files(direction="to-deploy"):
    """Sync root-level files."""
    count = 0
    for fname in ROOT_FILES:
        if direction == "to-deploy":
            src, dst = os.path.join(ROOT, fname), os.path.join(DEPLOY, fname)
        else:
            src, dst = os.path.join(DEPLOY, fname), os.path.join(ROOT, fname)

        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            count += 1
            print(f"   [{'→' if direction == 'to-deploy' else '←'}] {fname}")
    return count


def sync_root_dirs(direction="to-deploy"):
    """Sync root-level directories."""
    count = 0
    for dirname in ROOT_DIRS:
        if direction == "to-deploy":
            src, dst = os.path.join(ROOT, dirname), os.path.join(DEPLOY, dirname)
        else:
            src, dst = os.path.join(DEPLOY, dirname), os.path.join(ROOT, dirname)

        if os.path.exists(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            n = sum(len(f) for _, _, f in os.walk(dst))
            count += n
            print(f"   [{'→' if direction == 'to-deploy' else '←'}] {dirname}/ ({n} files)")
    return count


def main():
    direction = sys.argv[1] if len(sys.argv) > 1 else "to-deploy"

    print("=" * 55)
    print(f"  ReconcileAI Sync — Direction: {direction}")
    print("=" * 55)

    if direction in ("to-deploy", "both"):
        print("\n  ROOT → DEPLOY:")
        n1 = sync_root_files("to-deploy")
        n2 = sync_root_dirs("to-deploy")
        print(f"\n  BACKEND → DEPLOY/BACKEND:")
        n3 = sync_backend(BACKEND, os.path.join(DEPLOY, "backend"), "to-deploy")
        print(f"\n  Synced: {n1} files + {n2} content files + {n3} backend files")

    if direction in ("from-deploy", "both"):
        print("\n  DEPLOY → ROOT:")
        n1 = sync_root_files("from-deploy")
        n2 = sync_root_dirs("from-deploy")
        print(f"\n  DEPLOY/BACKEND → BACKEND:")
        n3 = sync_backend(BACKEND, os.path.join(DEPLOY, "backend"), "from-deploy")
        print(f"\n  Synced: {n1} files + {n2} content files + {n3} backend files")

    print(f"\n{'=' * 55}")
    print(f"  SYNC COMPLETE! ✅")
    print(f"{'=' * 55}")
    print()
    print("  NEXT STEPS:")
    print("  1. cd deploy && git add . && git commit -m 'your message'")
    print("  2. git push origin main")
    print("  3. Deploy on Deplexo!")

if __name__ == "__main__":
    main()
