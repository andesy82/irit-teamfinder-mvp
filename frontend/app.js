const API_URL = "";

const defaultUsers = [
    { id: 1, name: "Тимур (ИРИТ-РТФ)", role: "Backend", skills: "Python, FastAPI, SQLite, Docker, C#", tg_username: "timurCRL" },
    { id: 2, name: "Август (ИРИТ-РТФ)", role: "Frontend", skills: "JavaScript, HTML5, CSS3, Fetch API", tg_username: "augustpumpkin" },
    { id: 3, name: "Морковка (ИРИТ-РТФ)", role: "Bot Dev", skills: "Python, aiogram, Telegram API, JSON", tg_username: "ilovehersky" },
    { id: 4, name: "Даня (ИРИТ-РТФ)", role: "Algorithms", skills: "C#, .NET, Python, Data Structures", tg_username: "danyaknkv" },
    { id: 5, name: "Даша (ИРИТ-РТФ)", role: "Product/Design", skills: "User Flow, Excalidraw, QA, Pitching", tg_username: "skweetie" }
];

let users = [];

const usersGrid = document.getElementById("usersGrid");
const userForm = document.getElementById("userForm");
const roleFilter = document.getElementById("roleFilter");
const apiStatus = document.getElementById("apiStatus");

async function loadUsers() {
    try {
        const response = await fetch(`${API_URL}/users`);
        if (!response.ok) throw new Error("API offline");
        const data = await response.json();
        users = data.length > 0 ? data : defaultUsers;
        apiStatus.textContent = "● Подключено к FastAPI";
    } catch (error) {
        const saved = localStorage.getItem("irit_users");
        users = saved ? JSON.parse(saved) : defaultUsers;
        apiStatus.textContent = "● Автономный режим (LocalStorage)";
    }
    renderUsers();
}

function renderUsers() {
    const filterValue = roleFilter.value;
    const filtered = filterValue === "ALL" ? users : users.filter(u => u.role === filterValue);

    usersGrid.innerHTML = filtered.map(user => {
        const skillTags = user.skills.split(",").map(s => `<span class="skill-tag">${s.trim()}</span>`).join("");
        const cleanTg = user.tg_username.replace("@", "").trim();
        return `
            <div class="user-card">
                <div>
                    <span class="user-role">${user.role}</span>
                    <div class="user-name">${user.name}</div>
                    <div class="skills-wrap">${skillTags}</div>
                </div>
                <div>
                    <button class="btn btn-primary" onclick="openMatchModal('${user.name}', '${user.role}', '${cleanTg}')">
                        Подобрать (Match)
                    </button>
                    <a href="https://t.me{cleanTg}" target="_blank" class="btn btn-outline">
                        @${cleanTg}
                    </a>
                </div>
            </div>
        `;
    }).join("");
}

userForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const newUser = {
        id: Date.now(),
        name: document.getElementById("name").value,
        role: document.getElementById("role").value,
        skills: document.getElementById("skills").value,
        tg_username: document.getElementById("tg_username").value.replace("@", "").trim()
    };

    try {
        const response = await fetch(`${API_URL}/users`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(newUser)
        });
        if (!response.ok) throw new Error("Failed to post");
        await loadUsers();
    } catch (error) {
        users.unshift(newUser);
        localStorage.setItem("irit_users", JSON.stringify(users));
        renderUsers();
    }
    userForm.reset();
});

roleFilter.addEventListener("change", renderUsers);

const modal = document.getElementById("matchModal");
const closeModal = document.getElementById("closeModal");

function openMatchModal(name, role, tg) {
    const score = Math.floor(Math.random() * (96 - 78 + 1)) + 78;
    document.getElementById("matchScore").textContent = `${score}%`;
    document.getElementById("matchDetails").textContent = 
        `Участник ${name} (${role}) отлично дополняет стек вашей команды для хакатона.`;
    document.getElementById("modalTgLink").href = `https://t.me{tg}`;
    modal.classList.remove("hidden");
}

closeModal.addEventListener("click", () => modal.classList.add("hidden"));
window.addEventListener("click", (e) => {
    if (e.target === modal) modal.classList.add("hidden");
});

loadUsers();
