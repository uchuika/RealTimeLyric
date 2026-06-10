const form = document.querySelector("#lyrics-form");
const tokenInput = document.querySelector("#app-token");
const songUrlInput = document.querySelector("#song-url");
const loadButton = document.querySelector("#load-button");
const copyButton = document.querySelector("#copy-button");
const statusElement = document.querySelector("#status");
const lyricsElement = document.querySelector("#lyrics");
const mediaElement = document.querySelector("#media");

let player = null;
let lyricsText = "";

function setStatus(message, isError = false) {
  statusElement.textContent = message;
  statusElement.classList.toggle("error", isError);
}

function disposePlayer() {
  if (player) {
    player.dispose();
    player = null;
  }
  mediaElement.replaceChildren();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const token = tokenInput.value.trim();
  const songUrl = songUrlInput.value.trim();
  if (!token || !songUrl) {
    setStatus("アプリトークンと楽曲URLを入力してください。", true);
    return;
  }

  disposePlayer();
  lyricsText = "";
  lyricsElement.textContent = "";
  copyButton.disabled = true;
  loadButton.disabled = true;
  setStatus("楽曲情報と歌詞を読み込んでいます...");

  player = new TextAliveApp.Player({
    app: { token },
    mediaElement,
  });

  player.addListener({
    onVideoReady(video) {
      lyricsText = video.phrases
        .map((phrase) => phrase.text)
        .join("\n");

      if (!lyricsText) {
        lyricsElement.textContent = "この楽曲から歌詞を取得できませんでした。";
        setStatus("歌詞データが見つかりませんでした。", true);
      } else {
        lyricsElement.textContent = lyricsText;
        copyButton.disabled = false;
        setStatus(`${video.phraseCount}フレーズの歌詞を取得しました。`);
      }
      loadButton.disabled = false;
    },
  });

  try {
    await player.createFromSongUrl(songUrl);
  } catch (error) {
    console.error(error);
    lyricsElement.textContent = "歌詞の取得中にエラーが発生しました。";
    setStatus(`取得に失敗しました: ${error.message || error}`, true);
    loadButton.disabled = false;
  }
});

copyButton.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(lyricsText);
    setStatus("歌詞をクリップボードにコピーしました。");
  } catch (error) {
    setStatus(`コピーに失敗しました: ${error.message || error}`, true);
  }
});
