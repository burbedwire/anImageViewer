"""クリップ機能のダイアログ."""

import logging
import tkinter as tk
from pathlib import Path
from typing import Optional, Tuple

import customtkinter as ctk
from PIL import Image, ImageTk

# ロガー設定
logger = logging.getLogger(__name__)


class ClipDialog(ctk.CTkToplevel):
    """画像をクリップして保存するダイアログクラス."""

    def __init__(self, parent: ctk.CTk, image: Image.Image):
        super().__init__(parent)
        self._parent = parent
        self._original_image = image
        self._selected_region: Optional[Tuple[int, int, int, int]] = None

        self._setup_window()
        self._setup_ui()
        self._setup_canvas()
        self._display_image()

        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def _setup_window(self) -> None:
        """ウィンドウ設定を行う."""
        self.title("クリップ")
        self.geometry("800x600")
        self.resizable(True, True)

    def _setup_ui(self) -> None:
        """UIコンポーネントを設定する."""
        # 説明ラベル
        info_label = ctk.CTkLabel(
            self,
            text="クリップする領域をドラッグで選択してください",
            font=("Helvetica", 12),
        )
        info_label.pack(pady=(10, 5))

        # 選択領域表示ラベル
        self.region_label = ctk.CTkLabel(
            self,
            text="選択領域: 未選択",
            font=("Helvetica", 12),
        )
        self.region_label.pack(pady=(0, 10))

    def _setup_canvas(self) -> None:
        """キャンバスを設定する."""
        canvas_frame = ctk.CTkFrame(self)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(
            canvas_frame,
            bg="#2b2b2b",
            highlightthickness=0,
            cursor="cross",
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # ドラッグ選択用変数
        self._drag_start_x: int = 0
        self._drag_start_y: int = 0
        self._selection_rect: Optional[int] = None

        # マウスイベントバインド
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_press)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_release)

        # 確定ボタン
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.clip_button = ctk.CTkButton(
            button_frame,
            text="クリップして保存",
            command=self._clip_and_save,
            state=tk.DISABLED,
        )
        self.clip_button.pack(side=tk.LEFT, padx=(0, 10))

        cancel_button = ctk.CTkButton(
            button_frame,
            text="キャンセル",
            command=self.destroy,
        )
        cancel_button.pack(side=tk.LEFT)

    def _display_image(self) -> None:
        """画像をキャンバスに表示する."""
        self.canvas.delete("all")

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width < 10 or canvas_height < 10:
            # ウィンドウがまだ十分に描画されていない場合はデフォルト値を使用
            canvas_width = 800
            canvas_height = 500

        img = self._original_image
        if img.width > canvas_width or img.height > canvas_height:
            ratio = min(canvas_width / img.width, canvas_height / img.height)
            new_width = max(1, int(img.width * ratio))
            new_height = max(1, int(img.height * ratio))
            display_img = img.resize((new_width, new_height), Image.LANCZOS)
        else:
            display_img = img

        self._photo_image = ImageTk.PhotoImage(display_img)
        self._display_ratio = min(img.width / display_img.width, img.height / display_img.height) if display_img.width > 0 and display_img.height > 0 else 1

        center_x = canvas_width // 2
        center_y = canvas_height // 2
        self.canvas.create_image(center_x, center_y, image=self._photo_image, anchor=tk.CENTER)

    def _on_mouse_press(self, event: tk.Event) -> None:
        """マウス押下イベントを処理する."""
        self._drag_start_x = event.x
        self._drag_start_y = event.y

        # 既存の選択矩形を削除
        if self._selection_rect is not None:
            self.canvas.delete(self._selection_rect)

        # 新しい選択矩形を作成
        self._selection_rect = self.canvas.create_rectangle(
            event.x, event.y, event.x, event.y,
            outline="#00FF00",
            width=2,
            dash=(4, 4),
        )

    def _on_mouse_drag(self, event: tk.Event) -> None:
        """マウスドラッグイベントを処理する."""
        if self._selection_rect is not None:
            self.canvas.coords(
                self._selection_rect,
                self._drag_start_x,
                self._drag_start_y,
                event.x,
                event.y,
            )

    def _on_mouse_release(self, event: tk.Event) -> None:
        """マウスリリースイベントを処理する."""
        x1 = min(self._drag_start_x, event.x)
        y1 = min(self._drag_start_y, event.y)
        x2 = max(self._drag_start_x, event.x)
        y2 = max(self._drag_start_y, event.y)

        # 選択領域のサイズが有効か確認
        if x2 - x1 < 5 or y2 - y1 < 5:
            return

        # 表示画像の座標から元画像の座標に変換
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        center_x = canvas_width // 2
        center_y = canvas_height // 2

        img = self._original_image
        display_img_width = self._photo_image.width()
        display_img_height = self._photo_image.height()

        img_start_x = center_x - display_img_width // 2
        img_start_y = center_y - display_img_height // 2

        # 表示座標を元画像座標に変換
        ratio_x = img.width / display_img_width
        ratio_y = img.height / display_img_height

        orig_x1 = int(max(0, (x1 - img_start_x) * ratio_x))
        orig_y1 = int(max(0, (y1 - img_start_y) * ratio_y))
        orig_x2 = int(min(img.width, (x2 - img_start_x) * ratio_x))
        orig_y2 = int(min(img.height, (y2 - img_start_y) * ratio_y))

        self._selected_region = (orig_x1, orig_y1, orig_x2, orig_y2)
        self.region_label.configure(
            text=f"選択領域: ({orig_x1}, {orig_y1}) - ({orig_x2}, {orig_y2}) "
                f"サイズ: {orig_x2 - orig_x1}x{orig_y2 - orig_y1}"
        )
        self.clip_button.configure(state=tk.NORMAL)

        # 選択矩形のスタイルを変更
        self.canvas.itemconfig(self._selection_rect, outline="#00FF00", dash=())

    def _clip_and_save(self) -> None:
        """選択領域をクリップして保存ダイアログを表示する."""
        if self._selected_region is None:
            return

        x1, y1, x2, y2 = self._selected_region
        clipped_image = self._original_image.crop((x1, y1, x2, y2))

        # 保存ダイアログ
        file_path = ctk.filedialog.asksaveasfilename(
            title="クリップ画像を保存",
            defaultextension=".png",
            filetypes=[
                ("PNGファイル", "*.png"),
                ("JPGファイル", "*.jpg"),
            ],
        )

        if not file_path:
            return

        try:
            path = Path(file_path)
            if path.suffix.lower() == ".jpg":
                # JPGはRGBに変換が必要
                if clipped_image.mode == "RGBA":
                    background = Image.new("RGB", clipped_image.size, (255, 255, 255))
                    background.paste(clipped_image, mask=clipped_image.split()[3])
                    clipped_image = background
                elif clipped_image.mode != "RGB":
                    clipped_image = clipped_image.convert("RGB")
                clipped_image.save(path, "JPEG", quality=95)
            else:
                clipped_image.save(path, "PNG")

            logger.info("Clipped image saved to %s", path)
            self.destroy()
        except Exception as e:
            logger.error("Failed to save clipped image: %s", e)
            ctk.messagebox.show_error("エラー", f"保存に失敗しました:\n{e}")