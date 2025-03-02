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
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // File input enhancement
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const fileName = e.target.files[0]?.name;
            const label = this.nextElementSibling;
            if (label) {
                label.textContent = fileName || 'Choose file';
            }
        });
    }

    // Flash message auto-dismiss
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
});

// Form validation enhancement
function validateForm(form) {
    if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
    }
    form.classList.add('was-validated');
}

// Search input enhancement
const searchInput = document.querySelector('input[type="search"]');
if (searchInput) {
    searchInput.addEventListener('input', function(e) {
        if (this.value.length > 2) {
            this.form.classList.add('is-searching');
        } else {
            this.form.classList.remove('is-searching');
        }
    });
}

