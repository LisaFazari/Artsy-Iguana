// Check if the "user" cookie exists
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

// Hides and shows navigation items depending on user logged in or not
document.addEventListener("DOMContentLoaded", () => {
    const userCookie = getCookie("username");
    const loginNav = document.getElementById("nav-login");
    const registerNav = document.getElementById("nav-register");
    const myProfileNav = document.getElementById("nav-myprofile");

    if (userCookie && loginNav) {
        loginNav.style.display = "none"; // Hides the nav element
        registerNav.style.display = "none";
    } 
    else 
    myProfileNav.style.display = "none";
});