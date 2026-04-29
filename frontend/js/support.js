function getCookie(name) {
    const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
    return match ? decodeURIComponent(match[1]) : null;
}

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('supportForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const token = getCookie('access_token');
        if (!token) {
            alert('로그인 후 문의하기가 가능합니다.');
            location.href = 'login.html';
            return;
        }

        const title = form.querySelector('input[type="text"]').value.trim();
        const content = form.querySelector('textarea').value.trim();

        if (!title || !content) {
            alert('제목과 내용을 모두 입력해 주세요.');
            return;
        }

        const submitBtn = form.querySelector('.submit-inquiry-btn');
        submitBtn.disabled = true;
        submitBtn.textContent = '전송 중...';

        try {
            const res = await fetch('/api/v1/inquiry', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({
                    title,
                    content,
                    marketing_agree: document.getElementById('marketing-agree')?.checked ?? false,
                }),
            });

            if (res.ok) {
                alert('문의가 접수되었습니다. 빠르게 답변 드리겠습니다!');
                form.reset();
            } else if (res.status === 401) {
                alert('로그인이 만료되었습니다. 다시 로그인해 주세요.');
                location.href = 'login.html';
            } else {
                const data = await res.json().catch(() => ({}));
                alert(data.detail || '문의 접수 중 오류가 발생했습니다.');
            }
        } catch (err) {
            console.error('문의 전송 오류:', err);
            alert('서버와 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = '문의하기';
        }
    });
});
