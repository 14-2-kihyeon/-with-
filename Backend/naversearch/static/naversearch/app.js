
let currentMode = "all";
let selectedNewsId = null;     // ★ 현재 선택된 뉴스 id
// naversearch/static/naversearch/app.js

document.addEventListener("DOMContentLoaded", () => {
  const searchBtn = document.getElementById("search-btn");
  const searchInput = document.getElementById("search-input");
  const btnAll = document.getElementById("btn-all");
  const btnBookmark = document.getElementById("btn-bookmark");
  const summaryBtn = document.getElementById("summary-btn");        
  const summaryContent = document.getElementById("summary-content");

  // 페이지 처음 접속: 전체보기 모드
  currentMode = "all";
  btnAll.classList.add("active");
  btnBookmark.classList.remove("active");
  loadNewsList(currentMode);

  // [검색하기] 버튼 (검색 후에는 항상 전체보기 모드로)
  searchBtn.addEventListener("click", async () => {
    const query = searchInput.value.trim();
    if (!query) {
      alert("검색어를 입력해주세요.");
      return;
    }

    try {
      await axios.get("/api/news/search/", { params: { q: query } });
      // 검색 후에는 전체 리스트로 다시
      currentMode = "all";
      btnAll.classList.add("active");
      btnBookmark.classList.remove("active");
      await loadNewsList(currentMode);
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

  // [전체 보기] 버튼 클릭
  btnAll.addEventListener("click", () => {
    if (currentMode === "all") return;   // 이미 전체보기면 패스

    currentMode = "all";
    btnAll.classList.add("active");
    btnBookmark.classList.remove("active");
    loadNewsList(currentMode);
  });

  // [북마크 보기] 버튼 클릭
  btnBookmark.addEventListener("click", () => {
    if (currentMode === "bookmark") return;

    currentMode = "bookmark";
    btnBookmark.classList.add("active");
    btnAll.classList.remove("active");
    loadNewsList(currentMode);
  });

  // F06: [요약 보기] 버튼 클릭 시 GMS(OpenAI)로 요약 요청
  summaryBtn.addEventListener("click", async () => {
    if (!selectedNewsId) {
      alert("먼저 기사를 선택해 주세요.");
      return;
    }

    const originalText = summaryBtn.textContent;
    summaryBtn.disabled = true;
    summaryBtn.textContent = "요약 중...";
    summaryContent.textContent = "";

    try {
      const res = await axios.post(`/api/news/${selectedNewsId}/summary/`);
      const data = res.data;
      summaryContent.textContent = data.summary || "요약 결과가 없습니다.";
    } catch (error) {
      console.error(error);
      summaryContent.textContent = "요약 생성 중 오류가 발생했습니다.";
    } finally {
      summaryBtn.disabled = false;
      summaryBtn.textContent = originalText;
    }
  });

});







// 뉴스 목록 불러오기 (mode: "all" | "bookmark")
async function loadNewsList(mode = "all") {
  const listEl = document.getElementById("news-list");
  const emptyMsgEl = document.getElementById("empty-message");

  try {
    // 1) DB에 저장된 전체 뉴스 가져오기
    const res = await axios.get("/api/news/");
    let newsList = res.data;

    // 2) 북마크 보기 모드라면 is_bookmarked == true 만 남기기
    if (mode === "bookmark") {
      newsList = newsList.filter((news) => news.is_bookmarked);
    }

    listEl.innerHTML = "";

    if (!newsList.length) {
      // 기사 없을 때 처리
      emptyMsgEl.classList.remove("hidden");
      document.getElementById("news-detail").textContent =
        "좌측에서 기사를 선택하면 상세 내용이 여기에 표시됩니다.";
      return;
    }
    emptyMsgEl.classList.add("hidden");

    let firstLi = null;
    let firstId = null;

    newsList.forEach((news, index) => {
      const li = document.createElement("li");
      li.className = "naver-news-item";
      li.dataset.id = news.id;

      const titleSpan = document.createElement("span");
      titleSpan.className = "naver-news-title";
      titleSpan.textContent = news.title;

      const starBtn = document.createElement("button");
      starBtn.className =
        "naver-bookmark-btn " +
        (news.is_bookmarked ? "bookmarked" : "not-bookmarked");
      starBtn.innerText = "★";

      // ★ 북마크 버튼 클릭 (F04)
      starBtn.addEventListener("click", async (event) => {
        event.stopPropagation(); // li 클릭(상세보기) 막기

        try {
          const res = await axios.post(`/api/news/${news.id}/bookmark/`);
          const updated = res.data;
          const isMarked = updated.is_bookmarked;

          // 버튼 색 갱신
          starBtn.classList.toggle("bookmarked", isMarked);
          starBtn.classList.toggle("not-bookmarked", !isMarked);

          // 현재 모드가 bookmark 인데 해제되면, 목록에서 제거해야 하므로 재로딩
          if (currentMode === "bookmark" && !isMarked) {
            await loadNewsList("bookmark");
          }
        } catch (error) {
          console.error(error);
          alert("북마크 변경 중 오류가 발생했습니다.");
        }
      });

      // 제목 클릭 시: 상세 API 호출 + active 스타일 (F03)
      li.addEventListener("click", () => {
        document
          .querySelectorAll(".naver-news-item.active")
          .forEach((el) => el.classList.remove("active"));

        li.classList.add("active");
        loadNewsDetail(news.id);
      });

      li.appendChild(titleSpan);
      li.appendChild(starBtn);
      listEl.appendChild(li);

      if (index === 0) {
        firstLi = li;
        firstId = news.id;
      }
    });

    // 3) 첫 번째 기사 자동 선택 + 상세 표시
    if (firstLi && firstId !== null) {
      firstLi.classList.add("active");
      loadNewsDetail(firstId);
    }
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


// 선택된 뉴스 상세 + 요약 버튼 상태 초기화
async function loadNewsDetail(id) {
  const detailEl = document.getElementById("news-detail");
  const summaryBtn = document.getElementById("summary-btn");
  const summaryContent = document.getElementById("summary-content");

  selectedNewsId = id;          // ★ 현재 선택된 기사 기억
  summaryBtn.disabled = false;  // 기사 선택되면 요약 버튼 활성화
  summaryContent.textContent = ""; // 이전 요약 내용은 지움

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
    detailEl.textContent = "뉴스 상세를 불러오는 중 오류가 발생했습니다.";
  }
}




// === CSRF 토큰을 axios에 자동으로 실어 보내기 ===
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // cookie가 "name=값" 형태인지 확인
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
axios.defaults.headers.common["X-CSRFToken"] = getCookie("csrftoken");