document.addEventListener("DOMContentLoaded", () => {
  let isAdmin = localStorage.getItem("isAdmin") === "true";
  let authToken = localStorage.getItem("token") || "";
  fetchAndRenderPosts(); // load posts for both admin and guest

  // Redirect if neither admin nor guest
  if (localStorage.getItem("isAdmin") === null) {
    window.location.href = "login.html";
  }

  const loginSection = document.getElementById("loginSection");
  const uploadForm = document.getElementById("uploadForm");
  const categoriesContainer = document.getElementById("categoriesContainer");
  const loginError = document.getElementById("loginError");
  const categoryFilter = document.getElementById("categoryFilter");
  const imageModal = document.getElementById("imageModal");
  const modalImg = document.getElementById("modalImg");
  const modalClose = document.getElementById("modalClose");

  if (uploadForm) {
    uploadForm.style.display = isAdmin ? "grid" : "none";
  }


  // Login Handler
  const btnLogin = document.getElementById("btnLogin");
  if (btnLogin) {
    btnLogin.addEventListener("click", async () => {
      const username = document.getElementById("username").value.trim();
      const password = document.getElementById("password").value.trim();

      loginError.textContent = "";
      if (!username || !password) {
        loginError.textContent = "Please enter username and password.";
        return;
      }

      try {
        const res = await fetch("/api/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        });

        const data = await res.json();

        if (res.ok) {
          localStorage.setItem("isAdmin", "true");
          localStorage.setItem("token", data.token);
          window.location.href = "/home";
        } else {
          loginError.textContent = data.message || "Login failed";
        }
      } catch (err) {
        loginError.textContent = "Error connecting to server.";
      }
    });
  }

  // Guest Login Handler
  const btnGuest = document.getElementById("btnGuest");
  if (btnGuest) {
    btnGuest.addEventListener("click", () => {
      localStorage.setItem("isAdmin", "false");
      localStorage.setItem("token", "");
      window.location.href = "/home";
    });
  }

  // Upload Art Handler
  if (uploadForm) {
    uploadForm.addEventListener("submit", async (e) => {
      e.preventDefault();

      const title = document.getElementById("title").value.trim();
      const description = document.getElementById("description").value.trim();
      const category = document.getElementById("category").value.trim();
      const imageFile = document.getElementById("imageFile").files[0];

      if (!title || !description || !category || !imageFile) return;

      const formData = new FormData();
      formData.append("title", title);
      formData.append("description", description);
      formData.append("category", category);
      formData.append("imageFile", imageFile);

      try {
        const res = await fetch("/api/posts", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${authToken}`,
          },
          body: formData,
        });

        if (res.ok) {
          const reader = new FileReader();
          reader.onloadend = () => {
            const base64Image = reader.result;

            emailjs.send('service_p1ea29n', 'template_at32wmi', {
              title,
              category,
              description,
              image_attachment: base64Image
            }).then(() => {
              console.log('Email sent!');
            }).catch(err => {
              console.error('EmailJS failed:', err);
            });
          };
          reader.readAsDataURL(imageFile);

          uploadForm.reset();
          fetchAndRenderPosts();
        } else {
          alert("Failed to post art.");
        }
      } catch {
        alert("Server error.");
      }
    });
  }

  // Fetch and render art
  async function fetchAndRenderPosts() {
    try {
      const res = await fetch("/api/posts");
      const data = await res.json();

      if (!res.ok) throw new Error(data.message || "Failed to fetch posts");

      allPosts = data.posts;
      renderCategoryFilter();
      renderPosts();
    } catch {
      categoriesContainer.innerHTML = "<p>Failed to load posts.</p>";
    }
  }

  // Helpers
  let allPosts = [];
  let currentFilter = null;

  function renderCategoryFilter() {
    const categories = [...new Set(allPosts.map(p => p.category))].sort();

    categoryFilter.innerHTML = `<button ${currentFilter === null ? 'class="active"' : ''} data-cat="">All</button>`;
    categories.forEach(cat => {
      categoryFilter.innerHTML += `<button ${currentFilter === cat ? 'class="active"' : ''} data-cat="${cat}">${escapeHTML(cat)}</button>`;
    });

    categoryFilter.querySelectorAll("button").forEach(btn => {
      btn.onclick = () => {
        currentFilter = btn.getAttribute("data-cat") || null;
        renderCategoryFilter();
        renderPosts();
      };
    });
  }

  function renderPosts() {
    categoriesContainer.innerHTML = "";

    const filteredPosts = currentFilter ? allPosts.filter(p => p.category === currentFilter) : allPosts;
    const categories = {};
    filteredPosts.forEach(post => {
      if (!categories[post.category]) categories[post.category] = [];
      categories[post.category].push(post);
    });

    Object.keys(categories).forEach(cat => {
      const section = document.createElement("div");
      section.className = "category";
      section.innerHTML = `<h2>${escapeHTML(cat)}</h2>`;

      categories[cat].forEach(post => {
        const card = document.createElement("div");
        card.className = "art-card";
        card.dataset.id = post.id;

        card.innerHTML = `
          <img src="${post.image_url}" alt="${escapeHTML(post.title)}" class="art-image" />
          <h3>${escapeHTML(post.title)}</h3>
          <p>${escapeHTML(post.description)}</p>
          <button class="like-btn">❤️ ${post.likes}</button>
          <div class="comment-box">
            <input type="text" class="comment-input" placeholder="Add comment" />
            <button class="comment-btn">💬</button>
          </div>
          <ul class="comments-list">
            ${post.comments.map(c => `
              <li>
                ${escapeHTML(c.text || c)}
                ${isAdmin ? `<button class="delete-comment-btn" data-comment-id="${c.id || ''}" title="Delete comment">🗑️</button>` : ""}
              </li>`).join('')}
          </ul>
          ${isAdmin ? `<button class="delete-btn">🗑️ Delete Post</button>` : ""}
        `;
        section.appendChild(card);
      });

      categoriesContainer.appendChild(section);
    });

    attachEventListeners();
  }

  function escapeHTML(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function attachEventListeners() {
    document.querySelectorAll(".like-btn").forEach(btn => {
      btn.onclick = () => likePost(btn.closest(".art-card").dataset.id);
    });

    document.querySelectorAll(".comment-btn").forEach(btn => {
      btn.onclick = () => addComment(btn.closest(".art-card"));
    });

    document.querySelectorAll(".delete-btn").forEach(btn => {
      btn.onclick = () => deletePost(btn.closest(".art-card").dataset.id);
    });

    document.querySelectorAll(".delete-comment-btn").forEach(btn => {
      btn.onclick = async (e) => {
        e.stopPropagation();
        const postId = btn.closest(".art-card").dataset.id;
        const commentId = btn.dataset.commentId;
        if (!commentId) return alert("Cannot delete this comment.");
        if (!confirm("Delete this comment?")) return;

        try {
          const res = await fetch(`/api/posts/${postId}/comment/${commentId}`, {
            method: "DELETE",
            headers: { Authorization: `Bearer ${authToken}` },
          });
          if (res.ok) fetchAndRenderPosts();
          else alert("Failed to delete comment.");
        } catch {
          alert("Server error.");
        }
      };
    });

    document.querySelectorAll(".art-image").forEach(img => {
      img.onclick = () => {
        modalImg.src = img.src;
        imageModal.style.display = "flex";
      };
    });
  }

  modalClose.onclick = () => {
    imageModal.style.display = "none";
  };

  imageModal.onclick = (e) => {
    if (e.target === imageModal) imageModal.style.display = "none";
  };

  async function likePost(postId) {
    try {
      const res = await fetch(`/api/posts/${postId}/like`, {
        method: "POST",
        headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
      });
      if (res.ok) fetchAndRenderPosts();
    } catch { }
  }

  async function addComment(card) {
    const postId = card.dataset.id;
    const input = card.querySelector(".comment-input");
    const comment = input.value.trim();
    if (!comment) return;

    try {
      const res = await fetch(`/api/posts/${postId}/comment`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        },
        body: JSON.stringify({ comment }),
      });
      if (res.ok) {
        input.value = "";
        fetchAndRenderPosts();
      }
    } catch { }
  }

  async function deletePost(postId) {
    if (!confirm("Are you sure you want to delete this post?")) return;

    try {
      const res = await fetch(`/api/posts/${postId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.ok) fetchAndRenderPosts();
    } catch { }
  }
});
