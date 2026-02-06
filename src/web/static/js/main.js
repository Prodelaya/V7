document.addEventListener("DOMContentLoaded", function () {
    const cookieBanner = document.getElementById("cookie-banner");
    const acceptBtn = document.getElementById("accept-cookies");
    const rejectBtn = document.getElementById("reject-cookies");

    // Check if user has already made a choice
    if (!localStorage.getItem("cookieConsent")) {
        // Show banner with a slight delay for better UX (animation)
        setTimeout(() => {
            cookieBanner.classList.add("show");
        }, 500);
    }

    acceptBtn.addEventListener("click", function () {
        localStorage.setItem("cookieConsent", "accepted");
        hideBanner();
        // Here you would trigger your analytics pixels
        console.log("Cookies accepted - Analytics enabled");
    });

    rejectBtn.addEventListener("click", function () {
        localStorage.setItem("cookieConsent", "rejected");
        hideBanner();
        console.log("Cookies rejected");
    });

    function hideBanner() {
        cookieBanner.classList.remove("show");
        // Remove from DOM after transition to avoid layout issues or phantom clicks
        setTimeout(() => {
            cookieBanner.style.display = "none";
        }, 300);
    }
});
