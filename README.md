# desknetsRemindNotifier
デスクネッツのスケジュールをSlackリマインダーに登録する  
（参考にさせて頂いたサイト：https://github.com/kentoku24/desknetsNotifier ）

- 使い方
  * conf配下のcredentials.template.yamlを適当なファイル名にリネーム、必要な情報を記入し、このディレクトリ内でpython main.pyを実行  
    パラメータにリネームした(例：./conf/credentials.yaml)を設定、ファイル作成する  
    - DN_USERNAME DN_PASSWORD DN_URL これらには自分のデスクネッツの情報を記入
    - SLACK_TOKEN は[こちら](https://api.slack.com/custom-integrations/legacy-tokens)から取得
    - SLACK_NOTIFIER_USERS 登録対象とするSLACKUSERを記入 例）["AAAAAAAAA","BBBBBBBBB"]
    - SEARCH_STRING 対象とするスケジュールタイトルを記入
    
- 前提条件
  * Chrome Canaryを導入したWindows端末で動作確認をしていますので、Windows版のChromeDriverを同梱しています。
  お使いのOSに対応する[ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/) をこのディレクトリに置けば動くかもしれません。
  
  
