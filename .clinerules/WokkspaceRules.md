# Workspace共通ルール
## 開発環境
OS: Windows
言語: Python 3.14
仮想環境は venv を使用している

## ライブラリ
UIはCustomTkinterを使用する


## コーディング規約
PEP8 に準拠
関数名: snake_case
クラス名: PascalCase
定数: UPPER_SNAKE_CASE
型ヒントは必須
ログは logging モジュールを使用（print 禁止）

## テスト方針
テストフレームワーク: pytest
テストファイルは tests/test_xxx.py
境界値テストを必ず含める
バッファオーバーフローや例外系のテストも含める
テスト結果は、testResultフォルダに、日付のMarkdownファイルを用意して結果を書くこと

## コメント
関数には docstring（Google スタイル）のコメント
