document.addEventListener('DOMContentLoaded', () => {
    // 랭킹 데이터 삽입
    const rankingData = [
        { rank: 1, nick: "햄부기",        count: 240, color: "#FAEFC9" },
        { rank: 2, nick: "가령밤빵",       count: 235, color: "#EAD6E4" },
        { rank: 3, nick: "민영부기",       count: 210, color: "#838DBA" },
        { rank: 4, nick: "박진웅",         count: 198, color: "#9EB19A" },
        { rank: 5, nick: "신나는 나나밍",  count: 184, color: "#B19A9A" }
    ];

    const rankingTable = document.getElementById('ranking-list');
    rankingData.forEach(item => {
        const row = document.createElement('div');
        row.className = 'rank-row';
        row.innerHTML = `
            <span>${item.rank}등</span>
            <span style="text-align: left; padding-left: 10px;">
                <i class="p-circle" style="background-color: ${item.color}"></i>
                ${item.nick}
            </span>
            <span style="color: #34436D; font-weight: 600;">${item.count}개</span>
        `;
        rankingTable.appendChild(row);
    });

    // 탭 버튼 클릭 이벤트
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });
});