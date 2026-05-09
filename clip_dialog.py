"""クリップ機能のダイアログ."""

import logging
import math
import tkinter as tk
from pathlib import Path
from typing import Optional, Tuple

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk

# ロガー設定
logger = logging.getLogger(__name__)


class ClipDialog(ctk.CTkToplevel):
    """画像をクリップして保存するダイアログクラス."""

    # クロップモード定数
    MODE_RECTANGLE: str = "rectangle"
    MODE_CIRCLE: str = "circle"

    def __init__(self, parent: ctk.CTk, image: Image.Image):
        super().__init__(parent)
        self._parent = parent
        self._original_image = image
        self._selected_region: Optional[Tuple[int, int, int, int]] = None
        self._crop_mode: str = self.MODE_RECTANGLE  # デフォルトは矩形モード

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

        # モード切り替えフレーム
        mode_frame = ctk.CTkFrame(self)
        mode_frame.pack(pady=(5, 10))

        mode_label = ctk.CTkLabel(
            mode_frame,
            text="クロップモード:",
            font=("Helvetica", 12),
        )
        mode_label.pack(side=tk.LEFT, padx=(10, 5))

        # モード切り替えラジオボタン
        self._mode_var = tk.StringVar(value=self.MODE_RECTANGLE)

        rect_radio = ctk.CTkRadioButton(
            mode_frame,
            text="矩形",
            variable=self._mode_var,
            value=self.MODE_RECTANGLE,
            command=self._on_mode_change,
        )
        rect_radio.pack(side=tk.LEFT, padx=5)

        circle_radio = ctk.CTkRadioButton(
            mode_frame,
            text="円形",
            variable=self._mode_var,
            value=self.MODE_CIRCLE,
            command=self._on_mode_change,
        )
        circle_radio.pack(side=tk.LEFT, padx=5)

        # 選択領域表示ラベル
        self.region_label = ctk.CTkLabel(
            self,
            text="選択領域: 未選択",
            font=("Helvetica", 12),
        )
        self.region_label.pack(pady=(0, 10))

    def _on_mode_change(self) -> None:
        """モード変更時の処理を行う."""
        self._crop_mode = self._mode_var.get()
        logger.debug("Crop mode changed to: %s", self._crop_mode)
        # 選択領域をリセット
        self._selected_region = None
        self.region_label.configure(text="選択領域: 未選択")
        self.clip_button.configure(state=tk.DISABLED)
        # キャンバス上の選択描画をクリア
        if self._selection_rect is not None:
            self.canvas.delete(self._selection_rect)
            self._selection_rect = None

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

        # 既存の選択描画を削除
        if self._selection_rect is not None:
            self.canvas.delete(self._selection_rect)

        if self._crop_mode == self.MODE_RECTANGLE:
            # 新しい選択矩形を作成
            self._selection_rect = self.canvas.create_rectangle(
                event.x, event.y, event.x, event.y,
                outline="#00FF00",
                width=2,
                dash=(4, 4),
            )
        else:  # MODE_CIRCLE
            # 新しい選択円を作成（中心点から開始）
            self._selection_rect = self.canvas.create_oval(
                event.x, event.y, event.x, event.y,
                outline="#00FF00",
                width=2,
                dash=(4, 4),
                fill="",
            )

    def _on_mouse_drag(self, event: tk.Event) -> None:
        """マウスドラッグイベントを処理する."""
        if self._selection_rect is not None:
            if self._crop_mode == self.MODE_RECTANGLE:
                # 矩形モード: 通常のリクタングル描画
                self.canvas.coords(
                    self._selection_rect,
                    self._drag_start_x,
                    self._drag_start_y,
                    event.x,
                    event.y,
                )
            else:  # MODE_CIRCLE
                # 円形モード: 中心からドラッグ位置までの距離を半径とする円を描画
                center_x = self._drag_start_x
                center_y = self._drag_start_y
                radius = math.sqrt((event.x - center_x) ** 2 + (event.y - center_y) ** 2)
                self.canvas.coords(
                    self._selection_rect,
                    center_x - radius, center_y - radius,
                    center_x + radius, center_y + radius,
                )

    def _on_mouse_release(self, event: tk.Event) -> None:
        """マウスリリースイベントを処理する."""
        if self._crop_mode == self.MODE_RECTANGLE:
            self._on_mouse_release_rectangle(event)
        else:  # MODE_CIRCLE
            self._on_mouse_release_circle(event)

    def _on_mouse_release_rectangle(self, event: tk.Event) -> None:
        """矩形モードでマウスリリースされたときの処理を行う."""
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

    def _on_mouse_release_circle(self, event: tk.Event) -> None:
        """円形モードでマウスリリースされたときの処理を行う."""
        # 中心座標と半径を計算
        center_x = self._drag_start_x
        center_y = self._drag_start_y
        radius = math.sqrt((event.x - center_x) ** 2 + (event.y - center_y) ** 2)

        # 半径が有効か確認
        if radius < 3:
            return

        # 表示画像の座標から元画像の座標に変換
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        canvas_center_x = canvas_width // 2
        canvas_center_y = canvas_height // 2

        img = self._original_image
        display_img_width = self._photo_image.width()
        display_img_height = self._photo_image.height()

        img_start_x = canvas_center_x - display_img_width // 2
        img_start_y = canvas_center_y - display_img_height // 2

        # 表示座標を元画像座標に変換
        ratio_x = img.width / display_img_width
        ratio_y = img.height / display_img_height

        # 中心座標を元画像座標に変換
        orig_center_x = int((center_x - img_start_x) * ratio_x)
        orig_center_y = int((center_y - img_start_y) * ratio_y)
        orig_radius_x = int(radius * ratio_x)
        orig_radius_y = int(radius * ratio_y)

        # 円の外接矩形をselected_regionに保存（円形モード識別用）
        # 負の値を-1に設定して矩形モードと区別
        self._selected_region = (orig_center_x, orig_center_y, orig_radius_x, orig_radius_y)
        self.region_label.configure(
            text=f"円選択: 中心({orig_center_x}, {orig_center_y}) "
                f"半径: {orig_radius_x}x{orig_radius_y}"
        )
        self.clip_button.configure(state=tk.NORMAL)

        # 選択円のスタイルを変更
        self.canvas.itemconfig(self._selection_rect, outline="#00FF00", dash=())

    def _clip_and_save(self) -> None:
        """選択領域をクリップして保存ダイアログを表示する."""
        if self._selected_region is None:
            return

        if self._crop_mode == self.MODE_CIRCLE:
            clipped_image = self._clip_circle()
        else:
            clipped_image = self._clip_rectangle()

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

    def _clip_rectangle(self) -> Image.Image:
        """矩形領域をクリップする."""
        x1, y1, x2, y2 = self._selected_region
        return self._original_image.crop((x1, y1, x2, y2))

    def _clip_circle(self) -> Image.Image:
        """円形領域をクリップし、円外を透過にする."""
        center_x, center_y, radius_x, radius_y = self._selected_region
        img = self._original_image

        # 円の外接矩形を計算
        x1 = max(0, center_x - radius_x)
        y1 = max(0, center_y - radius_y)
        x2 = min(img.width, center_x + radius_x)
        y2 = min(img.height, center_y + radius_y)

        # 外接矩形領域を切り出す
        cropped = img.crop((x1, y1, x2, y2))

        # RGBAに変換（アルファチャンネルを確保）
        if cropped.mode != "RGBA":
            cropped = cropped.convert("RGBA")

        # マスク画像を作成（円内は255、円外は0）
        mask = Image.new("L", cropped.size, 0)
        draw = ImageDraw.Draw(mask)

        # 円の中心座標をクリップ済み画像の座標系に変換
        local_center_x = center_x - x1
        local_center_y = center_y - y1

        # 円を描画
        draw.ellipse(
            [
                (local_center_x - radius_x, local_center_y - radius_y),
                (local_center_x + radius_x, local_center_y + radius_y),
            ],
            fill=255,
        )

        # マスクを適用して円外を透過にする
        cropped.putalpha(mask)

        return cropped
