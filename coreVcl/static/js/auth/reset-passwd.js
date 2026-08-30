function initResetPasswordSubmit() {
  const form = document.querySelector('.panel--reset-pw');
  if (!form) return;

  form.addEventListener('submit', function(event) {
    event.preventDefault();
    submitForm(form, '/auth/reset-password', function() {
      window.location.href = '/auth/login2';
    });
  });
}

document.addEventListener('DOMContentLoaded', function() {
  initResetPasswordSubmit();
});
