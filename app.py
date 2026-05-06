"""画像ビューワーのメインアプリケーションウィンドウ."""

import logging
import tkinter as tk
from pathlib import Path
from typing import Optional, List

import customtkinter as ctk
from PIL import Image, ImageTk
try:
    from tkinterdnd2 import DND_FILES, DnDCanvas
    HAS_DND = True
except ImportError:
    HAS_DND = False
    DnDCanvas = None

# ロガー設定
logger = logging.getLogger(__name__)

# サポートする画像拡張子
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}

# デフォルトウィンドウサイズ
DEFAULT_WINDOW_WIDTH = 1280
DEFAULT_WINDOW_HEIGHT = 720

# 最小ウィンドウサイズ
MIN_WINDOW_WIDTH = 600
MIN_WINDOW_HEIGHT = 400


class ImageViewerApp(ctk.CTk):
    """画像ビューワーのメインアプリケーションクラス."""

    def __init__(self):
        super().__init__()
        self._setup_window()
        self._setup_menu()
        self._setup_canvas()
        self._setup_drag_drop()
        self._setup_key_bindings()

        # 現在開いている画像パス
        self._current_image_path: Optional[Path] = None
        # 現在表示しているフォルダの画像リスト
        self._image_list: List[Path] = []
        # 現在の画像インデックス
        self._current_index: int = -1
        # PIL Image
        self._current_image: Optional[Image.Image] = None
        # PhotoImage（キャンバス表示用）
        self._photo_image: Optional[ImageTk.PhotoImage] = None
        # キャンバス上の画像アイテムID
        self._canvas_image_item: Optional[int] = None

    def _setup_window(self) -> None:
        """ウィンドウの基本設定を行う."""
        self.title("ImageViewer")
        self.geometry(f"{DEFAULT_WINDOW_WIDTH}x{DEFAULT_WINDOW_HEIGHT}")
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        logger.info("MainWindow initialized with size %dx%d", DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)

    def _setup_menu(self) -> None:
        """メニューバーを設定する."""
        self.menu_bar = tk.Menu(self)
        self.configure(menu=self.menu_bar)

        # ファイルメニュー
        file_menu = tk.Menu(self.menu_bar, tearoff=False)
        file_menu.add_command(label="開く...", command=self._open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="閉じる", command=self._close_file, accelerator="Ctrl+W")
        file_menu.add_separator()
        file_menu.add_command(label="クリップして保存", command=self._clip_save, accelerator="Ctrl+Shift+C")
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.quit, accelerator="Alt+F4")
        self.menu_bar.add_cascade(label="ファイル", menu=file_menu)

        # 編集メニュー
        edit_menu = tk.Menu(self.menu_bar, tearoff=False)
        edit_menu.add_command(label="クリップ", command=self._start_clip, accelerator="Ctrl+C")
        edit_menu.add_command(label="透過色指定", command=self._set_transparency, accelerator="Ctrl+T")
        self.menu_bar.add_cascade(label="編集", menu=edit_menu)

        # 変換メニュー
        convert_menu = tk.Menu(self.menu_bar, tearoff=False)
        convert_menu.add_command(label="解像度変換", command=self._resize_image, accelerator="Ctrl+R")
        convert_menu.add_command(label="一括変換", command=self._batch_convert, accelerator="Ctrl+Shift+R")
        self.menu_bar.add_cascade(label="変換", menu=convert_menu)

        # ヘルプメニュー
        help_menu = tk.Menu(self.menu_bar, tearoff=False)
        help_menu.add_command(label="について", command=self._show_about)
        self.menu_bar.add_cascade(label="ヘルプ", menu=help_menu)

        # ショートカットキー設定
        self.bind("<Control-o>", lambda e: self._open_file())
        self.bind("<Control-w>", lambda e: self._close_file())
        self.bind("<Control-c>", lambda e: self._start_clip())
        self.bind("<Control-Shift-c>", lambda e: self._clip_save())
        self.bind("<Control-t>", lambda e: self._set_transparency())
        self.bind("<Control-r>", lambda e: self._resize_image())
        self.bind("<Control-Shift-r>", lambda e: self._batch_convert())

    def _setup_canvas(self) -> None:
        """画像表示用のキャンバスを設定する."""
        # 画像表示フレーム（背景色をキャンバスと同じに設定）
        self.canvas_frame = ctk.CTkFrame(self, fg_color="#2b2b2b")
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # gridレイアウトを使用（キャンバス:0行0列, 縦スクロールバー:0行1列, 横スクロールバー:1行0列）
        self.canvas_frame.grid_rowconfigure(0, weight=1)
        self.canvas_frame.grid_columnconfigure(0, weight=1)

        # tkinterdnd2が利用可能な場合はDnDCanvasを使用
        if HAS_DND and DnDCanvas is not None:
            self.canvas = DnDCanvas(
                self.canvas_frame,
                bg="#2b2b2b",
                highlightthickness=0,
            )
        else:
            self.canvas = tk.Canvas(
                self.canvas_frame,
                bg="#2b2b2b",
                highlightthickness=0,
            )
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # スクロールバー設定（gridで配置）
        h_scroll = ctk.CTkScrollbar(self.canvas_frame, orientation="horizontal", command=self.canvas.xview)
        v_scroll = ctk.CTkScrollbar(self.canvas_frame, orientation="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)
        h_scroll.grid(row=1, column=0, sticky="ew")
        v_scroll.grid(row=0, column=1, sticky="ns")

        # キャンバスリサイズ時の再描画
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        # ステータスバー
        self.status_bar = ctk.CTkLabel(self, text="準備完了", height=25)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=2)

    def _setup_drag_drop(self) -> None:
        """ドラッグアンドドロップを設定する."""
        if HAS_DND:
            try:
                self.canvas.drop_target_register(DND_FILES)
                self.canvas.dnd_bind('<Drop>', self._on_drop)
                logger.info("Drag and drop enabled")
            except Exception as e:
                logger.warning("Drag and drop initialization failed: %s", e)
        else:
            logger.warning("tkinterdnd2 not available, drag and drop disabled")

    def _setup_key_bindings(self) -> None:
        """キーバインディングを設定する."""
        # メインウィンドウにバインド（フォーカス位置に関係なく動作する）
        self.bind("<Left>", self._prev_image)
        self.bind("<Right>", self._next_image)
        self.bind("<Up>", self._first_image)
        self.bind("<Down>", self._last_image)
        
        # キャンバスもバインド（キャンバスがフォーカスの場合）
        self.canvas.bind("<Left>", self._prev_image)
        self.canvas.bind("<Right>", self._next_image)
        self.canvas.bind("<Up>", self._first_image)
        self.canvas.bind("<Down>", self._last_image)

    def _on_drop(self, event: str) -> None:
        """
        ドラッグアンドドロップイベントを処理する。

        Args:
            event: ドロップされたファイルパスの文字列。
        """
        try:
            # ファイルパスから囲みダブルクォートを削除
            file_path = event.strip('"').strip()
            if not file_path:
                return
            path = Path(file_path)
            if path.is_file():
                self.open_image(str(path))
            else:
                self._update_status(f"ファイルが見つかりません: {path.name}")
        except Exception as e:
            logger.error("Drop error: %s", e)

    def _on_canvas_resize(self, event: tk.Event) -> None:
        """キャンバスリサイズ時に画像を再描画する."""
        if self._current_image is not None:
            self._display_image(self._current_image)

    def _get_image_files(self, directory: Path) -> List[Path]:
        """ディレクトリ内の画像ファイルを取得する."""
        image_files = []
        for f in sorted(directory.iterdir()):
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
                image_files.append(f)
        return image_files

    def open_image(self, file_path: str) -> bool:
        """
        指定された画像ファイルを開く。

        Args:
            file_path: 開く画像ファイルのパス。

        Returns:
            画像が開けた場合はTrue、そうでない場合はFalse。
        """
        try:
            path = Path(file_path).resolve()
            if not path.is_file():
                logger.error("File not found: %s", path)
                self._update_status(f"ファイルが見つかりません: {path.name}")
                return False

            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                logger.error("Unsupported format: %s", path.suffix)
                self._update_status(f"サポートされていない形式: {path.suffix}")
                return False

            img = Image.open(path)
            img.load()  # 完全にメモリに読み込む

            # RGBに変換（PNGのアルファチャンネルがある場合は維持）
            if img.mode in ("RGBA", "LA", "P"):
                pass  # 透過のある形式は維持
            elif img.mode != "RGB":
                img = img.convert("RGB")

            self._current_image = img
            self._current_image_path = path
            self._current_index = -1

            # 同じフォルダの画像リストを更新
            image_files = self._get_image_files(path.parent)
            if image_files:
                self._image_list = image_files
                try:
                    self._current_index = self._image_list.index(path)
                except ValueError:
                    self._current_index = -1

            self._display_image(img)
            self._update_status(f"{path.name} ({img.width}x{img.height})")
            self.title(f"ImageViewer - {path.name}")
            logger.info("Opened image: %s (%dx%d)", path.name, img.width, img.height)
            return True
        except Exception as e:
            logger.error("Failed to open image: %s", e)
            self._update_status(f"画像を開くのに失敗しました: {e}")
            return False

    def _display_image(self, img: Image.Image) -> None:
        """
        キャンバスに画像を表示する。

        Args:
            img: 表示するPIL Image。
        """
        self.canvas.delete("all")

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # ウィンドウサイズより画像が大きい場合は縮小
        if img.width > canvas_width or img.height > canvas_height:
            ratio = min(canvas_width / img.width, canvas_height / img.height)
            new_width = max(1, int(img.width * ratio))
            new_height = max(1, int(img.height * ratio))
            display_img = img.resize((new_width, new_height), Image.LANCZOS)
        else:
            display_img = img

        self._photo_image = ImageTk.PhotoImage(display_img)
        center_x = canvas_width // 2
        center_y = canvas_height // 2

        self._canvas_image_item = self.canvas.create_image(
            center_x, center_y, image=self._photo_image, anchor=tk.CENTER
        )

        # スクロール領域設定
        scroll_width = max(canvas_width, display_img.width)
        scroll_height = max(canvas_height, display_img.height)
        self.canvas.configure(scrollregion=(0, 0, scroll_width, scroll_height))

    def _prev_image(self, event: tk.Event = None) -> None:
        """前の画像を表示する."""
        if self._current_index > 0:
            self._current_index -= 1
            self.open_image(str(self._image_list[self._current_index]))

    def _next_image(self, event: tk.Event = None) -> None:
        """次の画像を表示する."""
        if self._current_index < len(self._image_list) - 1:
            self._current_index += 1
            self.open_image(str(self._image_list[self._current_index]))

    def _first_image(self, event: tk.Event = None) -> None:
        """1枚目の画像を表示する."""
        if self._image_list:
            self._current_index = 0
            self.open_image(str(self._image_list[self._current_index]))

    def _last_image(self, event: tk.Event = None) -> None:
        """最後の画像を表示する."""
        if self._image_list:
            self._current_index = len(self._image_list) - 1
            self.open_image(str(self._image_list[self._current_index]))

    def _open_file(self) -> None:
        """ファイルオープンダイアログを表示する."""
        file_path = ctk.filedialog.askopenfilename(
            title="画像を開く",
            filetypes=[
                ("画像ファイル", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"),
                ("すべて", "*.*"),
            ],
        )
        if file_path:
            self.open_image(file_path)

    def _close_file(self) -> None:
        """現在開いているファイルを閉じる."""
        self._current_image = None
        self._current_image_path = None
        self._current_index = -1
        self._image_list = []
        self.canvas.delete("all")
        self._update_status("準備完了")
        self.title("ImageViewer")
        logger.info("File closed")

    def _clip_save(self) -> None:
        """クリップして保存ダイアログを表示する."""
        if self._current_image is None:
            logger.warning("No image opened")
            return
        from clip_dialog import ClipDialog
        dialog = ClipDialog(self, self._current_image)
        try:
            self.wait_window(dialog)
        except tk.TclError:
            pass  # ダイアログが既に破棄されている場合は無視

    def _start_clip(self) -> None:
        """クリップモードを開始する."""
        if self._current_image is None:
            logger.warning("No image opened")
            return
        from clip_dialog import ClipDialog
        dialog = ClipDialog(self, self._current_image)
        try:
            self.wait_window(dialog)
        except tk.TclError:
            pass  # ダイアログが既に破棄されている場合は無視

    def _set_transparency(self) -> None:
        """透過色指定ダイアログを表示する."""
        if self._current_image is None:
            logger.warning("No image opened")
            return
        from transparency_dialog import TransparencyDialog
        dialog = TransparencyDialog(self, self._current_image, self._current_image_path)
        try:
            self.wait_window(dialog)
        except tk.TclError:
            pass  # ダイアログが既に破棄されている場合は無視

    def _resize_image(self) -> None:
        """解像度変換ダイアログを表示する."""
        if self._current_image is None:
            logger.warning("No image opened")
            return
        from resize_dialog import ResizeDialog
        dialog = ResizeDialog(self, self._current_image, self._current_image_path)
        try:
            self.wait_window(dialog)
        except tk.TclError:
            pass  # ダイアログが既に破棄されている場合は無視

    def _batch_convert(self) -> None:
        """一括変換ダイアログを表示する."""
        from batch_convert_dialog import BatchConvertDialog
        dialog = BatchConvertDialog(self)
        try:
            self.wait_window(dialog)
        except tk.TclError:
            pass  # ダイアログが既に破棄されている場合は無視

    def _show_about(self) -> None:
        """についてダイアログを表示する."""
        about_dialog = ctk.CTkToplevel(self)
        about_dialog.title("について")
        about_dialog.geometry("400x200")
        about_dialog.resizable(False, False)

        label = ctk.CTkLabel(
            about_dialog,
            text="ImageViewer\n\n画像ビューワーアプリケーション\nCustomTkinter + Pillow",
            font=("Helvetica", 14),
        )
        label.pack(expand=True)

        close_button = ctk.CTkButton(about_dialog, text="閉じる", command=about_dialog.destroy)
        close_button.pack(pady=20)

        about_dialog.transient(self)
        about_dialog.grab_set()
        self.wait_window(about_dialog)

    def _update_status(self, message: str) -> None:
        """
        ステータスバーのテキストを更新する。

        Args:
            message: 表示するメッセージ。
        """
        self.status_bar.configure(text=message)