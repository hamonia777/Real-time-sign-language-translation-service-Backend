/* ──────────────────────────────────────────────────────────
   수어 연구소 - search.js
   기능: 로그인 체크, 실시간 자동완성, 최근/인기 검색어 API 연동, X버튼 삭제
   ────────────────────────────────────────────────────────── */

// 쿠키에서 토큰 꺼내는 함수
function getCookie(name) {
    const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
    return match ? decodeURIComponent(match[1]) : null;
}

const token = getCookie('access_token');
const authHeader = { 'Authorization': `Bearer ${token}` };

document.addEventListener('DOMContentLoaded', () => {

    /* ──────────────────────────────────────────────────────
       로그인 체크 & 헤더 버튼 처리
    ────────────────────────────────────────────────────────*/
    if (!token) {
        alert('로그인이 필요합니다.');
        location.href = 'login.html';
        return;
    }

    const authBtn = document.getElementById('headerAuthBtn');
    if (authBtn) {
        authBtn.innerText = '로그아웃';
        authBtn.classList.add('logout-style');
        authBtn.onclick = async () => {
            if (confirm('로그아웃 하시겠습니까?')) {
                document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                document.cookie = "refresh_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
                await fetch('/api/v1/auth/logout', { method: 'GET', credentials: 'include' });
                alert('로그아웃 되었습니다.');
                location.href = 'home.html';
            }
        };
    }

    const searchInput = document.getElementById('searchInput');
    const searchBtn   = document.getElementById('searchBtn');
    const resultsList = document.getElementById('results-list');
    const resultsNone = document.getElementById('results-none');

    /* ──────────────────────────────────────────────────────
       자동완성 드롭다운 생성
    ────────────────────────────────────────────────────────*/
    const autocompleteBox = document.createElement('ul');
    autocompleteBox.id = 'autocomplete-list';
    autocompleteBox.style.cssText = `
        position: absolute; top: 100%; left: 0; right: 95px;
        background: #fff; border: 1px solid #D6D6D6; border-radius: 8px;
        list-style: none; margin: 4px 0 0; padding: 6px 0;
        z-index: 999; display: none; box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        max-height: 220px; overflow-y: auto;
    `;
    searchInput.parentElement.style.position = 'relative';
    searchInput.parentElement.appendChild(autocompleteBox);

    let autocompleteTimer = null;

    /* ──────────────────────────────────────────────────────
       실시간 자동완성
    ────────────────────────────────────────────────────────*/
    searchInput.addEventListener('input', () => {
        const q = searchInput.value.trim();
        clearTimeout(autocompleteTimer);

        if (!q) {
            autocompleteBox.style.display = 'none';
            return;
        }

        autocompleteTimer = setTimeout(async () => {
            try {
                const res = await fetch(`/api/v1/search/suggest?word=${encodeURIComponent(q)}`, {
                    headers: authHeader
                });
                const data = await res.json();
                renderAutocomplete(data.results || []);
            } catch {
                autocompleteBox.style.display = 'none';
            }
        }, 250);
    });

    function renderAutocomplete(results) {
        autocompleteBox.innerHTML = '';
        if (!results.length) {
            autocompleteBox.style.display = 'none';
            return;
        }
        results.forEach(item => {
            const li = document.createElement('li');
            li.textContent = item.word;
            li.style.cssText = `
                padding: 10px 16px; font-size: 13px; cursor: pointer;
                color: #34436D; transition: background 0.15s;
            `;
            li.addEventListener('mouseenter', () => li.style.background = '#F4F8FD');
            li.addEventListener('mouseleave', () => li.style.background = '');
            li.addEventListener('click', () => {
                searchInput.value = item.word;
                autocompleteBox.style.display = 'none';
                doSearch(item.word);
            });
            autocompleteBox.appendChild(li);
        });
        autocompleteBox.style.display = 'block';
    }

    // 외부 클릭 시 자동완성 닫기
    document.addEventListener('click', (e) => {
        if (!searchInput.parentElement.contains(e.target)) {
            autocompleteBox.style.display = 'none';
        }
    });

    // Enter 키 검색
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            autocompleteBox.style.display = 'none';
            const q = searchInput.value.trim();
            if (!q) {
                loadAllWords();
            } else {
                doSearch(q);
            }
        }
    });

    // 검색 버튼 클릭
    searchBtn.addEventListener('click', () => {
        autocompleteBox.style.display = 'none';
        const q = searchInput.value.trim();
        if (!q) {
            loadAllWords(); // 빈 검색이면 전체 목록
        } else {
            doSearch(q);
        }
    });

    /* ──────────────────────────────────────────────────────
       검색 실행
    ────────────────────────────────────────────────────────*/
    async function doSearch(query) {
        if (!query) return;

        try {
            const res = await fetch(`/api/v1/search?word=${encodeURIComponent(query)}`, {
                headers: authHeader
            });
            const data = await res.json();
            renderResults(data.results || []);
            loadRecentSearches(); // 검색 후 최근 검색어 갱신
        } catch {
            showNone();
        }
    }

    function renderResults(results) {
        resultsList.innerHTML = '';
        if (!results.length) {
            showNone();
            return;
        }

        resultsList.classList.add('active');
        resultsNone.classList.remove('active');

        const ul = document.createElement('ul');
        ul.className = 'search-result-list';

        results.forEach(item => {
            const li = document.createElement('li');
            li.innerHTML = `
                <span class="sign-word" style="cursor:pointer;" onclick="window.open('https://sldict.korean.go.kr/front/search/searchAllList.do?searchKeyword=${encodeURIComponent(item.word)}', '_blank')">${item.word}</span>
                <div class="btn-group">
                    <button class="btn-basket">학습바구니 넣기</button>
                    <button class="btn-learn">지금 학습하기</button>
                </div>
            `;
            ul.appendChild(li);
        });
        resultsList.appendChild(ul);
    }

    function showNone() {
        resultsList.classList.remove('active');
        resultsNone.classList.add('active');
    }


    /* ──────────────────────────────────────────────────────
       최근 검색어
    ────────────────────────────────────────────────────────*/
    async function loadRecentSearches() {
        try {
            const res = await fetch('/api/v1/search/recent', { headers: authHeader });
            const data = await res.json();
            renderRecentTags(data.recentSearches || []);
        } catch {
            const local = JSON.parse(localStorage.getItem('recentSearches') || '[]');
            renderRecentTags(local.map((w, i) => ({ id: i, word: w })));
        }
    }

    function renderRecentTags(searches) {
        const tagList = document.querySelector('.tag-list');
        if (!tagList) return;
        tagList.innerHTML = '';

        searches.forEach(item => {
            const span = document.createElement('span');
            span.className = 'search-tag';
            span.innerHTML = `${item.word} <i class="close-icon" data-id="${item.id}">×</i>`;

            // 태그 클릭 → 검색
            span.addEventListener('click', (e) => {
                if (e.target.classList.contains('close-icon')) return;
                searchInput.value = item.word;
                doSearch(item.word);
            });

            // X 버튼 → 삭제
            span.querySelector('.close-icon').addEventListener('click', async () => {
                try {
                    await fetch(`/api/v1/search/recent/${item.id}`, {
                        method: 'DELETE',
                        headers: authHeader
                    });
                } catch {}
                span.remove();
            });

            tagList.appendChild(span);
        });
    }

    async function loadAllWords() {
        try {
            const res = await fetch('/api/v1/search/all', { headers: authHeader });
            const data = await res.json();
            renderResults(data.results || []);
        } catch {}
    }
    /* ──────────────────────────────────────────────────────
       인기 검색어
    ────────────────────────────────────────────────────────*/
    async function loadPopularSearches() {
        try {
            const res = await fetch('/api/v1/search/popular', { headers: authHeader });
            const data = await res.json();
            renderPopular(data.popularSearches || []);
        } catch {}
    }

    function renderPopular(searches) {
        const rankList = document.querySelector('.rank-list');
        if (!rankList) return;
        rankList.innerHTML = '';

        searches.forEach(item => {
            const li = document.createElement('li');
            li.innerHTML = `<span class="rank-num">${item.rank}</span> ${item.word}`;
            li.style.cursor = 'pointer';
            li.addEventListener('click', () => {
                searchInput.value = item.word;
                doSearch(item.word);
            });
            rankList.appendChild(li);
        });
    }


    /* ──────────────────────────────────────────────────────
       초기 로드
    ────────────────────────────────────────────────────────*/
    loadRecentSearches();
    loadPopularSearches();
    loadAllWords();
});