function login() {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    fetch("https://notehive-01sh.onrender.com", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.token) {
            localStorage.setItem("token", data.token);
            window.location.href = "dashboard.html";
        } else {
            alert("Login failed");
        }
    });
}
