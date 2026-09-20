
function initButton() {
  let count = 0;
  const btn = document.getElementById("btn-test");
  const textMsg = document.getElementById("text-test");
  const errMsg = document.getElementById("errMsg");
  const chkItem = document.getElementById("check-list");
  btn.addEventListener("click", function() {
    if (textMsg.value.trim() !== "") {
      const liItem = document.createElement("li");
      count++;
      errMsg.textContent = "";
      liItem.textContent = `${count} ${textMsg.value.trim()}`;
      chkItem.appendChild(liItem);
      textMsg.value = "";
    }
    else {
      errMsg.textContent = "請輸入內容";
    }
  });
}

document.addEventListener("DOMContentLoaded", function() {
  initButton();
});
