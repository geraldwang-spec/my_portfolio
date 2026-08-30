async function submitForm(form, endpoint, onSuccess) {
  const errorEl = form.querySelector('.error-message');
  const formData = new FormData(form);
  const data = Object.fromEntries(formData);

  try {

    const response = await fetch(endpoint, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    const result = await response.json();

    if (response.ok && result.success) {
      errorEl.textContent = '';
      onSuccess(result);
    } else {
      errorEl.textContent = result.message || '發生錯誤，請再試一次';
    }
  } catch (error) {
    console.log(error);
    errorEl.textContent = "無法連線到伺服器";
  }
}

function initPasswordMatch(passwordId, repeatId) {
  const password = document.getElementById(passwordId);
  const repeat = document.getElementById(repeatId);

  if (!password || !repeat) return;

  function checkMatch() {
    if (repeat.value !== password.value) {
      repeat.setCustomValidity("兩個密碼不一致");
    } else {
      repeat.setCustomValidity("");
    }
  }

  password.addEventListener('input', checkMatch);
  repeat.addEventListener('input', checkMatch);
}
