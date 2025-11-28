// naversearch/static/naversearch/app.js

document.addEventListener("DOMContentLoaded", () => {
  const searchBtn = document.getElementById("search-btn");
  const searchInput = document.getElementById("search-input");
  const btnAll = document.getElementById("btn-all");
  const btnBookmark = document.getElementById("btn-bookmark");

  // 처음 접속하면 전체 뉴스 목록 로딩
  loadNewsList("all");

  // 검색 버튼 클릭 시: 네이버 API 호출 + DB 저장 + 목록 갱신
  searchBtn.addEventListener("click", async () => {
    const query = searchInput.value.trim();
    if (!query) {
      alert("검색어를 입력해주세요.");
      return;
    }

    try {
      // 1) /api/news/search/ 호출해서 네이버 뉴스 → DB 저장
      await axios.get("/api/news/search/", {
        params: { q: query },
      });

      // 2) 저장 후 전체 목록 다시 불러오기
      await loadNewsList("all");
    } catch (error) {
      console.error(error);
      alert("뉴스 검색 중 오류가 발생했습니다.");
    }
  });

  // Enter 키로도 검색
  searchInput.addEventListener("keyup", (e) => {
    if (e.key === "Enter") {
      searchBtn.click();
    }
  });

  // 전체 보기 버튼
  btnAll.addEventListener("click", () => {
    btnAll.classList.add("active");
    btnBookmark.classList.remove("active");
    loadNewsList("all");
  });

  // 북마크 보기 버튼 (지금은 구조만, 기능은 나중에 완성)
  btnBookmark.addEventListener("click", () => {
    btnBookmark.classList.add("active");
    btnAll.classList.remove("active");
    loadNewsList("bookmark"); // 지금은 임시로 전체/북마크 구분 없이 동작시켜도 됨
  });
});

// 뉴스 목록 불러오기
async function loadNewsList(mode = "all") {
  const listEl = document.getElementById("news-list");
  const emptyMsgEl = document.getElementById("empty-message");

  try {
    // 아직 백엔드에서 북마크 필터 API는 없으니 일단 전부 가져오기
    const res = await axios.get("/api/news/");
    let newsList = res.data;

    // 추후 mode === 'bookmark' 일 때 is_bookmarked === true 인 것만 필터링
    if (mode === "bookmark") {
      newsList = newsList.filter((news) => news.is_bookmarked);
    }

    listEl.innerHTML = "";

    if (!newsList.length) {
      emptyMsgEl.classList.remove("hidden");
      return;
    }
    emptyMsgEl.classList.add("hidden");

    newsList.forEach((news) => {
      const li = document.createElement("li");
      li.className = "naver-news-item";
      li.dataset.id = news.id;

      const titleSpan = document.createElement("span");
      titleSpan.className = "naver-news-title";
      titleSpan.textContent = news.title;

      const starBtn = document.createElement("button");
      starBtn.className = "naver-bookmark-btn " + 
        (news.is_bookmarked ? "bookmarked" : "not-bookmarked");
      starBtn.innerText = "★";

      // 북마크 클릭 시: 나중에 API 연결 (지금은 모양만 토글해도 됨)
      starBtn.addEventListener("click", (event) => {
        event.stopPropagation(); // li 클릭(상세보기)와 분리
        // 나중에: /api/news/<id>/bookmark/ 같은 엔드포인트로 토글 예정
      });

      // li 클릭 시: 오른쪽에 상세 내용 표시 (간단 버전)
      li.addEventListener("click", () => {
        showNewsDetail(news);
      });

      li.appendChild(titleSpan);
      li.appendChild(starBtn);
      listEl.appendChild(li);
    });

  } catch (error) {
    console.error(error);
    alert("뉴스 목록을 불러오는 중 오류가 발생했습니다.");
  }
}

// 오른쪽 상세 영역에 내용 채우기
function showNewsDetail(news) {
  const detailEl = document.getElementById("news-detail");
  detailEl.innerHTML = ""; // 초기화

  const titleEl = document.createElement("div");
  titleEl.className = "naver-news-detail-title";
  titleEl.textContent = news.title;

  const metaEl = document.createElement("div");
  metaEl.className = "naver-news-detail-meta";
  metaEl.textContent = news.pub_date || "";

  const linkEl = document.createElement("a");
  linkEl.href = news.link;
  linkEl.target = "_blank";
  linkEl.rel = "noopener noreferrer";
  linkEl.textContent = "원문 보기";

  const bodyEl = document.createElement("div");
  bodyEl.className = "naver-news-detail-body";
  bodyEl.textContent = news.description || "";

  detailEl.appendChild(titleEl);
  detailEl.appendChild(metaEl);
  detailEl.appendChild(linkEl);
  detailEl.appendChild(document.createElement("hr"));
  detailEl.appendChild(bodyEl);
}


async function loadNewsDetail(id) {
  const detailEl = document.getElementById("news-detail");

  try {
    const res = await axios.get(`/api/news/${id}/`);
    const news = res.data;

    detailEl.innerHTML = "";

    const titleEl = document.createElement("div");
    titleEl.className = "naver-news-detail-title";
    titleEl.textContent = news.title;

    const metaEl = document.createElement("div");
    metaEl.className = "naver-news-detail-meta";
    metaEl.textContent = news.pub_date || "";

    const linkEl = document.createElement("a");
    linkEl.href = news.link;
    linkEl.target = "_blank";
    linkEl.rel = "noopener noreferrer";
    linkEl.textContent = "원문 보기";

    const bodyEl = document.createElement("div");
    bodyEl.className = "naver-news-detail-body";
    bodyEl.textContent = news.description || "";

    detailEl.appendChild(titleEl);
    detailEl.appendChild(metaEl);
    detailEl.appendChild(linkEl);
    detailEl.appendChild(document.createElement("hr"));
    detailEl.appendChild(bodyEl);
  } catch (error) {
    console.error(error);
    alert("뉴스 상세를 불러오는 중 오류가 발생했습니다.");
  }
}