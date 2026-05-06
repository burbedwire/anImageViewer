"""透過色指定機能のダイアログ."""

import logging
import time
import tkinter as tk
from pathlib import Path
from typing import Optional, Tuple

import customtkinter as ctk
from PIL import Image, ImageTk

# ロガー設定
logger = logging.getLogger(__name__)


class TransparencyDialog(ctk.CTkToplevel):
    """画像の透過色を指定して保存するダイアログクラス."""

    def __init__(self, parent: ctk.CTk, image: Image.Image, image_path: Optional[Path] = None):
        super().__init__(parent)
        self._parent = parent
        self._original_image = image.convert("RGBA") if image.mode != "RGBA" else image.copy()
        self._original_path = image_path
        self._background_color: Optional[Tuple[int, int, int]] = None
        self._tolerance: int = 30
        self._mask_image: Optional[Image.Image] = None
        self._is_blinking: bool = False
        self._blink_state: bool = False

        self._setup_window()
        self._setup_ui()
        self._setup_canvas()
        self._display_image()

        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def _setup_window(self) -> None:
        """ウィンドウ設定を行う."""
        self.title("透過色指定")
        self.geometry("800x600")
        self.resizable(True, True)

    def _setup_ui(self) -> None:
        """UIコンポーネントを設定する."""
        # 説明ラベル
        info_label = ctk.CTkLabel(
            self,
            text="画像をクリックして背景色を選択してください（許容範囲: 0-100）",
            font=("Helvetica", 12),
        )
        info_label.pack(pady=(10, 5))

        # 設定フレーム
        setting_frame = ctk.CTkFrame(self)
        setting_frame.pack(fill=tk.X, padx=10, pady=5)

        # 許容範囲スライダー
        ctk.CTkLabel(
            setting_frame,
            text="許容範囲:",
            font=("Helvetica", 12),
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.tolerance_slider = ctk.CTkSlider(
            setting_frame,
            from_=0,
            to=100,
            command=self._on_tolerance_change,
        )
        self.tolerance_slider.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.tolerance_slider.set(self._tolerance)

        self.tolerance_label = ctk.CTkLabel(
            setting_frame,
            text=str(self._tolerance),
            width=30,
            font=("Helvetica", 12),
        )
        self.tolerance_label.pack(side=tk.LEFT, padx=5)

        # 背景色表示
        self.color_label = ctk.CTkLabel(
            setting_frame,
            text="背景色: 未選択",
            font=("Helvetica", 12),
        )
        self.color_label.pack(side=tk.LEFT, padx=(20, 5))

        # 背景色プレビュー
        self.color_preview = ctk.CTkFrame(setting_frame, width=30, height=30)
        self.color_preview.pack(side=tk.LEFT, padx=5)

        # ボタンフレーム
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=(5, 10))

        self.save_button = ctk.CTkButton(
            button_frame,
            text="透過して保存(PNG)",
            command=self._save_transparent,
            state=tk.DISABLED,
        )
        self.save_button.pack(side=tk.LEFT, padx=(0, 10))

        self.preview_button = ctk.CTkButton(
            button_frame,
            text="マスクプレビュー",
            command=self._toggle_preview,
            state=tk.DISABLED,
        )
        self.preview_button.pack(side=tk.LEFT, padx=(0, 10))

        cancel_button = ctk.CTkButton(
            button_frame,
            text="キャンセル",
            command=self.destroy,
        )
        cancel_button.pack(side=tk.LEFT)

    def _setup_canvas(self) -> None:
        """キャンバスを設定する."""
        canvas_frame = ctk.CTkFrame(self)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # スクロールバー付きのキャンバス
        canvas_inner = ctk.CTkFrame(canvas_frame)

        h_scroll = ctk.CTkScrollbar(canvas_frame, orientation="horizontal")
        v_scroll = ctk.CTkScrollbar(canvas_frame, orientation="vertical")

        self.canvas = tk.Canvas(
            canvas_frame,
            bg="#2b2b2b",
            highlightthickness=0,
            cursor="cross",
            xscrollcommand=h_scroll.set,
            yscrollcommand=v_scroll.set,
        )
        h_scroll.configure(command=self.canvas.xview)
        v_scroll.configure(command=self.canvas.yview)

        # gridレイアウト
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        # マウスイベントバインド（背景色選択用）
        self.canvas.bind("<ButtonPress-1>", self._on_canvas_click)
        
        # マウスホイールでスクロール
        self.canvas.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

    def _display_image(self) -> None:
        """画像をキャンバスに1:1で表示する."""
        self.canvas.delete("all")

        img = self._original_image
        
        # 画像を1:1で表示（縮小しない）
        self._photo_image = ImageTk.PhotoImage(img)
        self._display_ratio_x = 1.0
        self._display_ratio_y = 1.0

        # キャンバスのスクロール領域を画像サイズに設定
        self.canvas.configure(scrollregion=(0, 0, img.width, img.height))
        
        # 画像を(0, 0)に配置
        self.canvas.create_image(0, 0, image=self._photo_image, anchor=tk.NW)
        
        # 中央にスクロール
        self.canvas.scan_mark(0, 0)

    def _on_canvas_click(self, event: tk.Event) -> None:
        """キャンバスクリックイベントを処理して背景色を選択する."""
        # スクロール位置を取得
        scroll_x = self.canvas.xview()[0] * self._original_image.width
        scroll_y = self.canvas.yview()[0] * self._original_image.height
        
        # クリック位置を画像座標に変換
        pix_x = int(event.x + scroll_x)
        pix_y = int(event.y + scroll_y)
        
        # 画像範囲内か確認
        if not (0 <= pix_x < self._original_image.width and 0 <= pix_y < self._original_image.height):
            return
        
        pix_x = max(0, min(pix_x, self._original_image.width - 1))
        pix_y = max(0, min(pix_y, self._original_image.height - 1))

        # 画素色を取得
        pixel = self._original_image.getpixel((pix_x, pix_y))
        if isinstance(pixel, tuple):
            self._background_color = (pixel[0], pixel[1], pixel[2])
        else:
            self._background_color = (pixel, pixel, pixel)

        # UI更新
        r, g, b = self._background_color
        self.color_label.configure(text=f"背景色: RGB({r}, {g}, {b})")
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        self.color_preview.configure(fg_color=hex_color)
        self.save_button.configure(state=tk.NORMAL)
        self.preview_button.configure(state=tk.NORMAL)

        # マスクを計算
        self._calculate_mask()

        logger.info("Background color selected: RGB(%d, %d, %d)", r, g, b)

    def _on_tolerance_change(self, value: float) -> None:
        """許容範囲変更時の処理."""
        self._tolerance = int(value)
        self.tolerance_label.configure(text=str(self._tolerance))

        # 背景色が選択されている場合はマスクを再計算
        if self._background_color is not None:
            self._calculate_mask()

    def _calculate_mask(self) -> None:
        """透過マスクを計算する."""
        if self._background_color is None:
            return

        r_bg, g_bg, b_bg = self._background_color
        img = self._original_image
        pixels = img.load()

        # マスク画像を作成（白色=非透過、黒色=透過）
        self._mask_image = Image.new("L", img.size, 255)
        mask_pixels = self._mask_image.load()

        for y in range(img.height):
            for x in range(img.width):
                pixel = pixels[(x, y)]
                r, g, b = pixel[0], pixel[1], pixel[2]

                # 色距離を計算（ユークリッド距離）
                distance = ((r - r_bg) ** 2 + (g - g_bg) ** 2 + (b - b_bg) ** 2) ** 0.5

                # 許容範囲内なら透過（黒）
                if distance <= self._tolerance * 4.42:  # 255/sqrt(3) ≈ 148 * 3 ≈ 442 / 100
                    mask_pixels[(x, y)] = 0
                else:
                    mask_pixels[(x, y)] = 255

    def _toggle_preview(self) -> None:
        """マスクプレビューをトグルする."""
        if self._mask_image is None:
            return

        if not self._is_blinking:
            self._is_blinking = True
            self._blink_mask_overlay()
        else:
            self._is_blinking = False
            self._display_image()  # 元画像に戻す

    def _blink_mask_overlay(self) -> None:
        """マスクオーバーレイを点滅表示する."""
        if not self._is_blinking:
            return

        if self._blink_state:
            # マスクオーバーレイ表示
            self._show_mask_overlay()
        else:
            # 元画像表示
            self._display_image()

        self._blink_state = not self._blink_state
        self.after(500, self._blink_mask_overlay)

    def _show_mask_overlay(self) -> None:
        """マスクオーバーレイを表示する."""
        self.canvas.delete("all")

        img = self._original_image
        
        # 表示比率を1:1に
        self._display_ratio_x = 1.0
        self._display_ratio_y = 1.0

        # マスクを適用したオーバーレイ画像を作成
        if self._mask_image:
            # 透過領域を赤でオーバーレイ
            display_img_rgba = img.copy()
            overlay = Image.new("RGBA", img.size, (255, 0, 0, 150))
            # マスクが0（透過）の場所に赤を合成（マスクを反転）
            inverted_mask = Image.eval(self._mask_image, lambda p: 255 - p)
            compositable = Image.new("RGBA", img.size, (0, 0, 0, 0))
            compositable.paste(overlay, mask=inverted_mask)
            display_img_rgba = Image.alpha_composite(display_img_rgba, compositable)
        else:
            display_img_rgba = img

        photo = ImageTk.PhotoImage(display_img_rgba)
        self.canvas.configure(scrollregion=(0, 0, img.width, img.height))
        self.canvas.create_image(0, 0, image=photo, anchor=tk.NW)
        self._photo_image = photo  # 参照保持

    def _save_transparent(self) -> None:
        """透過画像をPNGとして保存する."""
        if self._mask_image is None or self._background_color is None:
            return

        # 透過処理を適用
        result_image = self._original_image.copy()
        result_pixels = result_image.load()
        mask_pixels = self._mask_image.load()

        for y in range(self._original_image.height):
            for x in range(self._original_image.width):
                if mask_pixels[(x, y)] == 0:
                    # 透過にする
                    result_pixels[(x, y)] = (0, 0, 0, 0)

        # 保存ダイアログ
        default_name = self._original_path.stem if self._original_path else "image"
        file_path = ctk.filedialog.asksaveasfilename(
            title="透過画像を保存",
            defaultextension=".png",
            initialfile=default_name,
            filetypes=[
                ("PNGファイル", "*.png"),
                ("すべて", "*.*"),
            ],
        )

        if not file_path:
            return

        try:
            path = Path(file_path)
            result_image.save(path, "PNG")
            logger.info("Transparent image saved to %s", path)
            self.destroy()
        except Exception as e:
            logger.error("Failed to save transparent image: %s", e)
            ctk.messagebox.show_error("エラー", f"保存に失敗しました:\n{e}")

    def destroy(self) -> None:
        """ダイアログを閉じる."""
        self._is_blinking = False
        super().destroy()