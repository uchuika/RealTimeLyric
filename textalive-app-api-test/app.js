const searchForm = document.querySelector("#search-form");
const lyricsForm = document.querySelector("#lyrics-form");
const tokenInput = document.querySelector("#app-token");
const searchQueryInput = document.querySelector("#search-query");
const songUrlInput = document.querySelector("#song-url");
const searchButton = document.querySelector("#search-button");
const loadButton = document.querySelector("#load-button");
const copyButton = document.querySelector("#copy-button");
const statusElement = document.querySelector("#status");
const lyricsElement = document.querySelector("#lyrics");
const resultsSection = document.querySelector("#results-section");
const searchResultsElement = document.querySelector("#search-results");
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

function createResultCard(item) {
  const card = document.createElement("article");
  card.className = "result-card";

  const source = document.createElement("div");
  source.className = "source-badge";
  source.textContent = item.source;

  const details = document.createElement("div");
  details.className = "result-details";

  const title = document.createElement("h3");
  title.textContent = item.title;

  const artist = document.createElement("p");
  artist.textContent = item.artist || "アーティスト不明";

  const links = document.createElement("div");
  links.className = "result-links";

  const sourceLink = document.createElement("a");
  sourceLink.href = item.sourceUrl;
  sourceLink.target = "_blank";
  sourceLink.rel = "noopener noreferrer";
  sourceLink.textContent = "配信元";

  const songleLink = document.createElement("a");
  songleLink.href = item.songleUrl;
  songleLink.target = "_blank";
  songleLink.rel = "noopener noreferrer";
  songleLink.textContent = "Songle";
  links.append(sourceLink, songleLink);

  const selectButton = document.createElement("button");
  selectButton.type = "button";
  selectButton.textContent = "この楽曲の歌詞を取得";
  selectButton.addEventListener("click", () => {
    songUrlInput.value = item.sourceUrl;
    loadLyrics(item.sourceUrl);
  });

  details.append(title, artist, links, selectButton);
  card.append(source, details);
  return card;
}

async function searchSongs(query) {
  const endpoint = new URL("/api/search", window.location.origin);
  endpoint.searchParams.set("q", query);
  const response = await fetch(endpoint);
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || `HTTP ${response.status}`);
  }

  return data.items;
}

async function loadLyrics(songUrl) {
  const token = tokenInput.value.trim();
  if (!token) {
    setStatus("TextAliveアプリトークンを入力してください。", true);
    tokenInput.focus();
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
        setStatus("歌詞データが見つかりませんでした。別の検索結果をお試しください。", true);
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
}

searchForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const query = searchQueryInput.value.trim();

  searchButton.disabled = true;
  resultsSection.hidden = true;
  searchResultsElement.replaceChildren();
  setStatus(`「${query}」をSongleの登録楽曲から検索しています...`);

  try {
    const items = await searchSongs(query);
    if (items.length === 0) {
      setStatus("検索結果が見つかりませんでした。", true);
      return;
    }

    searchResultsElement.append(...items.map(createResultCard));
    resultsSection.hidden = false;
    setStatus(`${items.length}件の楽曲が見つかりました。歌詞を取得する楽曲を選んでください。`);
  } catch (error) {
    console.error(error);
    setStatus(`楽曲検索に失敗しました: ${error.message || error}`, true);
  } finally {
    searchButton.disabled = false;
  }
});

lyricsForm.addEventListener("submit", (event) => {
  event.preventDefault();
  loadLyrics(songUrlInput.value.trim());
});

copyButton.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(lyricsText);
    setStatus("歌詞をクリップボードにコピーしました。");
  } catch (error) {
    setStatus(`コピーに失敗しました: ${error.message || error}`, true);
  }
});
