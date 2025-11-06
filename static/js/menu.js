const menuToggle = document.getElementById("menu-toggle");
const navMenu = document.getElementById("nav-menu");
const userActions = document.getElementById("user-actions");

menuToggle.addEventListener("click", () => {
    const expanded = menuToggle.getAttribute("aria-expanded") === "true";
    menuToggle.setAttribute("aria-expanded", !expanded);
    navMenu.classList.toggle("open");
    userActions.classList.toggle("open");
});