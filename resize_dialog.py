"""解像度変換機能のダイアログ."""

import logging
import tkinter as tk
from pathlib import Path
from typing import Optional

import customtkinter as ctk
from PIL import Image

# ロガー設定
logger = logging.getLogger(__name__)


class ResizeDialog(ctk.CTkToplevel):
    """画像の解像度を変更して保存するダイアログクラス."""

    def __init__(self, parent: ctk.CTk, image: Image.Image, image_path: Optional[Path] = None):
        super().__init__(parent)
        self._parent = parent
        self._original_image = image
        self._original_path = image_path
        self._original_width = image.width
        self._original_height = image.height

        self._setup_window()
        self._setup_ui()

        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def _setup_window(self) -> None:
        """ウィンドウ設定を行う."""
        self.title("解像度変換")
        self.geometry("500x400")
        self.resizable(False, False)

    def _setup_ui(self) -> None:
        """UIコンポーネントを設定する."""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 元画像情報
        info_label = ctk.CTkLabel(
            main_frame,
            text=f"元画像: {self._original_width} x {self._original_height}",
            font=("Helvetica", 12),
        )
        info_label.pack(pady=(0, 15))

        # 変換モード選択
        mode_frame = ctk.CTkFrame(main_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(mode_frame, text="変換モード:", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=(0, 10))

        self.mode_var = tk.StringVar(value="ratio")
        ctk.CTkRadioButton(
            mode_frame,
            text="比率指定",
            variable=self.mode_var,
            value="ratio",
            command=self._on_mode_change,
        ).pack(side=tk.LEFT, padx=5)
        ctk.CTkRadioButton(
            mode_frame,
            text="幅(px)指定",
            variable=self.mode_var,
            value="width",
            command=self._on_mode_change,
        ).pack(side=tk.LEFT, padx=5)
        ctk.CTkRadioButton(
            mode_frame,
            text="高さ(px)指定",
            variable=self.mode_var,
            value="height",
            command=self._on_mode_change,
        ).pack(side=tk.LEFT, padx=5)

        # 比率指定フレーム
        self.ratio_frame = ctk.CTkFrame(main_frame)
        self.ratio_frame.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(self.ratio_frame, text="比率 (%):", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=(0, 10))
        self.ratio_entry = ctk.CTkEntry(self.ratio_frame, width=100)
        self.ratio_entry.pack(side=tk.LEFT, padx=5)
        self.ratio_entry.insert(0, "100")

        # 幅指定フレーム
        self.width_frame = ctk.CTkFrame(main_frame)
        self.width_frame.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(self.width_frame, text="幅 (px):", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=(0, 10))
        self.width_entry = ctk.CTkEntry(self.width_frame, width=100)
        self.width_entry.pack(side=tk.LEFT, padx=5)
        self.width_entry.insert(0, str(self._original_width))

        # 高さ指定フレーム
        self.height_frame = ctk.CTkFrame(main_frame)
        self.height_frame.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(self.height_frame, text="高さ (px):", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=(0, 10))
        self.height_entry = ctk.CTkEntry(self.height_frame, width=100)
        self.height_entry.pack(side=tk.LEFT, padx=5)
        self.height_entry.insert(0, str(self._original_height))

        # 予測サイズ表示
        self.preview_label = ctk.CTkLabel(
            main_frame,
            text=f"予測サイズ: {self._original_width} x {self._original_height}",
            font=("Helvetica", 12),
        )
        self.preview_label.pack(pady=(10, 15))

        # 保存形式選択
        format_frame = ctk.CTkFrame(main_frame)
        format_frame.pack(fill=tk.X, pady=(0, 10))

        ctk.CTkLabel(format_frame, text="保存形式:", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=(0, 10))

        self.format_var = tk.StringVar(value="jpg")
        ctk.CTkRadioButton(
            format_frame,
            text="JPG",
            variable=self.format_var,
            value="jpg",
            command=self._on_format_change,
        ).pack(side=tk.LEFT, padx=5)
        ctk.CTkRadioButton(
            format_frame,
            text="PNG",
            variable=self.format_var,
            value="png",
            command=self._on_format_change,
        ).pack(side=tk.LEFT, padx=5)

        # JPG quality設定フレーム
        self.quality_frame = ctk.CTkFrame(main_frame)
        self.quality_frame.pack(fill=tk.X, pady=(0, 15))

        ctk.CTkLabel(self.quality_frame, text="JPG Quality (1-100):", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=(0, 10))
        self.quality_slider = ctk.CTkSlider(self.quality_frame, from_=1, to=100, command=self._update_quality_label)
        self.quality_slider.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.quality_slider.set(95)
        self.quality_label = ctk.CTkLabel(self.quality_frame, text="95", width=30, font=("Helvetica", 12))
        self.quality_label.pack(side=tk.LEFT, padx=5)

        # ボタンフレーム
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        self.save_button = ctk.CTkButton(
            button_frame,
            text="変換して保存",
            command=self._resize_and_save,
        )
        self.save_button.pack(side=tk.LEFT, padx=(0, 10))

        cancel_button = ctk.CTkButton(
            button_frame,
            text="キャンセル",
            command=self.destroy,
        )
        cancel_button.pack(side=tk.LEFT)

        # 初期表示
        self._on_mode_change()

    def _set_frame_widgets_state(self, frame: ctk.CTkFrame, state: str) -> None:
        """
        フレーム内の全ウィジェットの状態を切り替える。

        Args:
            frame: 対象フレーム。
            state: "normal" または "disabled"。
        """
        for widget in frame.winfo_children():
            if hasattr(widget, "configure"):
                try:
                    widget.configure(state=state)
                except (tk.TclError, ValueError):
                    pass  # stateをサポートしないウィジェットは無視

    def _on_mode_change(self) -> None:
        """変換モード変更時の処理."""
        mode = self.mode_var.get()
        self._set_frame_widgets_state(self.ratio_frame, "normal" if mode == "ratio" else "disabled")
        self._set_frame_widgets_state(self.width_frame, "normal" if mode == "width" else "disabled")
        self._set_frame_widgets_state(self.height_frame, "normal" if mode == "height" else "disabled")
        self._update_preview()

    def _on_format_change(self) -> None:
        """保存形式変更時の処理."""
        fmt = self.format_var.get()
        if fmt == "jpg":
            self._set_frame_widgets_state(self.quality_frame, "normal")
        else:
            self._set_frame_widgets_state(self.quality_frame, "disabled")

    def _update_quality_label(self, value: float) -> None:
        """qualityラベルを更新する."""
        self.quality_label.configure(text=str(int(value)))

    def _calculate_new_size(self) -> tuple[int, int]:
        """
        新しいサイズを計算する。

        Returns:
            (width, height)のタプル。
        """
        mode = self.mode_var.get()

        try:
            if mode == "ratio":
                ratio = float(self.ratio_entry.get()) / 100.0
                if ratio <= 0:
                    raise ValueError("比率は0より大きい値を指定してください")
                new_width = max(1, int(self._original_width * ratio))
                new_height = max(1, int(self._original_height * ratio))
            elif mode == "width":
                new_width = int(self.width_entry.get())
                if new_width <= 0:
                    raise ValueError("幅は1以上の値を指定してください")
                ratio = new_width / self._original_width
                new_height = max(1, int(self._original_height * ratio))
            else:  # height
                new_height = int(self.height_entry.get())
                if new_height <= 0:
                    raise ValueError("高さは1以上の値を指定してください")
                ratio = new_height / self._original_height
                new_width = max(1, int(self._original_width * ratio))
        except ValueError as e:
            if str(e) == "invalid literal for int() with base 10: ''":
                raise ValueError("有効な数値を入力してください")
            raise

        return new_width, new_height

    def _update_preview(self) -> None:
        """予測サイズを更新する."""
        try:
            new_width, new_height = self._calculate_new_size()
            self.preview_label.configure(text=f"予測サイズ: {new_width} x {new_height}")
            self.preview_label.configure(fg_color=None, text_color="white")
        except ValueError as e:
            self.preview_label.configure(text=f"エラー: {e}")
            self.preview_label.configure(text_color="red")

    def _resize_and_save(self) -> None:
        """画像をリサイズして保存する."""
        try:
            new_width, new_height = self._calculate_new_size()
        except ValueError as e:
            ctk.messagebox.show_error("エラー", str(e))
            return

        # リサイズ
        resized_image = self._original_image.resize((new_width, new_height), Image.LANCZOS)

        # 保存ダイアログ
        default_name = self._original_path.stem if self._original_path else "image"
        file_path = ctk.filedialog.asksaveasfilename(
            title="変換済み画像を保存",
            defaultextension=f".{self.format_var.get()}",
            initialfile=default_name,
            filetypes=[
                ("PNGファイル", "*.png") if self.format_var.get() == "png" else ("JPGファイル", "*.jpg"),
                ("すべて", "*.*"),
            ],
        )

        if not file_path:
            return

        try:
            path = Path(file_path)
            quality = int(self.quality_slider.get())

            if path.suffix.lower() in (".jpg", ".jpeg"):
                # JPGはRGBに変換
                if resized_image.mode in ("RGBA", "LA"):
                    background = Image.new("RGB", resized_image.size, (255, 255, 255))
                    background.paste(resized_image, mask=resized_image.split()[-1])
                    resized_image = background
                elif resized_image.mode != "RGB":
                    resized_image = resized_image.convert("RGB")
                resized_image.save(path, "JPEG", quality=quality)
            else:
                resized_image.save(path, "PNG")

            logger.info("Resized image saved to %s (%dx%d, quality=%d)", path, new_width, new_height, quality)
            self.destroy()
        except Exception as e:
            logger.error("Failed to save resized image: %s", e)
            ctk.messagebox.show_error("エラー", f"保存に失敗しました:\n{e}")