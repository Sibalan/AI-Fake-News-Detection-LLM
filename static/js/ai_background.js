// ==========================
// AI Floating Particles
// ==========================

document.addEventListener("DOMContentLoaded", () => {

    const bg = document.querySelector(".ai-background");

    if (!bg) return;

    // Create particles
    for (let i = 0; i < 60; i++) {

        const dot = document.createElement("div");

        dot.className = "particle";

        dot.style.left = Math.random() * 100 + "%";
        dot.style.top = Math.random() * 100 + "%";

        dot.style.animationDuration =
            (8 + Math.random() * 10) + "s";

        dot.style.animationDelay =
            (Math.random() * 5) + "s";

        bg.appendChild(dot);
    }

});