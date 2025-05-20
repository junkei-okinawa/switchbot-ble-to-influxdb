# switchbot-ble-to-influxdb（日本語版）

SwitchBot BLEセンサーから環境データを収集し、InfluxDBに保存するツールです。

## 必要要件

* Python 3.12以上
* [uv](https://github.com/astral-sh/uv)
* [just](https://github.com/casey/just)
* SwitchBot メーター/センサー デバイス
* InfluxDB インスタンス

## 依存ライブラリ

主なPythonライブラリ：

* [pySwitchbot](https://github.com/sblibs/pySwitchbot): SwitchBotデバイス操作用
* `influxdb-client`: InfluxDBへのデータ送信用
* `python-dotenv`: 環境変数管理用

開発用依存は`pyproject.toml`で管理され、テストには`pytest`を利用します。

## インストール

1. **リポジトリのクローン**
    ```bash
    git clone https://github.com/junkei-okinawa/switchbot-ble-to-influxdb.git
    cd switchbot-ble-to-influxdb
    ```

2. **uvで依存関係をインストール**
    ```bash
    uv sync
    ```
    開発用依存も含めてインストールする場合：
    ```bash
    uv sync --dev
    ```

## 設定

`.env`ファイルをプロジェクトルートに作成し、以下の環境変数を設定してください。

```env
INFLUXDB_TOKEN="your_influxdb_token"
INFLUXDB_URL="http://localhost:8086" # InfluxDBのURL
INFLUXDB_ORG="your_influxdb_org"
INFLUXDB_BUCKET="your_influxdb_bucket"
INFLUXDB_MEASUREMENT="switchbot_metrics" # 任意のmeasurement名
DEVICE_ID="your_switchbot_device_address" # 対象SwitchBotデバイスのアドレス
```

各値はご自身の環境に合わせて設定してください。

## 使い方

スクリプトを実行してデータ収集を開始します：

```bash
uv run just dev
```

このコマンドで`main.py`が実行され、SwitchBot温湿度センサーを検出し、指定デバイスからデータを取得してInfluxDBに書き込みます。

ログはコンソールに出力されます。

## 注意事項（Raspberry Pi等でのタイムアウト対策）

Raspberry Pi等の環境では、SwitchBotデバイスのUUID認識に時間がかかる場合があります。
そのため、本プロジェクトではデバイス検出時に `scan_timeout=60` を明示的に指定しています。
（参考: commit 9ff7bc47034d1407da9c100e67837f1ccae97936）

デフォルトの `get_tempsensors()` ではタイムアウトする場合があるため、
`GetSwitchbotDevices().discover(scan_timeout=60)` を利用してください。

## 動作概要

`main.py`の処理概要：
1. 環境変数の読み込み
2. InfluxDBクライアントの初期化
3. `pyswitchbot`の`GetSwitchbotDevices`でSwitchBot温湿度センサーを検出
4. `DEVICE_ID`に一致するデバイスを抽出
5. センサーから温度・湿度・バッテリー情報を取得
6. InfluxDB用の`Point`オブジェクトに整形
7. 指定バケットにデータを書き込み

## 開発

### テスト実行

テストを実行するには：
```bash
uv run just test
# ユニットテスト
uv run just test tests/unit
# 結合テスト
uv run just test tests/integration
```
