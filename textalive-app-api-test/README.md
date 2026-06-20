# TextAlive 歌詞全文取得

TextAlive公式サイトと同様にSongleの登録楽曲を曲名・アーティスト名で検索し、
選択した楽曲URLからTextAlive App APIの歌詞全文を取得するブラウザアプリです。

YouTube、ニコニコ動画、Piapro、SoundCloudなど、Songleに登録されている
複数の配信元を横断して検索できます。

## 準備

1. TextAlive for Developersでアプリトークンを発行します。

YouTube Data APIキーは不要です。

## 起動

```powershell
npm start
```

ブラウザで`http://localhost:3000`を開いてください。

Songleの検索結果に歌詞が登録されていない場合、歌詞を取得できないことがあります。
その場合は別の検索結果を選択してください。
