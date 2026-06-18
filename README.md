# ROS2 Action / Parameter 実習 (Jazzy)

ROS2 の **Action** と **Parameter** を学ぶための実習用ワークスペースです。
ホスト環境（conda / pyenv 等）に依存せず、誰の PC でも同じ手順で動くように
作られています。

## 前提環境

- **x86_64 (amd64) の Linux**。使用イメージ `osrf/ros:jazzy-desktop-full` は
  amd64 専用のため、ARM / macOS は対象外です（`run_practical.bash` が自動でチェックします）。
- **Docker Engine** が導入済みで、実行ユーザが `docker` グループ所属（または `sudo` 実行）。
  - 未導入: https://docs.docker.com/engine/install/
  - 権限付与: `sudo usermod -aG docker $USER`（実行後に再ログイン）
- **初回のみ約5GB のイメージ取得**が走ります（ネット接続と空きディスクが必要）。
- Fedora / RHEL 系（SELinux 有効）でも、ワークスペースは `:z` 付きでマウントするので
  そのまま動きます。GPU は nvidia ランタイムがある時だけ自動で有効化されます。

## 構成

```
ros2_action_parameter_practical/
├── run_practical.bash        # コンテナ起動ランチャ（環境非依存）
└── ros2_practical_ws/
    ├── .bashrc               # コンテナ内で自動 source される設定
    └── src/
        ├── action_param_interfaces/   # AutoCharge.action 定義 (ament_cmake)
        └── action_param_demo/         # ノード群 (ament_python)
            ├── auto_charge_server.py        # Action サーバ + パラメータ
            ├── auto_charge_client.py        # Action クライアント
            ├── param_talker.py              # パラメータコールバックの例
            └── parameter_set_get_client.py  # 他ノードの param を set/get
```

## なぜ環境非依存なのか

`run_practical.bash` は **ホームディレクトリをマウントしません**。ワークスペース
だけを `/ros2_ws` にマウントするため、ホストの `~/.bashrc` / conda / pyenv が
コンテナに混入せず、常にコンテナ内の `/usr/bin/python3` でビルドされます。
（ホームを丸ごとマウントすると、ホストの conda python がビルドを乗っ取り
`ModuleNotFoundError: No module named 'em'` 等で失敗します。これを構造的に回避。）

- `ROS_DOMAIN_ID=42` + localhost 限定検出で、他の ROS2 環境（ホストの Humble や
  別コンテナ）と DDS が衝突しません。
- GPU は nvidia ランタイムがある時だけ自動で有効化（GPU 無し PC でも動作）。

## 1. 起動 & ビルド

ホスト側のターミナルで（各自のパスでOK。**最初の起動コマンドは環境ごとに違ってよい**）:

```bash
cd <このディレクトリ>/ros2_action_parameter_practical
./run_practical.bash
```

コンテナに入ると `[jazzy ws]` プロンプトになり、ROS2 Jazzy が自動で source 済みです。
続けてビルド:

```bash
# 中の作業ディレクトリは /ros2_ws
colcon build --symlink-install
source install/setup.bash
```

> 2つ目以降のターミナルは、ホスト側で再度 `./run_practical.bash` を実行すると
> **同じコンテナに追加のシェルとして入ります**（同じ ROS グラフを共有）。

Action 定義の確認:

```bash
cat src/action_param_interfaces/action/AutoCharge.action
ros2 interface show action_param_interfaces/action/AutoCharge
```

## 2. Action サーバ / クライアント

```bash
# Terminal 1: サーバ
ros2 run action_param_demo auto_charge_server

# Terminal 2: CLI から goal（--feedback で途中経過を表示）
ros2 action send_goal --feedback /auto_charge \
    action_param_interfaces/action/AutoCharge "{target_percent: 80}"

# Terminal 3: feedback トピックを直接 echo
ros2 topic echo /auto_charge/_action/feedback --flow-style

# クライアントノードから goal（target はパラメータで指定）
ros2 run action_param_demo auto_charge_client --ros-args -p target_percent:=90
```

## 3. パラメータ操作

```bash
# 一覧 / 取得
ros2 param list /auto_charge_server
ros2 param get /auto_charge_server charge_step
ros2 param get /auto_charge_server feedback_period_sec
ros2 param get /auto_charge_server station_name

# 変更（バリデーションを通る値）
ros2 param set /auto_charge_server charge_step 5
ros2 param set /auto_charge_server feedback_period_sec 0.5
ros2 param set /auto_charge_server station_name "fast_station"

# 変更後にもう一度 goal（charge_step / station が反映される）
ros2 action send_goal --feedback /auto_charge \
    action_param_interfaces/action/AutoCharge "{target_percent: 80}"

# 不正値は reject される（負の charge_step）
ros2 param set /auto_charge_server charge_step -1
#   -> Setting parameter failed: charge_step must be a positive integer
```

## 4. パラメータコールバック (param_talker)

```bash
ros2 run action_param_demo param_talker

# 別ターミナルで decoration を変更（出力がその場で変わる）
#
# 値のクォートに2つ理由があります:
#  1) YAML 対策: ros2 param set は値を YAML として解釈し、* (alias) や
#     ! (tag) は特別な記号。文字列として渡すには内側を ' ' で囲う。
#  2) bash 対策: ! は bash のヒストリ展開記号で "!!!" は event not found に
#     なる。そのターミナルで一度 `set +H` を実行して無効化しておく。
set +H
ros2 param set /param_talker decoration "'***'"
ros2 param set /param_talker decoration "'!!!'"
```

## 5. プログラムからの set/get (parameter_set_get_client)

`auto_charge_server` を起動した状態で:

```bash
ros2 run action_param_demo parameter_set_get_client
#   auto_charge_server の charge_step / station_name を set し、
#   3つのパラメータを get して表示します。
```

## 終了 / 後片付け

- 各シェルは `exit`、ノードは `Ctrl+C`。
- 最後のシェルを抜けるとコンテナは自動削除されます（`--rm`）。
- ビルド成果物 `ros2_practical_ws/build,install,log` はホストに残ります。
  作り直したい場合は削除して再ビルドしてください。
