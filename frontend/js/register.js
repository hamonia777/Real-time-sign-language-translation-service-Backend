// 가령: 26/04/19 수정내용: 가입하기 폼 submit 시 /api/v1/users/info 호출하여 초기 정보 저장
function getCookie(name) {
  const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
  return match ? decodeURIComponent(match[1]) : null;
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('registerForm');
  if (!form) return;

  const inputs = form.querySelectorAll('input[type="text"], input[type="tel"], input[type="email"]');
  const nameInput = inputs[0];
  const phoneInput = inputs[1];
  const emailInput = inputs[2];

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const term1 = document.getElementById('term1')?.checked;
    const term2 = document.getElementById('term2')?.checked;
    if (!term1 || !term2) {
      alert('필수 약관에 동의해주세요.');
      return;
    }

    const name = nameInput.value.trim();
    const phone = phoneInput.value.trim();
    const email = emailInput.value.trim();

    if (!name || !phone || !email) {
      alert('이름, 연락처, 이메일을 모두 입력해주세요.');
      return;
    }

    const token = getCookie('access_token');
    if (!token) {
      alert('로그인이 필요합니다.');
      location.href = 'login.html';
      return;
    }

    try {
      const res = await fetch('/api/v1/users/info', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ name: name, phone_num: phone, email: email }),
      });

      if (res.status === 401) {
        alert('로그인 세션이 만료되었습니다.');
        location.href = 'login.html';
        return;
      }
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        alert('가입 실패: ' + (data.detail || res.status));
        return;
      }

      alert('가입이 완료되었습니다.');
      location.href = 'home.html';
    } catch (err) {
      alert('네트워크 오류: ' + err.message);
    }
  });

  const allCheck = document.getElementById('checkAll');
  if (allCheck) {
    allCheck.addEventListener('change', () => {
      document.querySelectorAll('.check-list input[type="checkbox"]').forEach((cb) => {
        cb.checked = allCheck.checked;
      });
    });
  }
});
