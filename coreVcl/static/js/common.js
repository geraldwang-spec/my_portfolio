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

document.addEventListener('DOMContentLoaded', function() {
  initRipple();
})
