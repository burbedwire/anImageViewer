"""一括変換機能のダイアログ."""

import logging
import tkinter as tk
from pathlib import Path
from typing import List, Optional
from tkinter import messagebox

import customtkinter as ctk
from PIL import Image

# ロガー設定
logger = logging.getLogger(__name__)

# サポートする画像拡張子
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}


class BatchConvertDialog(ctk.CTkToplevel):
    """複数の画像を一括変換するダイアログクラス."""

    def __init__(self, parent: ctk.CTk):
        super().__init__(parent)
        self._parent = parent
        self._selected_files: List[Path] = []
        self._output_dir: Optional[Path] = None

        self._setup_window()
        self._setup_ui()

        self.transient(parent)
        self.grab_set()
        parent.wait_window(self)

    def _setup_window(self) -> None:
        """ウィンドウ設定を行う."""
        self.title("一括変換")
        self.geometry("650x650")
        self.resizable(False, False)

    def _setup_ui(self) -> None:
        """UIコンポーネントを設定する."""
        # スクロール可能なフレームを作成
        main_canvas = ctk.CTkCanvas(self, highlightthickness=0)
        scrollbar = ctk.CTkScrollbar(self, orientation="vertical", command=main_canvas.yview)
        scrollable_frame = ctk.CTkFrame(main_canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")),
        )

        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)

        main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # マウスホイールでスクロール
        main_canvas.bind_all("<MouseWheel>", lambda e: main_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        self._build_ui(scrollable_frame)

    def _build_ui(self, parent: ctk.CTkFrame) -> None:
        """
        UIコンポーネントを構築する。

        Args:
            parent: 親フレーム。
        """
        # 説明ラベル
        ctk.CTkLabel(
            parent,
            text="変換する画像を選択してください",
            font=("Helvetica", 14, "bold"),
        ).pack(pady=(15, 10))

        # ファイル選択ボタン
        file_frame = ctk.CTkFrame(parent)
        file_frame.pack(fill=tk.X, pady=(0, 10), padx=15)

        ctk.CTkButton(
            file_frame,
            text="画像を選択",
            command=self._select_files,
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.file_count_label = ctk.CTkLabel(
            file_frame,
            text="選択数: 0",
            font=("Helvetica", 12),
        )
        self.file_count_label.pack(side=tk.LEFT)

        # 選択ファイル表示リスト
        list_frame = ctk.CTkFrame(parent, height=120)
        list_frame.pack(fill=tk.BOTH, pady=(10, 10), padx=15)

        self.file_listbox = tk.Listbox(
            list_frame,
            font=("Helvetica", 12),
            bg="#3a3a3a",
            fg="white",
            selectmode=tk.EXTENDED,
            highlightthickness=0,
        )
        list_scrollbar = ctk.CTkScrollbar(list_frame, orientation="vertical", command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=list_scrollbar.set)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 出力フォルダ選択
        output_frame = ctk.CTkFrame(parent)
        output_frame.pack(fill=tk.X, pady=(10, 0), padx=15)

        ctk.CTkButton(
            output_frame,
            text="出力フォルダを選択",
            command=self._select_output_dir,
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.output_dir_label = ctk.CTkLabel(
            output_frame,
            text="出力フォルダ: 未選択",
            font=("Helvetica", 12),
        )
        self.output_dir_label.pack(side=tk.LEFT)

        # 解像度設定セクション
        self.resize_section_frame = ctk.CTkFrame(parent, fg_color="#2a2a2a")
        self.resize_section_frame.pack(fill=tk.X, pady=(15, 0), padx=15)

        # 解像度変更は常に有効
        self.resize_checkvar = tk.BooleanVar(value=True)

        # 解像度設定フレーム（常に表示）
        self.resize_setting_frame = ctk.CTkFrame(self.resize_section_frame)
        self.resize_setting_frame.pack(fill=tk.X, pady=(5, 10))

        # 変換モード選択
        mode_inner_frame = ctk.CTkFrame(self.resize_setting_frame)
        mode_inner_frame.pack(fill=tk.X, pady=(5, 5))

        ctk.CTkLabel(mode_inner_frame, text="モード:", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=(10, 10))

        self.mode_var = tk.StringVar(value="ratio")
        ctk.CTkRadioButton(
            mode_inner_frame,
            text="比率",
            variable=self.mode_var,
            value="ratio",
            command=self._on_mode_change,
        ).pack(side=tk.LEFT, padx=5)
        ctk.CTkRadioButton(
            mode_inner_frame,
            text="幅(px)",
            variable=self.mode_var,
            value="width",
            command=self._on_mode_change,
        ).pack(side=tk.LEFT, padx=5)
        ctk.CTkRadioButton(
            mode_inner_frame,
            text="高さ(px)",
            variable=self.mode_var,
            value="height",
            command=self._on_mode_change,
        ).pack(side=tk.LEFT, padx=5)

        # 比率入力
        self.ratio_input_frame = ctk.CTkFrame(self.resize_setting_frame)
        self.ratio_input_frame.pack(fill=tk.X, pady=(5, 5))

        ctk.CTkLabel(self.ratio_input_frame, text="比率 (%):", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=(10, 10))
        self.ratio_entry = ctk.CTkEntry(self.ratio_input_frame, width=120)
        self.ratio_entry.pack(side=tk.LEFT, padx=5)
        self.ratio_entry.insert(0, "100")

        # 幅入力
        self.width_input_frame = ctk.CTkFrame(self.resize_setting_frame)
        self.width_input_frame.pack(fill=tk.X, pady=(5, 5))

        ctk.CTkLabel(self.width_input_frame, text="幅 (px):", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=(10, 10))
        self.width_entry = ctk.CTkEntry(self.width_input_frame, width=120)
        self.width_entry.pack(side=tk.LEFT, padx=5)
        self.width_entry.insert(0, "1280")

        # 高さ入力
        self.height_input_frame = ctk.CTkFrame(self.resize_setting_frame)
        self.height_input_frame.pack(fill=tk.X, pady=(5, 5))

        ctk.CTkLabel(self.height_input_frame, text="高さ (px):", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=(10, 10))
        self.height_entry = ctk.CTkEntry(self.height_input_frame, width=120)
        self.height_entry.pack(side=tk.LEFT, padx=5)
        self.height_entry.insert(0, "720")

        # 初期状態：解像度変更を有効にして入力フレームを表示
        self._enable_widgets(self.resize_setting_frame, True)
        self._on_mode_change()

        # JPG quality設定
        quality_frame = ctk.CTkFrame(parent)
        quality_frame.pack(fill=tk.X, pady=(15, 0), padx=15)

        ctk.CTkLabel(quality_frame, text="JPG Quality:", font=("Helvetica", 12)).pack(side=tk.LEFT, padx=(10, 10))
        self.quality_slider = ctk.CTkSlider(quality_frame, from_=1, to=100, command=self._update_quality_label)
        self.quality_slider.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.quality_slider.set(95)
        self.quality_label = ctk.CTkLabel(quality_frame, text="95", width=30, font=("Helvetica", 12))
        self.quality_label.pack(side=tk.LEFT, padx=5)

        # プログレスバー
        self.progress = ctk.CTkProgressBar(parent)
        self.progress.pack(fill=tk.X, pady=(15, 5), padx=15)
        self.progress.set(0)

        # ステータス表示
        self.status_label = ctk.CTkLabel(
            parent,
            text="",
            font=("Helvetica", 12),
        )
        self.status_label.pack(pady=(5, 10))

        # ボタンフレーム
        button_frame = ctk.CTkFrame(parent)
        button_frame.pack(fill=tk.X, pady=(15, 15), padx=15)

        self.convert_button = ctk.CTkButton(
            button_frame,
            text="一括変換実行",
            command=self._start_batch_convert,
            state=tk.DISABLED,
            width=200,
        )
        self.convert_button.pack(side=tk.LEFT, padx=(0, 10))

        cancel_button = ctk.CTkButton(
            button_frame,
            text="キャンセル",
            command=self.destroy,
            width=100,
        )
        cancel_button.pack(side=tk.LEFT)

    def _select_files(self) -> None:
        """画像ファイルを選択する."""
        files = ctk.filedialog.askopenfilenames(
            title="画像を選択",
            filetypes=[
                ("画像ファイル", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"),
                ("すべて", "*.*"),
            ],
        )

        if files:
            self._selected_files = [Path(f).resolve() for f in files]
            self.file_listbox.delete(0, tk.END)
            for f in self._selected_files:
                self.file_listbox.insert(tk.END, f.name)
            self.file_count_label.configure(text=f"選択数: {len(self._selected_files)}")
            self._update_convert_button_state()
            logger.info("Selected %d files for batch conversion", len(self._selected_files))

    def _select_output_dir(self) -> None:
        """出力フォルダを選択する."""
        dir_path = ctk.filedialog.askdirectory(title="出力フォルダを選択")
        if dir_path:
            self._output_dir = Path(dir_path)
            self.output_dir_label.configure(text=f"出力フォルダ: {self._output_dir.name}")
            self._update_convert_button_state()
            logger.info("Output directory selected: %s", self._output_dir)

    def _enable_widgets(self, frame: ctk.CTkFrame, enabled: bool) -> None:
        """
        フレーム内の全ウィジェットを有効/無効にする。

        Args:
            frame: 対象フレーム。
            enabled: 有効にするかどうか。
        """
        state = tk.NORMAL if enabled else tk.DISABLED
        for widget in frame.winfo_children():
            self._set_widget_state(widget, state)

    def _set_widget_state(self, widget, state: str) -> None:
        """
        ウィジェットとその子ウィジェットの状態を設定する。

        Args:
            widget: 対象ウィジェット。
            state: tk.NORMAL または tk.DISABLED。
        """
        try:
            widget.configure(state=state)
        except (tk.TclError, ValueError, AttributeError):
            pass  # stateをサポートしないウィジェットは無視

        # フレームの場合は再帰的に処理
        if hasattr(widget, "winfo_children"):
            for child in widget.winfo_children():
                self._set_widget_state(child, state)

    def _on_resize_toggle(self) -> None:
        """解像度変更チェックボックス変更時の処理（非使用）."""
        pass

    def _on_mode_change(self) -> None:
        """変換モード変更時の処理."""
        mode = self.mode_var.get()

        # 解像度変更が有効かどうかを確認
        resize_enabled = self.resize_checkvar.get()

        # 各入力フレームの有効/無効を切り替え
        self._enable_widgets(self.ratio_input_frame, mode == "ratio" and resize_enabled)
        self._enable_widgets(self.width_input_frame, mode == "width" and resize_enabled)
        self._enable_widgets(self.height_input_frame, mode == "height" and resize_enabled)

    def _update_quality_label(self, value: float) -> None:
        """qualityラベルを更新する."""
        self.quality_label.configure(text=str(int(value)))

    def _update_convert_button_state(self) -> None:
        """変換ボタンの状態を更新する."""
        if self._selected_files and self._output_dir is not None:
            self.convert_button.configure(state=tk.NORMAL)
        else:
            self.convert_button.configure(state=tk.DISABLED)

    def _calculate_new_size(self, original_width: int, original_height: int) -> tuple[int, int]:
        """
        新しいサイズを計算する。

        Args:
            original_width: 元の幅。
            original_height: 元の高さ。

        Returns:
            (width, height)のタプル。
        """
        if not self.resize_checkvar.get():
            return original_width, original_height

        mode = self.mode_var.get()

        try:
            if mode == "ratio":
                ratio = float(self.ratio_entry.get()) / 100.0
                new_width = max(1, int(original_width * ratio))
                new_height = max(1, int(original_height * ratio))
            elif mode == "width":
                new_width = int(self.width_entry.get())
                ratio = new_width / original_width
                new_height = max(1, int(original_height * ratio))
            else:  # height
                new_height = int(self.height_entry.get())
                ratio = new_height / original_height
                new_width = max(1, int(original_width * ratio))
        except ValueError:
            return original_width, original_height

        return new_width, new_height

    def _start_batch_convert(self) -> None:
        """一括変換を開始する."""
        self.convert_button.configure(state=tk.DISABLED)
        total = len(self._selected_files)
        success_count = 0
        error_count = 0

        for i, file_path in enumerate(self._selected_files):
            try:
                self.status_label.configure(text=f"変換中: {file_path.name} ({i + 1}/{total})")
                self.progress.set((i + 1) / total)
                self.update()  # UI更新

                # 画像を開く
                img = Image.open(file_path)
                img.load()

                # RGBに変換
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # リサイズ
                new_width, new_height = self._calculate_new_size(img.width, img.height)
                if (new_width, new_height) != (img.width, img.height):
                    img = img.resize((new_width, new_height), Image.LANCZOS)

                # 出力パス（変換後フォルダに保存）
                output_path = self._output_dir / f"{file_path.stem}.jpg"

                # 保存
                quality = int(self.quality_slider.get())
                img.save(output_path, "JPEG", quality=quality)
                success_count += 1
                logger.info("Converted: %s -> %s", file_path.name, output_path)

            except Exception as e:
                error_count += 1
                logger.error("Failed to convert %s: %s", file_path.name, e)

        # 完了
        self.progress.set(1.0)
        if error_count == 0:
            self.status_label.configure(text=f"変換完了: {success_count}ファイル")
            messagebox.showinfo("完了", f"{success_count}ファイルを変換しました")
        else:
            self.status_label.configure(text=f"変換完了: {success_count}成功, {error_count}失敗")
            messagebox.showwarning(
                "完了",
                f"{success_count}ファイルを変換しました\n{error_count}ファイルは失敗しました",
            )

        self.convert_button.configure(state=tk.NORMAL)