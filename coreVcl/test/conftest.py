"""pytest 共用設定：讓測試能 import coreVcl 底下的套件（auth、modules）"""
import sys
from pathlib import Path

# 相當於把 coreVcl 加進 PYTHONPATH，不論從哪個目錄執行 pytest 都能 import
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
