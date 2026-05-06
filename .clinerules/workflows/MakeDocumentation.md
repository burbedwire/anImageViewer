# ドキュメント作成ルール
## readmeの作成
ルートディレクトリにreadme.mdを置くこと
readmeには下記を記載すること
- プロジェクト概要
- 環境
- 起動方法
- 使用方法

## 詳細ドキュメントの作成場所
docフォルダの配下に置くこと
下記のファイルを記載すること
- 詳細設計（環境、コードの構成、実行方法、使用方法、ＡＰＩ、設計思想など、詳細をすべて記載する）
- シーケンス図、クラス図、データフロー図、ユースケース図、フローチャート図、など（全体／コンポーネントで分けて、plantUML記法で保存）

## plantUML記法の例

### シーケンス図の例
@startuml
Alice-> Bob: Authentication Request
alt successful case
Bob-> Alice: Authentication Accepted
else some kind of failure
Bob-> Alice: Authentication Failure
group My own label
Alice-> Log : Log attack start
loop 1000 times
Alice-> Bob: DNS Attack
end
Alice-> Log : Log attack end
end
else Another type of failure
Bob-> Alice: Please repeat
end
@enduml

### ユースケース図の例
@startuml
:Main Admin: as Admin
(Use the application) as (Use)
User-> (Start)
User--> (Use)
Admin---> (Use)
note right of Admin : This is an example.
note right of (Use)
A note can also
be on several lines
end note
note "This note is connected\nto several objects." as N2
(Start) .. N2
N2 .. (Use)
@enduml

### フローチャート図の例
@startuml
!pragma useVerticalIf on
start
if (condition A) then (yes)
:Text 1;
elseif (condition B) then (yes)
:Text 2;
stop
elseif (condition C) then (yes)
:Text 3;
elseif (condition D) then (yes)
:Text 4;
else (nothing)
:Text else;
endif
stop
@enduml

