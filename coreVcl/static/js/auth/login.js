function initLoginSubmit() {
  const form = document.querySelector('.panel--login');
  if (!form) return;

  form.addEventListener('submit', function(event) {
    event.preventDefault();
    submitForm(form, '/auth/login2', function(result) {
      window.location.href = '/';
    });
  });
}

function initRegisterSubmit() {
  const form = document.querySelector('.panel--register');
  if (!form) return;

  form.addEventListener('submit', function(event) {
    event.preventDefault()
    submitForm(form, '/auth/register', function(result) {
      window.location.href = '/auth/login2';
    });
  });
}

function initResetSubmit() {
  const form = document.querySelector('.panel--reset');
  if (!form) return;

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


function initCardToggle() {
  const authCard = document.querySelector('.auth-card');
  const toggleBtn = document.querySelector('.toggle-btn');
  const reset = document.querySelector('.pass-forget');

  if (!authCard) return;

  if (toggleBtn) {
    toggleBtn.addEventListener('click', function() {
      const current = authCard.dataset.view;
      authCard.dataset.view = current === "login" ? "register" : "login";
      // authCard.classList.toggle('is-register-active');
    });
  }

  if (reset) {
    reset.addEventListener('click', function(event) {
      event.preventDefault();
      authCard.dataset.view = "reset";
    });
  }
}

document.addEventListener('DOMContentLoaded', function() {
  initLoginSubmit();
  initRegisterSubmit();
  initCardToggle();
  initResetSubmit();
  initPasswordMatch('register-password', 'register-repeat');
});
