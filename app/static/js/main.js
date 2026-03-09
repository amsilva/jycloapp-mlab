const modal = document.getElementById("modalCheckpoint");
const btn = document.getElementById("abrirModal");

btn.addEventListener("click", () => {
    modal.style.display = "block";
});

window.addEventListener("click", (e) => {
    if (e.target === modal) {
        modal.style.display = "none";
    }
});
