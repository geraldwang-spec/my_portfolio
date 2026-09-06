function initResetPasswordSubmit() {
  const form = document.querySelector('.panel--reset-pw');
  if (!form) return;

  form.addEventListener('submit', function(event) {
    event.preventDefault();
    submitForm(form, '/auth/renew_password', function(result) {
      if (!result.success) {

        console.log("test");
        alert(result.message);
        console.log("test");
      }
      window.location.href = '/auth/login';
    });
  });
}

document.addEventListener('DOMContentLoaded', function() {
  initResetPasswordSubmit();
  initPasswordMatch('reset-pw-password', 'reset-pw-repeat');
});
