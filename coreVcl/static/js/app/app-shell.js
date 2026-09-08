let currentMode = null;


function switchContent(targetId) {
  const contentArea = document.querySelector('.content-area');
  contentArea.textContent = 'This is ' + targetId + ' content';
  // 之後這裡會換成真正切換不同區塊的邏輯
}

function renderSidebar(mode) {
  const sidebar = document.querySelector(".sidebar");
  sidebar.innerHTML = '';

  const config = navConfig[mode];
  config.sidebarItems.forEach(function(item) {
    const btn = document.createElement('button');
    btn.classList.add('sidebar-item');
    btn.dataset.target = item.id;
    btn.textContent = item.label;
    btn.addEventListener('click', function() {
      switchContent(item.id);
    });
    sidebar.appendChild(btn);
  });

  if (config.sidebarItems.length > 0) {
    switchContent(sidebarItems[0].id);
  }
}

function initTopNav() {
  const modeButtons = document.querySelector(".nav-mode-btn");
  modeButtons.forEach(function(btn) {
    btn.addEventListener('click', function() {
      currentMode = btn.dataset.mode;

    });
  });
}

document.addEventListener('DOMContentLoaded', function() {

});
