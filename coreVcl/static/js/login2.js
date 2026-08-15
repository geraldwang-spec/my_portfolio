function initRipple() {
  const buttons = document.querySelectorAll('.btn');

  buttons.forEach(function(button) {
    button.addEventListener('click', function(event) {
      const rect = button.getBoundingClientRect();

      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;

      const size = Math.max(rect.width, rect.height)
      const ripple = document.createElement('span');
      ripple.classList.add('ripple')

      ripple.style.width = size + 'px';
      ripple.style.height = size + 'px';

      ripple.style.left = (x - size / 2) + 'px';
      ripple.style.top = (y - size / 2) + 'px';

      button.appendChild((ripple));

      ripple.addEventListener('animationend', function() {
        ripple.remove();
      });
    });
  });
}

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

function initLoginSubmit() {
  const form = document.querySelector('.panel--login');
  form.addEventListener('submit', function(event) {
    event.preventDefault();
    submitForm(form, '/auth/login2', function(result) {
      window.location.href = '/';
    });
  });
}

function initRegisterSubmit() {
  const form = document.querySelector('.panel--register');
  form.addEventListener('submit', function(event) {
    event.preventDefault()
    submitForm(form, '/auth/register', function(result) {
      window.location.href = '/auth/login2';
    });
  });
}

function initResetSubmit() {
  const form = document.querySelector('.panel--reset');
  form.addEventListener('submit', function(event) {
    event.preventDefault();
    submitForm(form, '/auth/resetpasswd', function(result) {
      if (result.success) {
        alert(result.message);
      }
      window.location.href = '/auth/login2';
    })
  });
}

// function initFormSubmit() {
//   const forms = document.querySelectorAll('.panel');
//
//   forms.forEach(function(form) {
//     form.addEventListener('submit', function(event) {
//       event.preventDefault();
//       console.log("表單被攔了，資料是：", new FormData(form));
//     });
//   });
// }

function initCardToggle() {
  const authCard = document.querySelector('.auth-card');
  const toggleBtn = document.querySelector('.toggle-btn');
  const reset = document.querySelector('.pass-forget');

  toggleBtn.addEventListener('click', function() {
    const current = authCard.dataset.view;
    authCard.dataset.view = current === "login" ? "register" : "login";
    // authCard.classList.toggle('is-register-active');
  });

  reset.addEventListener('click', function(event) {
    event.preventDefault();
    authCard.dataset.view = "reset";
  });
}


document.addEventListener('DOMContentLoaded', function() {
  initRipple();
  // initFormSubmit();
  initLoginSubmit();
  initRegisterSubmit();
  initCardToggle();
  initResetSubmit();
})
