document.addEventListener("DOMContentLoaded", function() {
  const date = new Date();
  const yearElement = document.querySelector(".year");
  if (yearElement) {
      yearElement.innerHTML = date.getFullYear();
  } else {
      console.error('Element with class "year" not found.');
  }

  setTimeout(function () {
      $("#message").fadeOut("slow");
  }, 3000);

  var baseJSLoaded = true;
  console.log('base.js is loaded');
});