document.getElementById('searchBtn').addEventListener('click', function() {
    const query = document.getElementById('searchInput').value.trim();
    const defaultRes = document.getElementById('results-default');
    const foundRes = document.getElementById('results-found');
    const noneRes = document.getElementById('results-none');

    // 모든 상태 초기화
    [defaultRes, foundRes, noneRes].forEach(el => el.classList.remove('active'));

    if (query === "") {
        defaultRes.classList.add('active'); // 아무것도 안 적으면 기본 목록
    } else if (query === "개발자") {
        foundRes.classList.add('active'); // '개발자' 검색 시 결과 노출
    } else {
        noneRes.classList.add('active'); // 그 외에는 결과 없음
    }
});