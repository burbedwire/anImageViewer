"""画像ビューワーアプリケーションのエントリポイント."""

import sys
import logging

from app import ImageViewerApp

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def main():
    """アプリケーションを起動する."""
    app = ImageViewerApp()
    app.mainloop()


if __name__ == "__main__":
    main()